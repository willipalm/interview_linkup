#!/usr/bin/env python3
"""Retrieval-only run: every search API, no Anthropic API calls. Answering and grading are done
afterwards by a Claude Code session from a blinded handoff folder, then ingested into the normal scorecard.

    # optional, before the run: blind query rewrites for the linkup-rewritten arm (a Claude Code session writes them)
    .venv/bin/python scripts/retrieval_run.py rewrite-prompts --gold bench2
    .venv/bin/python scripts/retrieval_run.py run --gold bench2 --tuned configs/linkup_tuned.json
    #   -> runs/<id>-retrieval/: retrieval.jsonl, retrieval_scorecard.md, handoff/ (tasks for Claude Code)
    # Claude Code session: follow runs/<id>-retrieval/handoff/INSTRUCTIONS.md, step 1 -> handoff/answers.jsonl
    .venv/bin/python scripts/retrieval_run.py grade-prompts runs/<id>-retrieval
    # Claude Code session: step 2 -> handoff/grades.jsonl
    .venv/bin/python scripts/retrieval_run.py ingest runs/<id>-retrieval --model "<model the session ran on>"
    #   -> agent.jsonl, judgments.jsonl, scorecard.md, research_scorecard.md, human_review.csv

How this differs from run_eval.py: there is no agent loop. Each (question, search arm) gets exactly one search, with
the user's query as typed (plus the as-of sentence on point-in-time rows, identical for every arm) and the same
harness filters run_eval.py applies (per-team domains and depth, the point-in-time upper bound). So this measures
the search API on the raw query, not an agent's query rewriting. Two exceptions, both Linkup-only and labelled:
linkup-rewritten sends a query rewritten per Linkup's docs (see rewrite-prompts), and the research arms
(configs/research_arms.json) send the question to each vendor's deep-research endpoint and use the vendor's own answer.
Research arms run only on research rows (finance and multi-hop questions), the same rows for every vendor, and are
reported separately in research_scorecard.md. linkup-native is left out: it needs an LLM to choose search parameters.
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import datetime as dt
import json
import pathlib
import random
import re
import statistics
import sys
import threading
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import run_eval as R  # noqa: E402  (importing makes no API calls)
import simpleqa_grader as sqa  # noqa: E402
from research_backends import RESEARCH_BACKENDS, ResearchError  # noqa: E402
from search_backends import BACKENDS, SearchError  # noqa: E402

SEARCH_ARMS = ["linkup-standard", "linkup-deep", "linkup-tuned", "linkup-fast", "linkup-rewritten", "perplexity", "parallel"]
RESEARCH_CONFIG = ROOT / "configs" / "research_arms.json"
RESEARCH_ARMS = [a for a in json.loads(RESEARCH_CONFIG.read_text()) if not a.startswith("_")] if RESEARCH_CONFIG.exists() else []
DEFAULT_ARMS = SEARCH_ARMS + RESEARCH_ARMS
REWRITES_DIR = ROOT / "gold" / "rewrites"


def is_research(row) -> bool:
    """Research rows: finance and multi-hop questions, never point-in-time rows (the research endpoints have no
    reliable upper date bound). bench2 rows carry an explicit flag; for bench1, multi-hop = hops >= 2 and finance =
    an investment-team question whose answer is a number."""
    if row.get("point_in_time"):
        return False
    if "research" in row:
        return bool(row["research"])
    return row["hops"] >= 2 or (row["team"] == "invest" and row["answer_type"] == "number")


def is_research_arm(cfg) -> bool:
    return bool(cfg.get("research"))


def load_rewrites(gold):
    path = REWRITES_DIR / f"{gold}.jsonl"
    if not path.exists():
        return None
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            o = json.loads(line)
            out[o["id"]] = o["q"]
    return out


# ─────────────────────────────── run ───────────────────────────────
def _base_record(row, arm):
    return {"id": row["id"], "arm": arm, "split": row["split"], "team": row["team"], "pattern": row["pattern"],
            "trap": row["trap"], "origin": row.get("origin"), "today": row["_today"],
            "point_in_time": row.get("point_in_time")}


def search_one(row, arm, cfg, mode, date_filter=True, rewrites=None):
    backend = BACKENDS[cfg["backend"]](**{k: v for k, v in cfg.items() if k == "depth"})
    depth = (cfg.get("teams") or {}).get(row["team"], {}).get("depth") or cfg.get("depth")
    if depth:
        backend.opts["depth"] = depth
    params = R.search_params(row, cfg, use_date_filter=date_filter)
    error = None
    if cfg.get("rewrite"):
        # Linkup's guidance: no dates in the query text; the point-in-time bound stays in toDate (params).
        sent = (rewrites or {}).get(row["id"])
        if not sent:
            error = f"no rewrite for {row['id']} in gold/rewrites/"
    else:
        sent = R.pit_query(row["query"], row, backend, mode)
    call = {"query": row["query"], "params": params, "depth": backend.opts.get("depth"),
            **({"sent_query": sent} if sent and sent != row["query"] else {})}
    if not error:
        try:
            out = backend.search(sent, k=R.TOP_K, **params)
            call.update(latency_ms=out["latency_ms"], n_results=len(out["results"]), request=out["request"],
                        raw=out["raw"], results=out["results"], unsupported=out["unsupported"], fee_usd=out["fee_usd"])
        except SearchError as e:
            error = str(e)
    if error:
        call["error"] = error
    return {**_base_record(row, arm), "date_filter": date_filter, "error": error,
            "search_calls": [call], "n_search_calls": 1, "backend_opts": {"depth": backend.opts.get("depth")}}


def research_one(row, arm, cfg):
    backend = RESEARCH_BACKENDS[cfg["backend"]](**{k: v for k, v in cfg.items() if k not in ("backend", "research")})
    rec = {**_base_record(row, arm), "date_filter": False, "error": None, "search_calls": [], "n_search_calls": 0,
           "backend_opts": {k: v for k, v in cfg.items() if k not in ("backend", "research")}}
    try:
        rec["research_call"] = backend.run(row["query"])
    except ResearchError as e:
        rec["error"] = str(e)
    except Exception as e:  # an unexpected vendor response must not abort the whole run
        rec["error"] = f"{cfg['backend']}-research: unexpected {type(e).__name__}: {e}"
    return rec


def _arms_config(args_tuned):
    arms = dict(R.ARMS)
    if args_tuned:
        arms["linkup-tuned"] = {"backend": "linkup", **json.loads(pathlib.Path(args_tuned).read_text())}
    if RESEARCH_CONFIG.exists():
        arms.update({a: c for a, c in json.loads(RESEARCH_CONFIG.read_text()).items() if not a.startswith("_")})
    return arms


def _available(cfg):
    cls = RESEARCH_BACKENDS[cfg["backend"]] if is_research_arm(cfg) else BACKENDS[cfg["backend"]]
    return cls().available, cls.key_env


def cmd_run(args):
    R.load_env(ROOT / ".env")
    arms = _arms_config(args.tuned)
    wanted = args.arms or [a for a in DEFAULT_ARMS if a in arms]
    unknown = [a for a in wanted if a not in arms]
    if unknown:
        sys.exit(f"unknown arms: {unknown} (linkup-tuned needs --tuned; research arms live in {RESEARCH_CONFIG.name})")
    if args.no_research:
        wanted = [a for a in wanted if not is_research_arm(arms[a])]

    if args.resume:
        run_dir = pathlib.Path(args.resume)
        meta = json.loads((run_dir / "meta.json").read_text())
        args.pit_query, gold = meta["pit_query"], meta.get("gold", "bench1")
    else:
        gold = args.gold
    rewrites = load_rewrites(gold)
    usable = {}
    for a in wanted:
        cfg = arms[a]
        if cfg.get("native"):
            print(f"SKIP  {a}: native arms need an LLM to choose search parameters")
            continue
        ok, key_env = _available(cfg)
        if not ok:
            print(f"SKIP  {a}: no {key_env} in .env")
            continue
        if cfg.get("rewrite") and rewrites is None:
            print(f"SKIP  {a}: no gold/rewrites/{gold}.jsonl yet (run rewrite-prompts, then have a Claude Code session write it)")
            continue
        usable[a] = cfg
    rows, expired = R.load_rows(args.split, args.ids, args.run_date, args.include_expired, gold=gold)
    if expired:
        print(f"WARN  skipped {len(expired)} expired rows (re-verify, or pass --include-expired): {', '.join(expired)}")

    if args.resume:
        usable = {**{a: c for a, c in meta["arms"].items()}, **{a: c for a, c in usable.items() if a not in meta["arms"]}}
        meta["arms"] = usable
        meta.setdefault("gold", gold)
    else:
        run_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{gold}-{args.split}-retrieval"
        run_dir = ROOT / "runs" / run_id
        meta = {"run_id": run_id, "mode": "retrieval-only", "gold": gold, "split": args.split, "ids": args.ids,
                "run_date": args.run_date, "date_filter": True, "pit_query": args.pit_query,
                "include_expired": args.include_expired, "agent_model": "none yet (Claude Code session)", "agent_effort": "n/a",
                "judge_model": "none yet (Claude Code session)", "arms": usable, "max_search_calls": 1, "top_k": R.TOP_K}
    s_arms = [a for a in usable if not is_research_arm(usable[a])]
    r_arms = [a for a in usable if is_research_arm(usable[a])]
    r_rows = [r for r in rows if is_research(r)]
    jobs = [(r, a) for r in rows for a in s_arms] + [(r, a) for r in r_rows for a in r_arms]
    print(f"Plan ({gold}, split={args.split}): {len(rows)} rows x {len(s_arms)} search arms = {len(rows) * len(s_arms)} searches"
          + (f"; {len(r_rows)} research rows x {len(r_arms)} research arms = {len(r_rows) * len(r_arms)} research jobs" if r_arms else "")
          + f". No LLM calls. As-of in query: {args.pit_query}. Arms: {', '.join(usable)}")
    if r_arms:
        est = []
        for a in r_arms:
            c = usable[a]
            if c["backend"] == "linkup":
                from research_backends import LINKUP_RESEARCH_FEE
                p = LINKUP_RESEARCH_FEE.get(c.get("reasoningDepth", "XL"))
            elif c["backend"] == "parallel":
                from research_backends import PARALLEL_TASK_FEE
                p = PARALLEL_TASK_FEE.get(c.get("processor", "ultra"))
            else:
                p = None
            est.append(f"{a} ~${p * len(r_rows):.0f}" if p is not None else f"{a} metered (tokens + tools; not estimated)")
        print("Research list-price estimate: " + "; ".join(est))
    if args.dry_run:
        return 0
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    path = run_dir / "retrieval.jsonl"
    latest = {(r["id"], r["arm"]): r for r in R.read_jsonl(path)}
    done = {k for k, r in latest.items() if not r.get("error")}
    jobs = [(r, a) for r, a in jobs if (r["id"], a) not in done]
    lock = threading.Lock()

    def work(job):
        row, arm = job
        cfg = usable[arm]
        rec = research_one(row, arm, cfg) if is_research_arm(cfg) else search_one(row, arm, cfg, args.pit_query, rewrites=rewrites)
        R.append_jsonl(path, rec, lock)
        return row["id"], arm, rec["error"]

    s_jobs = [j for j in jobs if not is_research_arm(usable[j[1]])]
    r_jobs = [j for j in jobs if is_research_arm(usable[j[1]])]
    total, n = len(jobs), 0
    # Research jobs mostly wait on the vendor (minutes each), so they get their own, wider pool and run alongside.
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex_s, cf.ThreadPoolExecutor(max_workers=args.research_workers) as ex_r:
        futs = [ex_s.submit(work, j) for j in s_jobs] + [ex_r.submit(work, j) for j in r_jobs]
        for fut in cf.as_completed(futs):
            n += 1
            i, a, e = fut.result()
            print(f"[{n}/{total}] {i:14} {a:20} {'ERROR ' + e[:120] if e else 'ok'}", flush=True)
    write_outputs(run_dir, meta)
    return 0


# ─────────────────────────────── LLM-free retrieval metrics ───────────────────────────────
def norm(s):
    s = unicodedata.normalize("NFKD", s or "").lower()
    return re.sub(r"[^a-z0-9$%.]+", " ", s).strip()


# Pages that republish a public benchmark's questions with their gold answers (the dataset itself, user mirrors
# of it, published result files). A search that returns one has found the answer key, not the answer, so these
# results are dropped before scoring and before the handoff. Keyed by the row's source_benchmark prefix.
BENCHMARK_LEAK_RE = {
    "finsearchcomp": re.compile(r"finsearchcomp|linkupplatform/linkup-finance-benchmark", re.I),
    "linkup-gtm-funding": re.compile(r"linkupplatform/search-benchmarks-on-gtm-usecases", re.I),
}


def _leak_re(row):
    sb = row.get("source_benchmark") or ""
    return next((rx for k, rx in BENCHMARK_LEAK_RE.items() if sb.startswith(k)), None)


def is_benchmark_page(row, url):
    rx = _leak_re(row)
    return bool(rx and url and rx.search(url))


def clean_results(row, results):
    """Results with the benchmark's own answer pages removed."""
    return [x for x in results if not is_benchmark_page(row, x.get("url"))]


def real_gold_sources(row):
    """Gold sources minus the benchmark's own pages (for those rows, matching the dataset page isn't a source hit)."""
    return [s for s in row["gold_sources"] if not is_benchmark_page(row, s)]


_NUM_RE = re.compile(r"(?<![\d.])(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)")
_MONEY_RE = re.compile(r"(?:\$|US\$|USD\s?|€)\s?(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s?(M|million|mn|B|billion|bn)\b", re.I)
_RANGE_RE = re.compile(r"accept \$([\d.]+)([MB]) to \$([\d.]+)([MB])")


def _sig_digits(s):
    return len(s.replace(",", "").replace(".", "").lstrip("0"))


def _numbers(text):
    return [(float(m.replace(",", "")), _sig_digits(m)) for m in _NUM_RE.findall(text)]


def numeric_fact_hit(fact, text):
    """Number-aware match for the two numeric fact styles bench2 uses; None if the fact is neither style.
    - "... (accept $21.0M to $35.0M)": some money amount in the text falls inside the accepted range.
    - "... rounding errors are allowed": every number in the fact (years left out) appears in the text within
      ±0.5%, allowing thousand/million scale differences. Numbers under 3 significant digits must match exactly."""
    m = _RANGE_RE.search(fact)
    if m:
        to_m = lambda v, u: float(v) * (1e3 if u == "B" else 1)
        lo, hi = to_m(m[1], m[2]), to_m(m[3], m[4])
        return any(lo <= float(v.replace(",", "")) * (1e3 if u.lower() in ("b", "billion", "bn") else 1) <= hi
                   for v, u in _MONEY_RE.findall(text))
    if "rounding errors are allowed" not in fact.lower():
        return None
    want = [(v, d) for v, d in _numbers(fact) if not (v.is_integer() and 1900 <= v <= 2100)]
    if not want:
        return None
    have = _numbers(text)
    def found(n, d):
        if d < 3:
            return any(x == n for x, _ in have)
        return any(e >= 3 and any(abs(x * s - n) <= 0.005 * n for s in (1, 1e3, 1e-3, 1e6, 1e-6)) for x, e in have)
    return all(found(n, d) for n, d in want)


def evidence_hit(row, results):
    """Rough recall proxy: does any result's title or content contain a required fact or an acceptable variant
    (normalised substring, at least 4 characters), or, for numeric facts, the gold number (numeric_fact_hit)?
    Benchmark answer pages are ignored. Misses paraphrases, so it undercounts; number matching can also hit by
    chance on number-heavy pages, which is what chance_hits measures."""
    results = clean_results(row, results)
    raw = " ".join((x.get("title") or "") + " " + (x.get("content") or "") for x in results)
    text = norm(raw)
    cands = [norm(c) for c in [*row["required_facts"], *row["acceptable_variants"]]]
    if any(len(c) >= 4 and c in text for c in cands):
        return True
    return any(numeric_fact_hit(f, raw) for f in row["required_facts"])


def chance_hits(rows_by_id, ok_by_id, ids):
    """Evidence hits when each row's facts are checked against another question's results (same question type,
    fixed rotation): how often evidence_hit fires by luck on this arm's pages. Compare with the real count."""
    by_pat = collections.defaultdict(list)
    for i in ids:
        if i in ok_by_id:
            by_pat[rows_by_id[i]["pattern"]].append(i)
    n = 0
    for p_ids in by_pat.values():
        if len(p_ids) < 2:
            continue
        k = len(p_ids) // 2
        for j, i in enumerate(p_ids):
            other = ok_by_id[p_ids[(j + k) % len(p_ids)]]
            n += evidence_hit(rows_by_id[i], other["search_calls"][0].get("results") or [])
    return n


def retrieval_scorecard(meta, rows_by_id, recs):
    A = {(r["id"], r["arm"]): r for r in recs}
    arms = [a for a in meta["arms"] if not is_research_arm(meta["arms"][a])]
    ids = sorted({r["id"] for r in recs}, key=lambda i: (rows_by_id[i]["team"], i))
    L = [f"# Retrieval scorecard: {meta['run_id']}", "",
         f"Questions: **{meta.get('gold', 'bench1')}** · split: **{meta['split']}** · rows: {len(ids)} · one search per question "
         f"and arm, query as typed · no LLM · as-of date in query text on point-in-time rows: {meta['pit_query']} · run date: {meta['run_date']}", "",
         "These metrics need no model. Correctness comes after the Claude Code session answers and grades "
         "(see handoff/INSTRUCTIONS.md), in scorecard.md.", "",
         "| Arm | Errors | Results / q | Evidence in results | Chance match | Gold source in results | Benchmark page returned | "
         "Authoritative share of results | Metadata complete | Point-in-time leaks | p50 search ms | Search $ / q (list) |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for a in arms:
        rs = [A[(i, a)] for i in ids if (i, a) in A]
        if not rs:
            continue
        ok = [r for r in rs if not r["error"]]
        raw = lambda r: r["search_calls"][0].get("results") or []
        res = lambda r: clean_results(rows_by_id[r["id"]], raw(r))
        leaked = sum(len(res(r)) < len(raw(r)) for r in ok)
        allres = [x for r in ok for x in res(r)]
        ev = sum(evidence_hit(rows_by_id[r["id"]], res(r)) for r in ok)
        chance = chance_hits(rows_by_id, {r["id"]: r for r in ok}, ids)
        with_gold = [r for r in ok if real_gold_sources(rows_by_id[r["id"]])]
        gold = sum(any(R.domain_match(x.get("url") or "", [R.host(s) for s in real_gold_sources(rows_by_id[r["id"]])]) for x in res(r))
                   for r in with_gold)
        auth = sum(R.domain_match(x.get("url") or "", rows_by_id[r["id"]]["authoritative_domains"]) for r in ok for x in res(r))
        meta_ok = sum(bool(x.get("url")) and bool(x.get("title")) and bool(x.get("published_date")) for x in allres)
        pit = [r for r in ok if r.get("point_in_time")]
        leaks = sum(1 for r in pit for x in res(r) if (x.get("published_date") or "")[:10] > r["point_in_time"])
        pit_n = sum(len(res(r)) for r in pit)
        lat = [r["search_calls"][0]["latency_ms"] for r in ok]
        fees = [R.call_fee(r["search_calls"][0], meta["arms"][a]["backend"]) for r in ok]
        fee = f"{sum(fees) / len(ok):.3f}" if ok and all(f is not None for f in fees) else "—"
        pit_s = f"{leaks}/{pit_n} dated after cutoff" if pit else "no point-in-time rows"
        L.append(f"| {a} | {len(rs) - len(ok)} | {(len(allres) / len(ok) if ok else 0):.1f} | {ev}/{len(ok)} | {chance} | "
                 f"{gold}/{len(with_gold)} | {leaked}/{len(ok)} | "
                 f"{(auth / len(allres) if allres else 0):.0%} | {(meta_ok / len(allres) if allres else 0):.0%} | "
                 f"{pit_s} | {R.pct(lat, .5) if lat else '—'} | {fee} |")
    L += ["", "- **Evidence in results**: a required fact or acceptable variant appears word for word in a result's title or "
          "content, or, for numeric facts (\"rounding errors are allowed\", \"accept $X to $Y\"), the gold number does "
          "(±0.5%, any thousand/million scale) or a money amount inside the accepted range does. A rough recall proxy: it "
          "misses paraphrases, and on number-heavy pages it can hit by luck.",
          "- **Chance match**: the same check with each question's facts tested against a different question's results "
          "(same question type). Read evidence as the gap above this, not the raw count.",
          "- **Benchmark page returned**: questions where the arm returned a page that republishes the source benchmark with "
          "its answers (the dataset, a mirror, a published results file). Those results are removed from every other column "
          "and from the handoff, so no arm gets credit for finding the answer key.",
          "- **Gold source in results**: a result's domain matches a gold source's domain, over the questions that have a "
          "gold source other than the benchmark itself.",
          "- **Point-in-time leaks**: results whose publish date is after the row's cutoff. Results with no date can't be "
          "checked, and pages rewritten after publication keep their old date, so this is a lower bound.", ""]
    r_arms = [a for a in meta["arms"] if is_research_arm(meta["arms"][a])]
    if r_arms:
        L += ["## Research jobs (research rows only)", "", "| Arm | Jobs | Errors | p50 minutes | Sources / answer | $ total | $ / job |",
              "|---|---|---|---|---|---|---|"]
        for a in r_arms:
            rs = [r for r in recs if r["arm"] == a]
            ok = [r for r in rs if not r["error"]]
            mins = [r["research_call"]["latency_ms"] / 60000 for r in ok]
            fees = [r["research_call"].get("fee_usd") for r in ok]
            tot = sum(f for f in fees if f is not None)
            L.append(f"| {a} | {len(rs)} | {len(rs) - len(ok)} | {(f'{statistics.median(mins):.1f}' if mins else '—')} | "
                     f"{(statistics.mean(len(r['research_call']['sources']) for r in ok) if ok else 0):.1f} | "
                     f"{tot:.2f}{'' if all(f is not None for f in fees) else ' (some unpriced)'} | {(tot / len(ok) if ok else 0):.3f} |")
        L.append("")
    for title, key in (("By team", lambda r: r["team"]), ("By question type", lambda r: r["pattern"]),
                       ("By origin", lambda r: r.get("source_benchmark") or r.get("origin") or "claude"),
                       ("By workflow", lambda r: r.get("workflow") or "chat Q&A")):
        L += [f"## Evidence in results, {title.lower()}", "", "Chance match in brackets where it is above zero.", "",
              "| Slice | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
        for k in sorted({key(rows_by_id[i]) for i in ids}, key=str):
            kid = [i for i in ids if key(rows_by_id[i]) == k]
            cells = []
            for a in arms:
                ok = [A[(i, a)] for i in kid if (i, a) in A and not A[(i, a)]["error"]]
                hit = sum(evidence_hit(rows_by_id[r['id']], r['search_calls'][0].get('results') or []) for r in ok)
                ch = chance_hits(rows_by_id, {r["id"]: r for r in ok}, kid)
                cells.append(f"{hit}/{len(ok)}" + (f" ({ch})" if ch else ""))
            L.append(f"| {k} (n={len(kid)}) | " + " | ".join(cells) + " |")
        L.append("")
    return "\n".join(L)


# ─────────────────────────────── handoff for Claude Code ───────────────────────────────
INSTRUCTIONS = """# Claude Code handoff: answer, then grade

This folder holds {n} blinded tasks from a retrieval-only benchmark run (`{run_id}`). Each task is one question
plus the search results one search API returned for it. **The API is hidden on purpose**: don't open `_key.json`,
`answers_research.jsonl` or anything outside this folder, and don't try to work out which vendor produced a task.
Do the tasks in the order given.

## Step 1: answer (`tasks_pending.jsonl` -> `answers.jsonl`)

`tasks_pending.jsonl` holds the {n_pending} tasks that have no answer yet (`tasks.jsonl` has all {n}). **Append** to
`answers.jsonl`; never rewrite or remove lines already in it. (Some task ids are missing from the sequence: those are
research-endpoint answers, already filled in by the harness. They only come back in step 2, mixed in with yours.)

You are the research assistant inside an investment fund's internal chat tool. For each line of `tasks_pending.jsonl`:

- Treat the task's `today` as the present date.
- Answer `question` using **only** the task's `results`. Don't use your own knowledge, other tasks' results, the web,
  or any other tool. If the results don't contain the answer, say you couldn't find it rather than guess.
- Be concise: the direct answer first, then the key facts with dates.
- List the result URLs you relied on.

Write one JSON object per line to `answers.jsonl`:
`{{"task_id": "...", "answer": "...", "citations": ["https://...", ...]}}`

When every pending task has a line in `answers.jsonl`, tell the user to run:
`.venv/bin/python scripts/retrieval_run.py grade-prompts {run_rel}`

## Step 2: grade (`grade_tasks_pending.jsonl` -> `grades.jsonl`)

`grade-prompts` writes `grade_tasks_pending.jsonl` with the answered tasks that have no grade yet (`grade_tasks.jsonl`
has every answered task). Each line has a `task_id` and a `prompt`: the benchmark's frozen grading rubric (SimpleQA
grader plus overrides) with the gold answer and the answer to grade. Follow each prompt exactly and judge only from
what it contains. Answers vary in length and style (some come from research endpoints); don't reward length or tone.
**Append** one JSON object per line to `grades.jsonl`; never rewrite lines already in it:
`{{"task_id": "...", "grade": "A|B|C", "missing_facts": [...], "contradictions": [...], "stale_or_leaked": false, "one_sided": false, "reason": "..."}}`
(A = CORRECT, B = INCORRECT, C = NOT_ATTEMPTED.)

Ideally step 2 runs in a **fresh session** that never saw the step 1 work, so the grader doesn't remember writing the answers.

Then tell the user to run:
`.venv/bin/python scripts/retrieval_run.py ingest {run_rel} --model "<the model this session ran on>"`
"""


def _rows_by_id(meta):
    rows, _ = R.load_rows("all", None, meta["run_date"], True, gold=meta.get("gold", "bench1"))
    return {r["id"]: r for r in rows}


def write_outputs(run_dir, meta):
    rows_by_id = _rows_by_id(meta)
    latest = {(r["id"], r["arm"]): r for r in R.read_jsonl(run_dir / "retrieval.jsonl")}
    recs = list(latest.values())
    (run_dir / "retrieval_scorecard.md").write_text(retrieval_scorecard(meta, rows_by_id, recs), encoding="utf-8")
    hd = run_dir / "handoff"
    hd.mkdir(exist_ok=True)
    ok = {(r["id"], r["arm"]): r for r in recs if not r["error"]}
    # Append-only: task ids already handed out keep their (row, arm), so answers/grades from an earlier
    # session stay valid when arms are added later. New pairs get the next ids, shuffled among themselves
    # (research and search pairs together, so ids don't reveal which is which).
    key = json.loads((hd / "_key.json").read_text()) if (hd / "_key.json").exists() else {}
    assigned = {tuple(v) for v in key.values()}
    new = sorted(k for k in ok if k not in assigned)
    random.Random(f"{meta['run_id']}:{len(key)}").shuffle(new)
    for n, pair in enumerate(new, len(key) + 1):
        key[f"T{n:04d}"] = list(pair)
    research = lambda arm: is_research_arm(meta["arms"].get(arm, {}))
    tasks, r_answers = [], []
    for tid, (rid, arm) in key.items():
        r = ok.get((rid, arm))
        if r is None:  # a job that was ok before but errors on a later retry: keep its id, no task
            continue
        if research(arm):
            rc = r["research_call"]
            r_answers.append({"task_id": tid, "answer": rc["answer"], "citations": [s["url"] for s in rc["sources"] if s.get("url")]})
            continue
        res = [{k: x.get(k) for k in ("url", "title", "published_date", "content")}
               for x in clean_results(rows_by_id[rid], r["search_calls"][0].get("results") or [])]
        tasks.append({"task_id": tid, "today": r["today"], "question": rows_by_id[rid]["query"], "results": res})
    (hd / "_key.json").write_text(json.dumps(key, indent=1))
    with open(hd / "answers_research.jsonl", "w", encoding="utf-8") as f:  # harness-owned; rebuilt on every write
        for a in r_answers:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")
    answered = set(_load_handoff(run_dir, "answers.jsonl")) if (hd / "answers.jsonl").exists() else set()
    pending = [t for t in tasks if t["task_id"] not in answered]
    for name, objs in (("tasks.jsonl", tasks), ("tasks_pending.jsonl", pending)):
        with open(hd / name, "w", encoding="utf-8") as f:
            for t in objs:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")
    run_rel = run_dir.relative_to(ROOT) if run_dir.is_relative_to(ROOT) else run_dir
    (hd / "INSTRUCTIONS.md").write_text(INSTRUCTIONS.format(n=len(tasks), n_pending=len(pending), run_id=meta["run_id"],
                                                            run_rel=run_rel), encoding="utf-8")
    errs = len(recs) - len(ok)
    print(f"Wrote {run_dir / 'retrieval_scorecard.md'} and {len(tasks)} handoff tasks in {hd} "
          f"({len(new)} new pairs, {len(pending)} still to answer, {len(r_answers)} research answers pre-filled)"
          + (f"; {errs} jobs errored and are left out" if errs else ""))


def _load_handoff(run_dir, name):
    path = run_dir / "handoff" / name
    if not path.exists():
        sys.exit(f"missing {path}")
    out, bad = {}, []
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        if not line.strip():
            continue
        try:
            o = json.loads(line)
            out[o["task_id"]] = o
        except (json.JSONDecodeError, KeyError) as e:
            bad.append(f"line {n}: {e}")
    if bad:
        sys.exit(f"{path}: unreadable lines: {bad[:5]}")
    return out


def _all_answers(run_dir):
    """Session answers (search arms) plus the harness's pre-filled research answers."""
    hd = run_dir / "handoff"
    out = _load_handoff(run_dir, "answers.jsonl") if (hd / "answers.jsonl").exists() else {}
    if (hd / "answers_research.jsonl").exists():
        out.update(_load_handoff(run_dir, "answers_research.jsonl"))
    if not out:
        sys.exit(f"no answers yet in {hd}")
    return out


def cmd_grade_prompts(args):
    run_dir = pathlib.Path(args.run_dir)
    meta = json.loads((run_dir / "meta.json").read_text())
    rows_by_id = _rows_by_id(meta)
    key = json.loads((run_dir / "handoff" / "_key.json").read_text())
    answers = _all_answers(run_dir)
    missing = sorted(set(key) - set(answers))
    if missing:
        print(f"WARN  {len(missing)} tasks have no answer yet and are left out: {missing[:10]}")
    tasks = []
    for tid in sorted(answers):
        if tid not in key:
            sys.exit(f"answers have unknown task_id {tid}")
        row = rows_by_id[key[tid][0]]
        today = row["point_in_time"] or meta["run_date"]
        trap = row["trap"] or ("point-in-time" if row.get("point_in_time") else "none")
        prompt = sqa.build_prompt(
            question=row["query"], target=row["gold_answer"], predicted_answer=answers[tid].get("answer") or "",
            intent=row["intent_note"], as_of=today,
            required_facts=json.dumps(row["required_facts"], ensure_ascii=False),
            acceptable_variants=json.dumps(row["acceptable_variants"], ensure_ascii=False),
            notes=row["verification_notes"] or "(none)", trap=trap)
        tasks.append({"task_id": tid, "prompt": prompt})
    graded = set(_load_handoff(run_dir, "grades.jsonl")) if (run_dir / "handoff" / "grades.jsonl").exists() else set()
    pending = [t for t in tasks if t["task_id"] not in graded]
    for name, objs in (("grade_tasks.jsonl", tasks), ("grade_tasks_pending.jsonl", pending)):
        with open(run_dir / "handoff" / name, "w", encoding="utf-8") as f:
            for t in objs:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")
    print(f"Wrote {len(tasks)} grading prompts to {run_dir / 'handoff' / 'grade_tasks.jsonl'} "
          f"({len(pending)} not graded yet -> grade_tasks_pending.jsonl)")
    return 0


def research_scorecard(meta, rows_by_id, agent_recs, judgments):
    """Research arms vs every search arm, on the research rows only (the rows the research arms ran on)."""
    J = {(j["id"], j["arm"]): j["grade"] for j in judgments}
    A = {(r["id"], r["arm"]): r for r in agent_recs}
    r_arms = [a for a in meta["arms"] if is_research_arm(meta["arms"][a])]
    ids = sorted({r["id"] for r in agent_recs if r["arm"] in r_arms}, key=lambda i: (rows_by_id[i]["team"], i))
    if not ids:
        return None
    arms = r_arms + [a for a in meta["arms"] if a not in r_arms]
    L = [f"# Research scorecard: {meta['run_id']}", "",
         f"Questions: **{meta.get('gold', 'bench1')}** · research rows only (finance and multi-hop questions): {len(ids)} · "
         f"research arms send the question to each vendor's deep-research endpoint and are graded on the vendor's own answer; "
         f"search arms are the same rows from the main run (one search, answer written by `{meta.get('agent_model')}`) for reference.", "",
         "| Arm | Kind | Correct | Incorrect | Not attempted | Accuracy when attempted | F1 | Errors | p50 latency | $ / q (list) | $ / correct |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for a in arms:
        recs = [A[(i, a)] for i in ids if (i, a) in A]
        if not recs:
            continue
        g = [J.get((r["id"], a), "ERROR") for r in recs]
        ok, bad, na, err = g.count("CORRECT"), g.count("INCORRECT"), g.count("NOT_ATTEMPTED"), g.count("ERROR")
        m = sqa.aggregate([x for x in g if x != "ERROR"])
        if is_research_arm(meta["arms"][a]):
            fees = [(r.get("research_call") or {}).get("fee_usd") for r in recs]
            lat = [r["latency_ms"] / 60000 for r in recs if not r["error"]]
            lat_s = f"{statistics.median(lat):.1f} min" if lat else "—"
        else:
            fees = [R.call_fee(c, meta["arms"][a]["backend"]) for r in recs for c in r["search_calls"]]
            lat = [c["latency_ms"] for r in recs for c in r["search_calls"] if "latency_ms" in c]
            lat_s = f"{R.pct(lat, .5)} ms" if lat else "—"
        priced = bool(fees) and all(f is not None for f in fees)
        L.append(f"| {a} | {'research' if is_research_arm(meta['arms'][a]) else 'search'} | **{ok}/{len(recs)}** | {bad} | {na} | "
                 f"{m.get('accuracy_given_attempted', 0):.0%} | {m.get('f1', 0):.2f} | {err} | {lat_s} | "
                 f"{(f'{sum(fees) / len(recs):.3f}' if priced else '—')} | {((f'{sum(fees) / ok:.3f}' if ok else '∞') if priced else '—')} |")
    L += ["", "Research list prices per question: Linkup by reasoningDepth (S $0.25, M $0.50, L $1.50, XL $2.50); Parallel by processor "
          "(ultra $0.30, ultra8x $2.40); Perplexity has no per-request price, so its $ is the actual cost the API reported "
          "(usage.cost.total_cost). Search arms: per-call list price. The answering model's cost is left out (same for every search arm).", ""]
    src = lambda i: rows_by_id[i].get("source_benchmark") or rows_by_id[i]["pattern"]
    L += ["## By source", "", "| Source | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
    for k in sorted({src(i) for i in ids}):
        kid = [i for i in ids if src(i) == k]
        L.append(f"| {k} (n={len(kid)}) | " + " | ".join(
            f"{sum(J.get((i, a)) == 'CORRECT' for i in kid)}/{sum((i, a) in A for i in kid)}" for a in arms) + " |")
    mark = {"CORRECT": "✅", "INCORRECT": "❌", "NOT_ATTEMPTED": "➖", "ERROR": "⚠️"}
    L += ["", "## Per question", "", "| ID | Source | " + " | ".join(arms) + " |", "|---|---|" + "---|" * len(arms)]
    for i in ids:
        L.append(f"| {i} | {src(i)} | " + " | ".join(mark.get(J.get((i, a)), "—") for a in arms) + " |")
    return "\n".join(L) + "\n"


def cmd_ingest(args):
    run_dir = pathlib.Path(args.run_dir)
    meta = json.loads((run_dir / "meta.json").read_text())
    key = json.loads((run_dir / "handoff" / "_key.json").read_text())
    answers = _all_answers(run_dir)
    grades = _load_handoff(run_dir, "grades.jsonl")
    latest = {(r["id"], r["arm"]): r for r in R.read_jsonl(run_dir / "retrieval.jsonl")}
    model = args.model or "claude-code-session"
    meta.update(agent_model=f"{model} via Claude Code (1 search, results given)", judge_model=f"{model} via Claude Code",
                agent_effort="n/a")
    agent_recs, judgments, counts = [], [], collections.Counter()
    for tid, (rid, arm) in key.items():
        base = latest[(rid, arm)]
        a, g = answers.get(tid), grades.get(tid)
        rc = base.get("research_call") or {}
        lat = rc.get("latency_ms", 0) if rc else (base["search_calls"][0].get("latency_ms", 0) if base["search_calls"] else 0)
        rec = {**{k: v for k, v in base.items() if k != "research_call"}, "answer": (a or {}).get("answer", ""),
               "citations": (a or {}).get("citations", []) or [],
               "stop_reason": ("research_endpoint" if rc else "claude_code") if a else "no_answer", "latency_ms": lat,
               "tokens_in": 0, "tokens_out": 0, "cache_write_tokens": 0, "cache_read_tokens": 0, "llm_cost_usd": 0.0,
               "fallback_ran": False, "agent_model": "vendor research endpoint" if rc else meta["agent_model"],
               "agent_effort": "n/a", "task_id": tid}
        if rc:
            rec["research_call"] = {k: rc.get(k) for k in ("job_id", "status", "latency_ms", "fee_usd", "request", "sources")}
        if not a:
            rec["error"] = rec["error"] or "no answer in handoff"
        agent_recs.append(rec)
        if g and a:
            letter = (g.get("grade") or "").strip().upper()[:1]
            j = {**{k: g.get(k) for k in ("missing_facts", "contradictions", "stale_or_leaked", "one_sided", "reason")},
                 "letter": letter, "grade": sqa.LETTER_TO_GRADE.get(letter, "ERROR"), "judge_model": meta["judge_model"],
                 "judge_cost_usd": 0.0, "judge_fallback_ran": False}
        else:
            j = {"grade": "ERROR", "reason": "no answer" if not a else "no grade in handoff/grades.jsonl"}
        j.update(id=rid, arm=arm)
        judgments.append(j)
        counts[j["grade"]] += 1
    for name, objs in (("agent.jsonl", agent_recs), ("judgments.jsonl", judgments)):
        with open(run_dir / name, "w", encoding="utf-8") as f:
            for o in objs:
                f.write(json.dumps(o, ensure_ascii=False, default=str) + "\n")
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    rows_by_id = _rows_by_id(meta)
    s_arms = [a for a in meta["arms"] if not is_research_arm(meta["arms"][a])]
    s_recs = [r for r in agent_recs if r["arm"] in s_arms]
    s_judg = [j for j in judgments if j["arm"] in s_arms]
    (run_dir / "scorecard.md").write_text(R.scorecard(rows_by_id, s_recs, s_judg, s_arms, meta), encoding="utf-8")
    rs = research_scorecard(meta, rows_by_id, agent_recs, judgments)
    if rs:
        (run_dir / "research_scorecard.md").write_text(rs, encoding="utf-8")
    rpath, n_rev, _ = R.write_review_csv(run_dir, rows_by_id, agent_recs, judgments)
    print(f"Ingested {len(agent_recs)} tasks ({dict(counts)}). Wrote {run_dir / 'scorecard.md'}"
          + (f", {run_dir / 'research_scorecard.md'}" if rs else "") + f" and {rpath} ({n_rev} for human review).")
    return 0


# ─────────────────────────────── query rewrites for linkup-rewritten ───────────────────────────────
REWRITE_INSTRUCTIONS = """# Claude Code task: rewrite queries for Linkup (`{gold}`)

`{tasks_rel}` holds {n} questions as fund users typed them (id, team, question). Write one rewritten query per line to
`{out_rel}`: `{{"id": "...", "q": "..."}}`. These feed the `linkup-rewritten` arm (Linkup standard depth), which tests
whether following Linkup's query guidance helps. Work **blind**: don't open the gold files, `runs/`, or search the web,
and don't use what you know about the answer. Ideally use a fresh session.

Linkup's guidance for standard depth (docs.linkup.so, search best practices), which the rewrite must follow:
- Standard depth follows natural-language instructions literally, so write the query as a retrieval instruction.
- Name the evidence to retrieve instead of asking for an answer: the document types and sources that would hold it
  (e.g. the company's 8-K or press release, the 10-K, the regulator's rule page, the court docket, the vendor's
  release notes), the full entity name (and ticker when the question gives it or it's unambiguous), and the fields
  to extract.
- **No dates or date ranges in the text** ("as of", "in 2026", "latest as of ..."): the harness sends the date bound
  as `toDate`. Keep relative words the user wrote ("current", "latest", "now") and any period the question itself
  asks about (e.g. "fiscal year 2019", "Q3 FY27"), since those identify the fact, not a search window.
- Don't add facts that could be the answer: no names, numbers, outcomes or dates of the event you think happened.
  If you recognise the answer, still write the query as if you didn't.
- One query, at most ~60 words. Keep the user's intent and scope; don't add sub-questions.
"""


def cmd_rewrite_prompts(args):
    rows, _ = R.load_rows("all", None, dt.date.today().isoformat(), True, gold=args.gold)
    REWRITES_DIR.mkdir(parents=True, exist_ok=True)
    tasks = REWRITES_DIR / f"{args.gold}_tasks.jsonl"
    out = REWRITES_DIR / f"{args.gold}.jsonl"
    with open(tasks, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({"id": r["id"], "team": r["team"], "question": r["query"]}, ensure_ascii=False) + "\n")
    done = load_rewrites(args.gold) or {}
    instr = REWRITES_DIR / f"{args.gold}_INSTRUCTIONS.md"
    instr.write_text(REWRITE_INSTRUCTIONS.format(gold=args.gold, n=len(rows), tasks_rel=tasks.relative_to(ROOT),
                                                 out_rel=out.relative_to(ROOT)), encoding="utf-8")
    print(f"Wrote {len(rows)} rewrite tasks to {tasks} and instructions to {instr} "
          f"({len(set(r['id'] for r in rows) - set(done))} without a rewrite yet in {out.name}).")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="search every arm, no LLM; writes retrieval scorecard + Claude Code handoff")
    r.add_argument("--gold", default="bench1", choices=list(R.GOLD_FILES), help="question set (ignored with --resume)")
    r.add_argument("--split", default="all", choices=["dev", "test", "all"])
    r.add_argument("--ids", nargs="*")
    r.add_argument("--arms", nargs="*", help=f"default: {' '.join(DEFAULT_ARMS)} (those with a key)")
    r.add_argument("--no-research", action="store_true", help="leave out the research arms")
    r.add_argument("--tuned", help="JSON config for linkup-tuned (configs/linkup_tuned.json)")
    r.add_argument("--run-date", default=dt.date.today().isoformat())
    r.add_argument("--pit-query", default="all", choices=R.PIT_QUERY_MODES)
    r.add_argument("--include-expired", action="store_true")
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--research-workers", type=int, default=6, help="concurrent research jobs (they mostly wait)")
    r.add_argument("--resume", help="existing retrieval run dir: retry errored jobs, add new arms")
    r.add_argument("--dry-run", action="store_true")
    g = sub.add_parser("grade-prompts", help="build grading prompts from handoff answers")
    g.add_argument("run_dir")
    i = sub.add_parser("ingest", help="merge handoff answers + grades into the standard scorecard")
    i.add_argument("run_dir")
    i.add_argument("--model", help="model the Claude Code session ran on, for the scorecard header")
    w = sub.add_parser("rewrite-prompts", help="write blind rewrite tasks for the linkup-rewritten arm")
    w.add_argument("--gold", default="bench1", choices=list(R.GOLD_FILES))
    args = ap.parse_args()
    return {"run": cmd_run, "grade-prompts": cmd_grade_prompts, "ingest": cmd_ingest,
            "rewrite-prompts": cmd_rewrite_prompts}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())

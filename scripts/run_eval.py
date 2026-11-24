#!/usr/bin/env python3
"""Run the search-API eval: same LLM agent, only the search backend varies.

    .venv/bin/python scripts/run_eval.py --ping                 # check keys: 1 search per backend, no LLM
    .venv/bin/python scripts/run_eval.py --dry-run              # show the plan, no calls
    .venv/bin/python scripts/run_eval.py                        # dev split, all arms with a key
    .venv/bin/python scripts/run_eval.py --tuned configs/linkup_tuned.json   # adds the linkup-tuned arm
    .venv/bin/python scripts/run_eval.py --resume runs/<run_id> --arms linkup-native  # add an arm to an existing run
    .venv/bin/python scripts/run_eval.py --resume runs/<run_id> # finish an interrupted run
    .venv/bin/python scripts/run_eval.py --rejudge runs/<run_id>  # re-grade saved answers (after a rubric fix)
    .venv/bin/python scripts/run_eval.py --split test           # ONLY after the Linkup config is frozen

Keys are read from .env (see .env.example). Arms whose key is missing are skipped with a warning.

Per (row, arm) it logs to runs/<run_id>/: the agent's answer, every search call (request, raw
vendor response, latency), token use and cost (agent.jsonl), then the judge's grade
(judgments.jsonl), then a scorecard (scorecard.md).
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import pathlib
import re
import statistics
import sys
import threading
import time
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import anthropic  # noqa: E402

import simpleqa_grader as sqa  # noqa: E402
from search_backends import BACKENDS, SearchError  # noqa: E402

# ─────────────────────────────── config ───────────────────────────────
AGENT_MODEL = "claude-sonnet-5-5"
JUDGE_MODEL = "claude-opus-5-5"  # different model from the agent; same family (see EVAL_DESIGN §3)
PRICES = {  # $ per 1M tokens, Anthropic first-party: input, output, cache write (5-min, 1.25x input), cache read
    "claude-sonnet-5-5": {"in": 2.00, "out": 10.00, "cache_write": 2.50, "cache_read": 0.10},
    "claude-opus-5-5": {"in": 4.00, "out": 20.00, "cache_write": 5.00, "cache_read": 0.20},
}
FALLBACK_BETA = "server-side-fallback-2026-07-01"
MAX_SEARCH_CALLS = 6
TOP_K = 10

ARMS = {
    "linkup-standard": {"backend": "linkup", "depth": "standard"},
    "linkup-deep": {"backend": "linkup", "depth": "deep"},
    # Linkup's recommended default for agents: keyword-style, ~1s, $0.005.
    "linkup-fast": {"backend": "linkup", "depth": "fast"},
    # Standard depth with the query rewritten per Linkup's best practices (evidence named, no dates in the text;
    # the point-in-time bound goes only in toDate). Rewrites come from gold/rewrites/<gold>.jsonl (retrieval_run.py
    # rewrite-prompts), written blind to gold answers and results.
    "linkup-rewritten": {"backend": "linkup", "depth": "standard", "rewrite": True},
    "perplexity": {"backend": "perplexity"},
    "parallel": {"backend": "parallel"},
}
BASELINE_ARM = "linkup-standard"
NATIVE_CONFIG = ROOT / "configs" / "linkup_native.json"

SYSTEM = """You are the research assistant inside an investment fund's internal chat tool. Today's date is {today}.

Answer the user's question using the {tool} tool. Search before answering anything about current facts, rules, figures, people or events. Don't rely on what you remember, because it may be out of date: treat {today} as the present. You can call {tool} up to {max_calls} times.

Lead with the direct answer, then the key supporting details. Cite the pages you relied on as [n] in the text, with a Sources list of URLs at the end. If the results don't settle the question, or credible sources disagree, say so plainly instead of guessing."""

SEARCH_TOOL = {
    "name": "web_search",
    "description": "Search the web. Returns up to 10 results, each with url, title, published_date and an extract of the page content.",
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "The search query."}},
        "required": ["query"],
        "additionalProperties": False,
    },
    "strict": True,
}

# ── linkup-native arm: Linkup's own tool shape and query guidance, from docs.linkup.so
# (search/best-practices, search/for-agents, tutorials/filtering; read 2026-11-23). The generic arms
# above keep the vendor-neutral web_search tool. Comparing linkup-native with a generic competitor arm
# is NOT like-for-like: the fair comparison is against perplexity-native / parallel-native built from
# those vendors' docs the same way.
LINKUP_GUIDE = """
How to use linkup_search (this follows Linkup's own guidance):
- depth "standard" is the default (about 1-3 s). Linkup's search agent reads your query and can run several sub-searches in parallel, so write a retrieval request: say what to find, not what to conclude. Good: "Find the IRS announcement of the 2027 401(k) contribution limits." Weak: "401k limit 2027?". To widen coverage, add "Run several searches with adjacent keywords." It can also read one URL you put in the query.
- depth "fast" (about 1 s) is a keyword lookup with no instruction-following. Use it for a single simple fact, with a short keyword query.
- depth "deep" takes 5-30 s and costs 10x. Use it only when steps depend on each other or several pages must be read, and write the steps in order: "First find X's press release. Then scrape it. Then extract the effective date."
- Put date ranges in from_date / to_date (YYYY-MM-DD), not in the query text. For "latest", "this week" or "just announced" questions, set from_date to a recent date.
- To favour primary sources (sec.gov, irs.gov, a court, the company's own site) without losing others, list them in prioritize_domains. Use include_domains only when the answer must come solely from those domains: it is a hard filter, so everything else disappears.
"""

LINKUP_TOOL = {
    "name": "linkup_search",
    "description": ("Search the web with Linkup. Use it whenever you need current facts, specific named entities, recent "
                    "events, or anything likely missing from your training data. Returns up to 10 results, each with url, "
                    "title, published_date and an extract of the page content."),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Be specific: include the key entity and terms. For standard/deep, "
                      "a retrieval request (what to find); for fast, short keywords. Don't put date ranges here."},
            "depth": {"type": "string", "enum": ["fast", "standard", "deep"],
                      "description": "standard by default; fast for a single keyword fact; deep only when one step depends on another."},
            "from_date": {"type": "string", "format": "date", "description": "Only results published on or after this date (YYYY-MM-DD)."},
            "to_date": {"type": "string", "format": "date", "description": "Only results published on or before this date (YYYY-MM-DD)."},
            "prioritize_domains": {"type": "array", "items": {"type": "string"},
                                   "description": "Domains to favour, e.g. [\"sec.gov\"]. Other sources still appear. Ignored by fast."},
            "include_domains": {"type": "array", "items": {"type": "string"},
                                "description": "Hard filter: return ONLY these domains. Use rarely."},
        },
        "required": ["query", "depth"],
        "additionalProperties": False,
    },
    "strict": True,
}

# Judge prompt, schema and aggregate metrics: scripts/simpleqa_grader.py (SimpleQA grader + benchmark overrides)


# ─────────────────────────────── utils ───────────────────────────────
def load_env(path: pathlib.Path):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = re.split(r"\s+#", v, maxsplit=1)[0]  # allow "KEY=value   # comment"
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def make_client() -> anthropic.Anthropic:
    """Org-level API keys (not scoped to a workspace) need the anthropic-workspace-id header."""
    ws = os.environ.get("ANTHROPIC_WORKSPACE_ID", "").strip()
    return anthropic.Anthropic(default_headers={"anthropic-workspace-id": ws} if ws else None)


def host(url: str) -> str:
    try:
        h = urllib.parse.urlparse(url).hostname or ""
    except ValueError:
        return ""
    return h[4:] if h.startswith("www.") else h


def domain_match(url: str, domains) -> bool:
    h = host(url)
    return any(h == d or h.endswith("." + d) for d in domains if d)


URL_RE = re.compile(r"https?://[^\s\)\]\>\"'`]+")


def extract_urls(text: str) -> list[str]:
    seen, out = set(), []
    for u in URL_RE.findall(text or ""):
        u = u.rstrip(".,;:")
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def cost_usd(model, tok_in, tok_out, cache_write=0, cache_read=0):
    p = PRICES[model]
    return (tok_in * p["in"] + tok_out * p["out"] + cache_write * p["cache_write"] + cache_read * p["cache_read"]) / 1e6


def fallback_ran(response) -> bool:
    return any(getattr(e, "type", None) == "fallback_message"
               for e in (getattr(response.usage, "iterations", None) or []))


def pct(xs, q):
    if not xs:
        return None
    xs = sorted(xs)
    i = min(len(xs) - 1, max(0, round(q * (len(xs) - 1))))
    return xs[i]


# ─────────────────────────────── agent ───────────────────────────────
def search_params(row, arm_cfg, use_date_filter):
    """Per-row filters the harness sets: per-team settings (the fund knows each user's team from their
    login) and the point-in-time upper bound. Nothing here reads gold labels such as pattern or trap."""
    p = {"include": None, "exclude": None, "from_date": None, "to_date": None, "prioritize": None}
    team_cfg = (arm_cfg.get("teams") or {}).get(row["team"], {})
    p["include"] = team_cfg.get("include_domains") or None
    p["exclude"] = team_cfg.get("exclude_domains") or arm_cfg.get("exclude_domains") or None
    p["prioritize"] = team_cfg.get("prioritize_domains") or None
    if use_date_filter and row.get("point_in_time"):
        p["to_date"] = row["point_in_time"]
    return p


def _iso(s):
    try:
        return dt.date.fromisoformat(s) if s else None
    except (TypeError, ValueError):
        raise ValueError(f"bad date {s!r}: use YYYY-MM-DD")


def native_params(base, tool_input, today):
    """Merge what the agent asked for (linkup_search inputs) with what the harness enforces.
    The point-in-time upper bound always wins, and dates after the agent's 'today' are dropped."""
    p = dict(base)
    today = dt.date.fromisoformat(today)
    frm, to = _iso(tool_input.get("from_date")), _iso(tool_input.get("to_date"))
    if base["to_date"]:
        cap = dt.date.fromisoformat(base["to_date"])
        to = min(to, cap) if to else cap
    if to and to > today:
        to = None
    if frm and (frm > today or (to and frm >= to)):
        frm = None
    p["from_date"] = frm.isoformat() if frm else None
    p["to_date"] = to.isoformat() if to else None
    clean = lambda ds: [d.strip().lower().removeprefix("https://").removeprefix("http://").removeprefix("www.").strip("/")
                        for d in ds or [] if d and d.strip()]
    prio = list(dict.fromkeys(clean(base["prioritize"]) + clean(tool_input.get("prioritize_domains"))))
    p["prioritize"] = prio or None
    p["include"] = clean(tool_input.get("include_domains")) or base["include"]
    return p


PIT_QUERY_MODES = ("all", "unsupported", "off")


def pit_query(q: str, row, backend, mode: str) -> str:
    """On point-in-time rows, state the as-of date in the query text itself.

    Parallel's Search API has no upper date bound (source_policy has after_date only), so without this it
    would get no cutoff at all. 'all' adds the same sentence for every arm, so the query text stays
    identical across arms and only each backend's own date filter differs. 'unsupported' adds it only
    where the backend can't filter; 'off' never adds it."""
    pit = row.get("point_in_time")
    if not pit or mode == "off" or (mode == "unsupported" and backend.supports.get("to_date")):
        return q
    d = dt.date.fromisoformat(pit)
    q = q.rstrip()
    return f"{q}{'' if q.endswith(('.', '?', '!')) else '.'} As of {d:%B} {d.day}, {d.year}: only use sources published on or before that date."


def run_agent(client, row, arm, arm_cfg, backend, args):
    today = row["_today"]
    native = bool(arm_cfg.get("native"))
    tool = LINKUP_TOOL if native else SEARCH_TOOL
    system = SYSTEM.format(today=today, max_calls=MAX_SEARCH_CALLS, tool=tool["name"]) + (LINKUP_GUIDE if native else "")
    messages = [{"role": "user", "content": row["query"]}]
    params = search_params(row, arm_cfg, use_date_filter=not args.no_date_filter)
    depth = (arm_cfg.get("teams") or {}).get(row["team"], {}).get("depth") or arm_cfg.get("depth")
    if depth:
        backend.opts["depth"] = depth

    calls, tok_in, tok_out, c_write, c_read, turns, used_fallback = [], 0, 0, 0, 0, 0, False
    stop, answer, error = None, "", None
    t0 = time.perf_counter()
    try:
        while turns < MAX_SEARCH_CALLS + 3:
            turns += 1
            resp = client.beta.messages.create(
                model=AGENT_MODEL, max_tokens=16000, system=system,
                tools=[tool], messages=messages,
                output_config={"effort": args.agent_effort},
                cache_control={"type": "ephemeral"},  # each turn resends the conversation; cache the prefix
                betas=[FALLBACK_BETA], fallbacks="default",
            )
            tok_in += resp.usage.input_tokens
            tok_out += resp.usage.output_tokens
            c_write += resp.usage.cache_creation_input_tokens or 0
            c_read += resp.usage.cache_read_input_tokens or 0
            used_fallback = used_fallback or fallback_ran(resp)
            stop = resp.stop_reason
            if stop == "pause_turn":
                messages.append({"role": "assistant", "content": resp.content})
                continue
            if stop != "tool_use":
                answer = "".join(b.text for b in resp.content if b.type == "text")
                break
            messages.append({"role": "assistant", "content": resp.content})
            results = []
            for b in [b for b in resp.content if b.type == "tool_use"]:
                q = (b.input or {}).get("query", "")
                if len(calls) >= MAX_SEARCH_CALLS:
                    results.append({"type": "tool_result", "tool_use_id": b.id, "is_error": True,
                                    "content": "Search limit reached. Answer now with what you have."})
                    continue
                try:
                    call_params = native_params(params, b.input or {}, today) if native else params
                except ValueError as e:
                    results.append({"type": "tool_result", "tool_use_id": b.id, "is_error": True, "content": str(e)})
                    continue
                call_depth = (b.input or {}).get("depth") if native else None
                sent_q = pit_query(q, row, backend, args.pit_query)
                call = {"query": q, "params": call_params, "depth": call_depth or backend.opts.get("depth"),
                        **({"sent_query": sent_q} if sent_q != q else {}),
                        **({"agent_input": b.input} if native else {})}
                try:
                    out = backend.search(sent_q, k=TOP_K, depth=call_depth, **call_params)
                    call.update(latency_ms=out["latency_ms"], n_results=len(out["results"]),
                                request=out["request"], raw=out["raw"], results=out["results"],
                                unsupported=out["unsupported"], fee_usd=out["fee_usd"])
                    payload = [{k: v for k, v in r.items() if k != "last_updated" or v} for r in out["results"]]
                    results.append({"type": "tool_result", "tool_use_id": b.id,
                                    "content": json.dumps(payload, ensure_ascii=False)})
                except SearchError as e:
                    call.update(error=str(e))
                    results.append({"type": "tool_result", "tool_use_id": b.id, "is_error": True,
                                    "content": f"Search failed: {e}"})
                calls.append(call)
            messages.append({"role": "user", "content": results})
        else:
            error = "turn limit reached without a final answer"
    except anthropic.APIStatusError as e:
        error = f"anthropic {e.status_code}: {e.message}"
    except anthropic.APIConnectionError as e:
        error = f"anthropic connection error: {e}"

    return {
        "id": row["id"], "arm": arm, "split": row["split"], "team": row["team"], "pattern": row["pattern"],
        "trap": row["trap"], "today": today, "point_in_time": row.get("point_in_time"),
        "date_filter": not args.no_date_filter, "answer": answer, "stop_reason": stop, "error": error,
        "citations": extract_urls(answer), "search_calls": calls, "n_search_calls": len(calls),
        "latency_ms": round((time.perf_counter() - t0) * 1000), "tokens_in": tok_in, "tokens_out": tok_out,
        "cache_write_tokens": c_write, "cache_read_tokens": c_read,
        "llm_cost_usd": round(cost_usd(AGENT_MODEL, tok_in, tok_out, c_write, c_read), 5), "fallback_ran": used_fallback,
        "agent_model": AGENT_MODEL, "agent_effort": args.agent_effort, "backend_opts": dict(backend.opts),
    }


# ─────────────────────────────── judge ───────────────────────────────
def judge(client, row, rec):
    if rec["error"] or not rec["answer"]:
        return {"grade": "ERROR", "reason": rec["error"] or f"no answer (stop_reason={rec['stop_reason']})"}
    trap = row["trap"] or ("point-in-time" if row.get("point_in_time") else "none")
    prompt = sqa.build_prompt(
        question=row["query"], target=row["gold_answer"], predicted_answer=rec["answer"], intent=row["intent_note"],
        as_of=row["_today"], required_facts=json.dumps(row["required_facts"], ensure_ascii=False),
        acceptable_variants=json.dumps(row["acceptable_variants"], ensure_ascii=False),
        notes=row["verification_notes"] or "(none)", trap=trap)
    try:
        resp = client.beta.messages.create(
            model=JUDGE_MODEL, max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
            output_config={"effort": "high", "format": {"type": "json_schema", "schema": sqa.GRADE_SCHEMA}},
            betas=[FALLBACK_BETA], fallbacks="default",
        )
    except anthropic.APIStatusError as e:
        return {"grade": "ERROR", "reason": f"judge anthropic {e.status_code}: {e.message}"}
    if resp.stop_reason == "refusal":
        return {"grade": "ERROR", "reason": "judge refused"}
    text = next((b.text for b in resp.content if b.type == "text"), "")
    try:
        out = json.loads(text)
    except json.JSONDecodeError:
        return {"grade": "ERROR", "reason": f"judge returned non-JSON: {text[:200]}"}
    out["letter"] = out.get("grade")
    out["grade"] = sqa.LETTER_TO_GRADE.get(out["letter"], "ERROR")
    out["judge_model"] = JUDGE_MODEL
    out["judge_cost_usd"] = round(cost_usd(JUDGE_MODEL, resp.usage.input_tokens, resp.usage.output_tokens,
                                           resp.usage.cache_creation_input_tokens or 0, resp.usage.cache_read_input_tokens or 0), 5)
    out["judge_fallback_ran"] = fallback_ran(resp)
    return out


# ─────────────────────────────── scoring ───────────────────────────────
def scorecard(rows_by_id, agent_recs, judgments, arms, meta) -> str:
    J = {(j["id"], j["arm"]): j for j in judgments}
    A = {(r["id"], r["arm"]): r for r in agent_recs}
    ids = sorted({r["id"] for r in agent_recs}, key=lambda i: (rows_by_id[i]["team"], i))
    lines = [f"# Scorecard: {meta['run_id']}", "",
             f"Questions: **{meta.get('gold', 'bench1')}** · split: **{meta['split']}** · rows: {len(ids)} · agent: `{meta.get('agent_model', AGENT_MODEL)}` (effort {meta['agent_effort']}) · "
             f"judge: `{meta.get('judge_model', JUDGE_MODEL)}` · date filter on point-in-time rows: {'on' if meta['date_filter'] else 'off'} · as-of date in query text: {meta.get('pit_query', 'off')} · run date: {meta['run_date']}", ""]
    if meta["split"] == "dev":
        lines += ["> Dev split: for tuning and a first look only. With this few rows, one question is ~6 points. Don't report these numbers as results.", ""]
    elif meta["split"] == "all":
        lines += ["> All rows, dev and test together. The dev rows were used for tuning linkup-tuned, so report test-split numbers for that arm.", ""]

    def grade(i, a):
        return (J.get((i, a)) or {}).get("grade", "—")

    # summary per arm
    lines += ["## Summary", "",
              "| Arm | Correct | Incorrect | Not attempted | Accuracy when attempted | F1 | Errors | Authoritative citations | Gold-source hit | Result metadata complete | Searches / q | p50 search ms | p50 answer s | LLM $ / q | Search $ / q (list) | Search $ / correct |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for a in arms:
        recs = [A[(i, a)] for i in ids if (i, a) in A]
        if not recs:
            continue
        g = [grade(r["id"], a) for r in recs]
        ok, bad, na, err = g.count("CORRECT"), g.count("INCORRECT"), g.count("NOT_ATTEMPTED"), g.count("ERROR")
        m = sqa.aggregate([x for x in g if x != "ERROR"])
        cites = [u for r in recs for u in r["citations"]]
        auth = sum(domain_match(u, rows_by_id[r["id"]]["authoritative_domains"]) for r in recs for u in r["citations"])
        gold_hit = sum(any(domain_match(u, [host(s) for s in rows_by_id[r["id"]]["gold_sources"]]) for u in r["citations"]) for r in recs)
        res = [x for r in recs for c in r["search_calls"] for x in c.get("results", [])]
        meta_ok = sum(bool(x.get("url")) and bool(x.get("title")) and bool(x.get("published_date")) for x in res)
        lat = [c["latency_ms"] for r in recs for c in r["search_calls"] if "latency_ms" in c]
        ans = [r["latency_ms"] / 1000 for r in recs if not r["error"]]
        fees = [call_fee(c, usable_backend(meta, a)) for r in recs for c in r["search_calls"]]
        priced = bool(fees) and all(f is not None for f in fees)
        fee_q = f"{sum(fees) / len(recs):.3f}" if priced else "—"
        fee_c = (f"{sum(fees) / ok:.4f}" if ok else "∞") if priced else "—"
        lines.append(
            f"| {a} | **{ok}/{len(recs)}** | {bad} | {na} | {m.get('accuracy_given_attempted', 0):.0%} | {m.get('f1', 0):.2f} | {err} | {auth}/{len(cites) or 0} | {gold_hit}/{len(recs)} | "
            f"{(meta_ok / len(res) if res else 0):.0%} of {len(res)} | {statistics.mean(r['n_search_calls'] for r in recs):.1f} | "
            f"{pct(lat, .5) if lat else '—'} | {(f'{pct(ans, .5):.1f}' if ans else '—')} | {statistics.mean(r['llm_cost_usd'] for r in recs):.3f} | {fee_q} | {fee_c} |")
    lines += ["", "Grading: SimpleQA grader (openai/simple-evals) plus this benchmark's required-facts rules. Not attempted = the answer "
              "doesn't give the required facts but contradicts nothing (an honest \"couldn't find it\" lands here). Accuracy when attempted = "
              "correct / (correct + incorrect); F1 is SimpleQA's harmonic mean of that and overall correct. An API that guesses "
              "less scores higher on accuracy when attempted.", "",
              "Result metadata complete = the result has a URL, a title and a publish date (publisher comes from the URL). "
              "Search $ = vendor list price per call x calls: Linkup $0.005 fast/standard, $0.05 deep (searchResults); "
              "Perplexity Search API $0.005 per request; Parallel Search API $0.005 per request in its default advanced mode "
              "with 10 results (pricing pages read 2026-11-24). Search $ / correct = total search spend / correct answers; it "
              "leaves out the answering model, which is the same for every arm. — = no checked list price. Contract pricing will differ.", ""]
    if any(meta["arms"].get(a, {}).get("native") for a in arms):
        lines += ["> **linkup-native** uses a Linkup-specific tool (depth, dates and domain priority chosen by the agent) and "
                  "Linkup's query guidance. The other arms use the generic web_search tool, so linkup-native vs a generic "
                  "competitor arm isn't like-for-like. Compare it with linkup-standard to see what Linkup's best practices "
                  "add, and with perplexity-native / parallel-native (built the same way from their docs) for the vendor decision.", ""]

    # paired comparison vs baseline and between Linkup and each competitor
    pairs = [(x, y) for x in arms for y in arms if x.startswith("linkup") and not y.startswith("linkup")]
    if pairs:
        lines += ["## Head-to-head (paired, same questions)", "",
                  "| Linkup arm | vs | Only Linkup right | Only competitor right | Both right | Both wrong |", "|---|---|---|---|---|---|"]
        for x, y in pairs:
            both = [i for i in ids if (i, x) in A and (i, y) in A]
            gx = {i: grade(i, x) == "CORRECT" for i in both}
            gy = {i: grade(i, y) == "CORRECT" for i in both}
            lines.append(f"| {x} | {y} | {sum(gx[i] and not gy[i] for i in both)} | {sum(gy[i] and not gx[i] for i in both)} | "
                         f"{sum(gx[i] and gy[i] for i in both)} | {sum(not gx[i] and not gy[i] for i in both)} |")
        lines.append("")

    # slices: correct / n per arm, with incorrect in brackets when any (a wrong answer is worse than a miss)
    PATTERNS = {"P1": "P1 news / freshness", "P2": "P2 official source", "P3": "P3 entity lookup",
                "P4": "P4 multi-hop", "P5": "P5 technical docs"}

    def freshness(i):
        r = rows_by_id[i]
        return "point-in-time twin" if r.get("point_in_time") else r["freshness"]

    def slice_table(title, keyfn, order=None, label=lambda k: k):
        keys = sorted({keyfn(i) for i in ids}, key=lambda k: (order.index(k) if order and k in order else 99, k))
        out = [f"## {title}", "", f"| {title.split(' ', 1)[1].capitalize()} | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
        for k in keys:
            kid = [i for i in ids if keyfn(i) == k]
            cells = []
            for a in arms:
                c = sum(grade(i, a) == "CORRECT" for i in kid)
                w = sum(grade(i, a) == "INCORRECT" for i in kid)
                cells.append(f"{c}/{len(kid)}" + (f" ({w}✗)" if w else ""))
            out.append(f"| {label(k)} (n={len(kid)}) | " + " | ".join(cells) + " |")
        return out + [""]

    lines += slice_table("By team", lambda i: rows_by_id[i]["team"], ["tech", "legal_rc", "tax_hr", "invest"])
    lines += slice_table("By question type", lambda i: rows_by_id[i]["pattern"], list(PATTERNS), lambda k: PATTERNS.get(k, k))
    lines += slice_table("By freshness", freshness, ["breaking", "volatile", "slow", "static", "point-in-time twin"])
    WORKFLOWS = {"sourcing_signal": "sourcing signal check", "crm_enrichment": "CRM enrichment",
                 "news_briefing": "fintech news briefing", None: "chat Q&A (no workflow)"}
    lines += slice_table("By workflow", lambda i: rows_by_id[i].get("workflow"), list(WORKFLOWS), lambda k: WORKFLOWS.get(k, k))
    SOURCES = {"finsearchcomp-t2": "FinSearchComp T2 (filings + macro lookup)", "finsearchcomp-t3": "FinSearchComp T3 (multi-step, filings)",
               "linkup-gtm-funding": "Private-company funding (±25% of Crunchbase)", "edgar-8k-exec": "8-K executive changes"}
    if any(rows_by_id[i].get("source_benchmark") for i in ids):
        lines += slice_table("By source benchmark", lambda i: rows_by_id[i].get("source_benchmark") or "fund queries",
                             list(SOURCES), lambda k: SOURCES.get(k, k))
    lines += ["Cells: correct/n, with (k✗) = answers graded INCORRECT. Freshness: breaking = event in the last ~7 days, "
              "volatile = can change within weeks, point-in-time twin = asked as of a past date with the date filter on.", ""]

    # linkup-native: which depth the agent chose, by question type (reporting only)
    for a in [a for a in arms if meta["arms"].get(a, {}).get("native")]:
        recs = [A[(i, a)] for i in ids if (i, a) in A]
        depths = ["fast", "standard", "deep"]
        lines += [f"## {a}: depth chosen per search, by question type", "",
                  "| Question type | " + " | ".join(depths) + " | from_date set | domains prioritised |", "|---|" + "---|" * (len(depths) + 2)]
        for pat in PATTERNS:
            cs = [c for r in recs if r["pattern"] == pat for c in r["search_calls"]]
            if cs:
                lines.append(f"| {PATTERNS[pat]} | " + " | ".join(str(sum(c.get("depth") == d for c in cs)) for d in depths) +
                             f" | {sum(bool(c['params'].get('from_date')) for c in cs)} | {sum(bool(c['params'].get('prioritize')) for c in cs)} |")
        lines.append("")

    # per question
    mark = {"CORRECT": "✅", "INCORRECT": "❌", "NOT_ATTEMPTED": "➖", "ERROR": "⚠️"}
    lines += ["## Per question", "", "✅ correct · ❌ incorrect · ➖ not attempted · ⚠️ error"
              + ("" if any(not a.startswith("linkup") for a in arms) else " · no competitor arms in this run, so no win/lose flags"), "", "| ID | Team | Pattern | Trap | " + " | ".join(arms) + " | Linkup only? |",
              "|---|---|---|---|" + "---|" * len(arms) + "---|"]
    competitors = [a for a in arms if not a.startswith("linkup")]
    for i in ids:
        r = rows_by_id[i]
        gs = {a: grade(i, a) for a in arms}
        lk = any(gs[a] == "CORRECT" for a in arms if a.startswith("linkup"))
        comp = any(gs[a] == "CORRECT" for a in competitors)
        flag = ("" if not competitors else
                "**Linkup wins**" if lk and not comp else ("**Linkup loses**" if comp and not lk else ""))
        trap = r["trap"] or ("point-in-time" if r.get("point_in_time") else "")
        lines.append(f"| {i} | {r['team']} | {r['pattern']} | {trap} | " +
                     " | ".join(mark.get(gs[a], "—") for a in arms) + f" | {flag} |")
    lines.append("")

    # where Linkup loses: reasons
    losses = []
    for i in ids:
        for a in arms:
            if a.startswith("linkup") and grade(i, a) != "CORRECT":
                if any(grade(i, c) == "CORRECT" for c in arms if not c.startswith("linkup")):
                    j = J.get((i, a)) or {}
                    losses.append(f"- **{i}** ({a}): {j.get('reason', '')} Missing: {', '.join(j.get('missing_facts', []) or ['—'])}")
    if losses:
        lines += ["## Where Linkup loses (a competitor got it right)", "",
                  "Root-cause each one (retrieval miss, stale index, wrong entity, LLM synthesis) and send it to Linkup engineering.", "", *losses, ""]

    flags = [f"- {r['id']} / {r['arm']}: fallback model answered" for r in agent_recs if r.get("fallback_ran")]
    unsup = sorted({(r["arm"], f) for r in agent_recs for c in r["search_calls"] for f in c.get("unsupported", [])})
    if flags or unsup:
        lines += ["## Caveats", ""] + flags + [f"- {a}: `{f}` not supported, so the filter wasn't applied (capability gap)" for a, f in unsup] + [""]
    return "\n".join(lines)


def usable_backend(meta, arm):
    return (meta["arms"].get(arm) or {}).get("backend")


def call_fee(call, backend_name):
    """Fee recorded at call time; for runs logged before fees were recorded, recompute Linkup's from the request."""
    if call.get("fee_usd") is not None:
        return call["fee_usd"]
    if call.get("request") and backend_name in ("linkup", "perplexity", "parallel"):
        from search_backends import BACKENDS
        return BACKENDS[backend_name]().fee_usd(call["request"])
    return None


# ─────────────────────────────── human review ───────────────────────────────
REVIEW_COLS = ["why_selected", "id", "arm", "team", "pattern", "trap", "as_of", "query", "gold_answer", "required_facts",
               "agent_answer", "cited_urls", "judge_grade", "judge_reason", "judge_missing_facts",
               "human_grade", "human_note"]


def write_review_csv(run_dir, rows_by_id, recs, judgments, n_random=20, seed=20261123):
    """EVAL_DESIGN §3 audit: every question where arms disagree, plus 20 random other judgments."""
    import csv
    import random
    J = {(j["id"], j["arm"]): j for j in judgments}
    by_id = {}
    for r in recs:
        by_id.setdefault(r["id"], []).append(r)
    disagree = {i for i, rs in by_id.items() if len({(J.get((r["id"], r["arm"])) or {}).get("grade") for r in rs}) > 1}
    picked = [(r, "arms disagree on this question") for r in recs if r["id"] in disagree]
    rest = [r for r in recs if r["id"] not in disagree]
    random.Random(seed).shuffle(rest)
    picked += [(r, "random sample") for r in rest[:n_random]]
    path = run_dir / "human_review.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=REVIEW_COLS)
        w.writeheader()
        for r, why in sorted(picked, key=lambda x: (x[0]["id"], x[0]["arm"])):
            g, j = rows_by_id[r["id"]], J.get((r["id"], r["arm"])) or {}
            w.writerow({"why_selected": why, "id": r["id"], "arm": r["arm"], "team": g["team"], "pattern": g["pattern"],
                        "trap": g["trap"] or ("point-in-time" if g.get("point_in_time") else ""), "as_of": r["today"],
                        "query": g["query"], "gold_answer": g["gold_answer"], "required_facts": " | ".join(g["required_facts"]),
                        "agent_answer": r["answer"] or f"(no answer: {r['error']})", "cited_urls": " | ".join(r["citations"]),
                        "judge_grade": j.get("grade", ""), "judge_reason": j.get("reason", ""),
                        "judge_missing_facts": " | ".join(j.get("missing_facts") or []), "human_grade": "", "human_note": ""})
    return path, len(picked), len(disagree)


def audit(run_dir):
    """Compare filled-in human_grade against the judge (EVAL_DESIGN §3: > 2 disagreements -> fix rubric, regrade)."""
    import csv
    path = run_dir / "human_review.csv"
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    norm = {"CORRECT": "CORRECT", "C": "CORRECT", "INCORRECT": "INCORRECT", "I": "INCORRECT", "WRONG": "INCORRECT",
            "NOT_ATTEMPTED": "NOT_ATTEMPTED", "NOT ATTEMPTED": "NOT_ATTEMPTED", "NA": "NOT_ATTEMPTED", "N": "NOT_ATTEMPTED"}
    done = [r for r in rows if r["human_grade"].strip()]
    bad = [r for r in done if norm.get(r["human_grade"].strip().upper()) is None]
    if bad:
        print("Unrecognised human_grade values (use CORRECT / INCORRECT / NOT_ATTEMPTED):",
              ", ".join(f"{r['id']}/{r['arm']}={r['human_grade']!r}" for r in bad))
    graded = [r for r in done if r not in bad]
    dis = [r for r in graded if norm[r["human_grade"].strip().upper()] != r["judge_grade"]]
    print(f"Human-reviewed: {len(graded)}/{len(rows)}. Agree with judge: {len(graded) - len(dis)}. Disagree: {len(dis)}.")
    for r in dis:
        print(f"  {r['id']:12} {r['arm']:16} judge={r['judge_grade']:13} human={r['human_grade'].strip().upper():13} {r['human_note']}")
    if len(dis) > 2:
        print("More than 2 disagreements: fix the grader rules (scripts/simpleqa_grader.py), then --rejudge this run.")
    elif graded:
        print("Judge accepted (2 or fewer disagreements).")
    return 0


# ─────────────────────────────── main ───────────────────────────────
GOLD_FILES = {"bench1": ROOT / "gold" / "gold_set.jsonl",            # fund queries written for this eval
              "bench2": ROOT / "gold" / "bench2" / "bench2_set.jsonl"}  # public benchmarks + 8-K exec changes


def load_rows(split, ids, run_date, include_expired, gold="bench1"):
    rows = [json.loads(l) for l in open(GOLD_FILES[gold], encoding="utf-8") if l.strip()]
    if ids:
        rows = [r for r in rows if r["id"] in ids]
    elif split != "all":
        rows = [r for r in rows if r["split"] == split]
    keep, expired = [], []
    for r in rows:
        if r["expires_at"] and r["expires_at"] < run_date and not include_expired:
            expired.append(r["id"])
            continue
        r["_today"] = r["point_in_time"] or run_date
        keep.append(r)
    return keep, expired


def append_jsonl(path, obj, lock):
    with lock, open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, default=str) + "\n")


def read_jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()] if path.exists() else []


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", default="dev", choices=["dev", "test", "all"])
    ap.add_argument("--ids", nargs="*", help="run only these gold ids")
    ap.add_argument("--arms", nargs="*", help=f"subset of arms (default: all with keys); with --resume, arms to ADD to that run. "
                    f"Known: {', '.join(ARMS)}, linkup-native, linkup-tuned")
    ap.add_argument("--tuned", help="JSON config for the linkup-tuned arm (see configs/linkup_tuned.json)")
    ap.add_argument("--run-date", default=dt.date.today().isoformat(), help="the agent's 'today' for normal rows")
    ap.add_argument("--no-date-filter", action="store_true", help="point-in-time rows: prompt date only, no upper date bound")
    ap.add_argument("--pit-query", default="all", choices=PIT_QUERY_MODES,
                    help="point-in-time rows: add the as-of date to the search query text for all arms (default), only for backends with no upper date bound (Parallel), or off")
    ap.add_argument("--include-expired", action="store_true", help="run rows past expires_at (re-verify them first!)")
    ap.add_argument("--agent-effort", default="medium", choices=["low", "medium", "high", "xhigh", "max"])
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--resume", help="existing run dir: skip (id, arm) pairs already done")
    ap.add_argument("--rejudge", help="existing run dir: re-grade saved answers and rebuild the scorecard")
    ap.add_argument("--audit", help="existing run dir: compare human_review.csv grades with the judge")
    ap.add_argument("--report", help="existing run dir: rebuild scorecard.md and human_review.csv only (no API calls)")
    ap.add_argument("--ping", action="store_true", help="one test search per backend, no LLM calls")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    load_env(ROOT / ".env")
    if args.audit:
        return audit(pathlib.Path(args.audit))
    if args.report:
        run_dir = pathlib.Path(args.report)
        meta = json.loads((run_dir / "meta.json").read_text())
        rows, _ = load_rows("all", None, meta["run_date"], True)
        rows_by_id = {r["id"]: r for r in rows}
        recs, judgments = read_jsonl(run_dir / "agent.jsonl"), read_jsonl(run_dir / "judgments.jsonl")
        (run_dir / "scorecard.md").write_text(scorecard(rows_by_id, recs, judgments, list(meta["arms"]), meta), encoding="utf-8")
        rpath, n_rev, n_dis = write_review_csv(run_dir, rows_by_id, recs, judgments)
        print(f"Rebuilt {run_dir / 'scorecard.md'} and {rpath} ({n_rev} answers for review)")
        return 0

    # The agent writes its own queries here, so the pre-rewritten-query arm only exists in retrieval_run.py.
    arms = {a: c for a, c in ARMS.items() if not c.get("rewrite")}
    if NATIVE_CONFIG.exists():
        arms["linkup-native"] = {"backend": "linkup", "native": True, **json.loads(NATIVE_CONFIG.read_text())}
    if args.tuned:
        arms["linkup-tuned"] = {"backend": "linkup", **json.loads(pathlib.Path(args.tuned).read_text())}
    if args.arms:
        unknown = set(args.arms) - set(arms)
        if unknown:
            sys.exit(f"unknown arms: {unknown}")
        arms = {a: arms[a] for a in args.arms}

    if args.ping:
        for name, cls in BACKENDS.items():
            b = cls()
            if not b.available:
                print(f"{name:11} SKIP  (no {cls.key_env} in .env)")
                continue
            try:
                out = b.search("Federal Reserve FOMC statement October 2026", k=3)
                r0 = out["results"][0] if out["results"] else {}
                print(f"{name:11} OK    {out['latency_ms']} ms, {len(out['results'])} results; first: {r0.get('title')!r} "
                      f"({r0.get('url')}), published_date={r0.get('published_date')}")
            except SearchError as e:
                print(f"{name:11} FAIL  {e}")
        return 0

    have_llm = bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))
    if args.resume or args.rejudge:
        prev = json.loads((pathlib.Path(args.resume or args.rejudge) / "meta.json").read_text())
        arms = {**prev["arms"], **({a: c for a, c in arms.items() if a not in prev["arms"]} if args.resume and args.arms else {})}
    usable = {}
    for a, cfg in arms.items():
        if args.rejudge or BACKENDS[cfg["backend"]]().available:
            usable[a] = cfg
        else:
            print(f"WARN  skipping arm {a}: no {BACKENDS[cfg['backend']].key_env} in .env")
    if not usable:
        sys.exit("No search API keys found. Copy .env.example to .env and add at least one.")

    if args.rejudge:
        run_dir = pathlib.Path(args.rejudge)
        meta = json.loads((run_dir / "meta.json").read_text())
        rows, _ = load_rows("all", None, meta["run_date"], True)
    elif args.resume:
        run_dir = pathlib.Path(args.resume)
        meta = json.loads((run_dir / "meta.json").read_text())
        rows, expired = load_rows(meta["split"], meta.get("ids"), meta["run_date"], meta["include_expired"])
        meta["arms"] = {**meta["arms"], **usable}
        args.pit_query = meta.get("pit_query", "off")  # added arms must match how the run started (older runs: off)
    else:
        rows, expired = load_rows(args.split, args.ids, args.run_date, args.include_expired)
        run_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{args.split}" + ("-nofilter" if args.no_date_filter else "")
        run_dir = ROOT / "runs" / run_id
        meta = {"run_id": run_id, "split": args.split, "ids": args.ids, "run_date": args.run_date,
                "date_filter": not args.no_date_filter, "pit_query": args.pit_query, "include_expired": args.include_expired,
                "agent_model": AGENT_MODEL, "agent_effort": args.agent_effort, "judge_model": JUDGE_MODEL,
                "arms": usable, "max_search_calls": MAX_SEARCH_CALLS, "top_k": TOP_K}
    rows_by_id = {r["id"]: r for r in rows}

    if not args.rejudge:
        if expired:
            print(f"WARN  skipped {len(expired)} expired rows (re-verify, or pass --include-expired): {', '.join(expired)}")
        jobs = [(r, a) for r in rows for a in usable]  # row-major: arms interleave, as the design requires
        print(f"Plan: {len(rows)} rows x {len(usable)} arms = {len(jobs)} agent runs + {len(jobs)} judge calls "
              f"(split={meta['split']}, run date {meta['run_date']}).")
        if args.dry_run:
            for a, cfg in usable.items():
                print(f"  arm {a}: {cfg}")
            return 0
        if not have_llm:
            sys.exit("No ANTHROPIC_API_KEY in .env.")
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "meta.json").write_text(json.dumps(meta, indent=2))
        # Latest record per (id, arm) wins, as in the scorecard. A pair whose latest attempt errored
        # (API credit, network, rate limit) is retried on --resume instead of counted as done.
        latest = {(r["id"], r["arm"]): r for r in read_jsonl(run_dir / "agent.jsonl")}
        done = {k for k, r in latest.items() if not r.get("error")}
        if args.resume and len(latest) > len(done):
            print(f"Retrying {len(latest) - len(done)} (id, arm) pairs whose last attempt errored.")
        # A pair with a good answer but a failed grading call (latest judgment ERROR) is re-graded only:
        # the answer is kept, so the agent isn't re-run and the arm doesn't get a second try.
        latest_j = {(j["id"], j["arm"]): j for j in read_jsonl(run_dir / "judgments.jsonl")}
        regrade = {k for k in done if latest_j.get(k, {}).get("grade") == "ERROR"} if args.resume else set()
        if regrade:
            print(f"Re-grading {len(regrade)} answered pairs whose grading call errored.")
        jobs = [(r, a) for r, a in jobs if (r["id"], a) not in done or (r["id"], a) in regrade]

        client = make_client()
        lock = threading.Lock()

        def work(job):
            row, arm = job
            if (row["id"], arm) in regrade:
                rec = latest[(row["id"], arm)]
            else:
                cfg = usable[arm]
                backend = BACKENDS[cfg["backend"]](**{k: v for k, v in cfg.items() if k == "depth"})
                rec = run_agent(client, row, arm, cfg, backend, args)
                append_jsonl(run_dir / "agent.jsonl", rec, lock)
            j = judge(client, row, rec)
            j.update(id=row["id"], arm=arm)
            append_jsonl(run_dir / "judgments.jsonl", j, lock)
            return row["id"], arm, j["grade"]

        with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
            for n, fut in enumerate(cf.as_completed([ex.submit(work, j) for j in jobs]), 1):
                i, a, g = fut.result()
                print(f"[{n}/{len(jobs)}] {i:12} {a:16} {g}")
    else:
        client = make_client()
        recs = read_jsonl(run_dir / "agent.jsonl")
        judged = []
        for n, rec in enumerate(recs, 1):
            j = judge(client, rows_by_id[rec["id"]], rec)
            j.update(id=rec["id"], arm=rec["arm"])
            judged.append(j)
            print(f"[{n}/{len(recs)}] {rec['id']:12} {rec['arm']:16} {j['grade']}")
        old = run_dir / "judgments.jsonl"
        if old.exists():
            old.rename(run_dir / f"judgments.{int(time.time())}.bak.jsonl")
        for j in judged:
            append_jsonl(old, j, threading.Lock())

    recs = read_jsonl(run_dir / "agent.jsonl")
    judgments = read_jsonl(run_dir / "judgments.jsonl")
    md = scorecard(rows_by_id, recs, judgments, [a for a in meta["arms"]], meta)
    (run_dir / "scorecard.md").write_text(md, encoding="utf-8")
    rpath, n_rev, n_dis = write_review_csv(run_dir, rows_by_id, recs, judgments)
    print(f"\nScorecard: {run_dir / 'scorecard.md'}")
    print(f"Human review sheet: {rpath} ({n_rev} answers: {n_dis} questions where arms disagree + random sample). "
          f"Fill in human_grade, then run --audit {run_dir}\n")
    print(md.split("## By team")[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())

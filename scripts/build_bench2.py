#!/usr/bin/env python3
"""Build benchmark 2 (gold/bench2/bench2_set.jsonl): fund-relevant slices of public benchmarks, plus 8-K executive changes.

    python scripts/build_bench2.py
    python scripts/validate_gold.py gold/bench2/bench2_set.jsonl --csv gold/bench2/bench2_set.csv

Slices (sources and licences in gold/bench2/sources/README.md):
  INV-FSC2-*  FinSearchComp T2 (global): single figures from filings, macro and market data. 28 company + 12 macro rows.
  INV-FSC3-*  FinSearchComp T3 (global): only the multi-step questions built on company filings (no price/volume/FX).
  INV-FUND-*  Linkup GTM funding set: private-company total funding, scored within ±25% of Crunchbase (July 2026).
  *-EXEC-*    8-K Item 5.02 executive changes (Oct 12 - Nov 20, 2026), gold from the filing.

Every row is split=test (nothing here was used for tuning). `research: true` marks the rows where the research arms
also run: the finance rows (FinSearchComp, funding) and multi-hop rows. Sampling is seeded, so the file is reproducible.
"""
from __future__ import annotations

import csv
import json
import pathlib
import random
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "gold" / "bench2" / "sources"
OUT = ROOT / "gold" / "bench2" / "bench2_set.jsonl"
SEED = 20261124
FSC_URL = "https://huggingface.co/datasets/ByteSeedXpert/FinSearchComp"
FUND_URL = "https://github.com/LinkupPlatform/Search-Benchmarks-on-GTM-Usecases/tree/main/company/research-evals/funding-retrieval"
FUND_SNAPSHOT = "2026-07-10"  # commit date of golden_set.csv; Crunchbase values are from on or before this date
RUN_AS_OF = "2026-11-24"

N_T2_COMPANY, N_T2_MACRO, N_FUND = 28, 12, 30

# T2 rows are "company" when they ask for a financial-statement line of one company; everything else (macro
# statistics, commodity and index prices, rates, institutions such as the IMF) is "macro".
STATEMENT_RE = re.compile(r"expenses|cost of sales|total assets|ending cash|prepaid|long-term debt|short-term debt|stockholders|"
                          r"financing activities|investing activities|operating activities|property and equipment|"
                          r"cash and cash equivalents|before income taxes|inventories|contribution profit|stores|gross profit|"
                          r"operating income|accounts receivable|total liabilities of [A-Z]|revenue|net income|net loss|"
                          r"total costs|equity of|deficit of|deferred rent|paid-in capital|accrued|shareholder equity|preferred stock", re.I)
NOT_COMPANY_RE = re.compile(r"IMF|commercial banks|GDP|in the United States \(|government", re.I)
# T3 rows built on company filings (statements, ratios over fiscal years). Everything else in T3 is market-data work
# (prices, volumes, turnover, FX, index constituents) that a fund gets from its terminal, not from web search.
T3_FILINGS = re.compile(r"fiscal year|annual report|total assets|goodwill|gross (profit )?margin|net income|inventory turnover|"
                        r"liability|debt-to-asset|net profit margin|depreciation|international markets|chemicals sales|"
                        r"financing activities|return on invested capital", re.I)
T3_MARKET = re.compile(r"stock price|trading volume|trading value|closing price|market capitali[sz]ation|turnover rate|"
                       r"exchange rate|central parity|weekly|P/E|PE-TTM|Price-to-Earnings|constituent", re.I)


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def tolerance_note(answer):
    a = answer.lower()
    if "range" in a or "between" in a or "within" in a:
        return "Gold states an accepted range: any value inside it is CORRECT."
    m = re.search(r"(marginal|margin) (of )?error of ([\d.]+%?)", a)
    if m:
        return f"Gold allows a margin of error of {m.group(3)}; values within it are CORRECT."
    return ("Rounding errors are allowed: a value that matches the gold at the gold's stated precision, or differs only by "
            "rounding (about ±0.5% relative), is CORRECT. Unit conversions (millions vs thousands) are fine if the value is equal.")


def fsc_rows():
    t2 = list(csv.DictReader(open(SRC / "finsearchcomp_t2_global.csv", encoding="utf-8")))
    t3 = list(csv.DictReader(open(SRC / "finsearchcomp_t3_global.csv", encoding="utf-8")))
    company = [x for x in t2 if STATEMENT_RE.search(x["problem"]) and not NOT_COMPANY_RE.search(x["problem"])]
    macro = [x for x in t2 if x not in company]
    rng = random.Random(SEED)
    pick2 = [("company", x) for x in rng.sample(company, N_T2_COMPANY)] + [("macro", x) for x in rng.sample(macro, N_T2_MACRO)]
    rows = []
    for n, (kind, x) in enumerate(pick2, 1):
        ans = norm(x["answer"])
        rows.append(dict(
            id=f"INV-FSC2-{n:02d}", sub_team="credit" if kind == "company" else "macro",
            persona_role="credit analyst" if kind == "company" else "macro analyst", pattern="P2",
            query=norm(x["problem"]), intent_note="Single historical figure from a primary source (filing or official statistics).",
            answer_type="number", gold_answer=ans, required_facts=[ans], acceptable_variants=[],
            gold_sources=[FSC_URL], authoritative_domains=["sec.gov"] if kind == "company" else [],
            as_of="2026-05-08", freshness="static", expires_at=None, hops=1, difficulty="med", trap=None,
            verified_by="FinSearchComp analyst team (ByteDance Seed), via LinkupPlatform/linkup-finance-benchmark",
            verification_notes=tolerance_note(ans) + " Gold is verified against primary sources by the FinSearchComp authors.",
            origin="human", source_benchmark="finsearchcomp-t2", source_id=x["id"]))
    seen, pick3 = set(), []
    for x in t3:
        p = norm(x["problem"])
        if T3_FILINGS.search(p) and not T3_MARKET.search(p) and p.lower() not in seen:
            seen.add(p.lower())
            pick3.append(x)
    for n, x in enumerate(pick3, 1):
        ans = norm(x["answer"])
        rows.append(dict(
            id=f"INV-FSC3-{n:02d}", sub_team="credit", persona_role="credit analyst", pattern="P4",
            query=norm(x["problem"]), intent_note="Multi-step: pull figures across filings or years, then compute.",
            answer_type="number", gold_answer=ans, required_facts=[ans], acceptable_variants=[],
            gold_sources=[FSC_URL], authoritative_domains=["sec.gov"],
            as_of="2026-02-06", freshness="static", expires_at=None, hops=2, difficulty="hard", trap=None,
            verified_by="FinSearchComp analyst team (ByteDance Seed), via LinkupPlatform/linkup-finance-benchmark",
            verification_notes=tolerance_note(ans) + " Multi-part answers need every part.",
            origin="human", source_benchmark="finsearchcomp-t3", source_id=x["id"]))
    return rows


def money(s):
    m = re.match(r"\$([\d.]+)([MB])", s.strip())
    return float(m.group(1)) * (1e3 if m.group(2) == "B" else 1) if m else None  # in $M


def fmt(v):
    return f"${v / 1e3:.2f}B" if v >= 1e3 else f"${v:.1f}M"


def funding_rows():
    gs = [x for x in csv.DictReader(open(SRC / "linkup_gtm_funding_golden_set.csv", encoding="utf-8")) if money(x["golden"])]
    rows = []
    for n, x in enumerate(random.Random(SEED).sample(gs, N_FUND), 1):
        g = money(x["golden"])
        lo, hi = g * 0.75, g * 1.25
        year = x["founded"][:4]
        rows.append(dict(
            id=f"INV-FUND-{n:02d}", sub_team="private_markets", persona_role="private markets associate", pattern="P3",
            query=f"{x['company']} ({x['hq']}, founded {year}) — how much total funding has it raised to date?",
            intent_note="Total equity raised across all rounds, for a sourcing screen. Needs reconciling several rounds.",
            answer_type="number", gold_answer=f"{x['golden']} total funding (Crunchbase, as of {FUND_SNAPSHOT})",
            required_facts=[f"total funding of about {x['golden']} (accept {fmt(lo)} to {fmt(hi)})"], acceptable_variants=[],
            gold_sources=[FUND_URL, "https://www.crunchbase.com/"], authoritative_domains=["crunchbase.com"],
            as_of=FUND_SNAPSHOT, freshness="volatile", expires_at="2027-01-10", hops=2, difficulty="med", trap=None,
            verified_by="Crunchbase total equity funding, via LinkupPlatform/Search-Benchmarks-on-GTM-Usecases",
            verification_notes=(f"Scoring rule from the source benchmark: CORRECT if the stated total is within ±25% of "
                                f"{x['golden']} ({fmt(lo)} to {fmt(hi)}). A single round reported as the total, or a total outside "
                                f"the band, is INCORRECT. The gold is a Crunchbase snapshot from {FUND_SNAPSHOT}: if a higher "
                                f"total is explained by a round the answer dates after {FUND_SNAPSHOT}, grade CORRECT and note it. "
                                f"Valuation is not graded. Wrong company (same name, different HQ) is INCORRECT."),
            origin="human", source_benchmark="linkup-gtm-funding", source_id=x["num"]))
    return rows


def exec_rows():
    d = json.loads((SRC / "edgar_8k_exec_changes.json").read_text())
    rows = []
    for n, e in enumerate(d["events"], 1):
        prefix = "LRC" if e["team"] == "legal_rc" else "INV"
        rows.append(dict(
            id=f"{prefix}-EXEC-{n:02d}", sub_team=e["sub_team"],
            persona_role="credit analyst" if e["team"] == "invest" else "in-house counsel", pattern="P1",
            query=e["query"], intent_note=f"Current {e['role']} of {e['company']} ({e['ticker']}) after a recent change; needs the person and the timing.",
            answer_type="fact", gold_answer=e["gold_answer"], required_facts=e["required_facts"],
            acceptable_variants=e["acceptable_variants"], gold_sources=[e["source"]], authoritative_domains=["sec.gov"],
            as_of=RUN_AS_OF, freshness="breaking", expires_at=e["expires_at"], hops=1, difficulty="med", trap=e["trap"],
            verified_by="claude-research",
            verification_notes=f"Source: SEC 8-K Item 5.02 ({e['company']}). Filing quote: \"{e['quote']}\". {e['notes'] if e['notes'] != '(none)' else ''}".strip(),
            origin="claude", source_benchmark="edgar-8k-exec", source_id=e["key"]))
    return rows


def main():
    rows = fsc_rows() + funding_rows() + exec_rows()
    for r in rows:
        r.update(split="test", team=r.get("team") or ("legal_rc" if r["id"].startswith("LRC") else "invest"),
                 point_in_time=None, workflow=None,
                 research=r["source_benchmark"] in {"finsearchcomp-t2", "finsearchcomp-t3", "linkup-gtm-funding"} or r["hops"] >= 2)
    order = ["id", "split", "team", "sub_team", "persona_role", "pattern", "query", "intent_note", "answer_type", "gold_answer",
             "required_facts", "acceptable_variants", "gold_sources", "authoritative_domains", "as_of", "freshness", "expires_at",
             "hops", "difficulty", "trap", "verified_by", "verification_notes", "origin", "point_in_time", "workflow",
             "research", "source_benchmark", "source_id"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({k: r[k] for k in order}, ensure_ascii=False) + "\n")
    by = {}
    for r in rows:
        by[r["source_benchmark"]] = by.get(r["source_benchmark"], 0) + 1
    print(f"Wrote {len(rows)} rows to {OUT}: {by}; research rows: {sum(r['research'] for r in rows)}")


if __name__ == "__main__":
    main()

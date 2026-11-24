#!/usr/bin/env python3
"""Validate the gold set and print its distribution.

Usage:
    python scripts/validate_gold.py gold/gold_set.jsonl [--csv gold/gold_set.csv] [--today YYYY-MM-DD]

Exit code 1 if any hard error (schema, enum, keep-gate, duplicate id).
Expired rows and missed mix targets are reported as warnings.
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import json
import re
import sys
import unicodedata

ENUMS = {
    "split": {"dev", "test"},
    "team": {"tech", "legal_rc", "tax_hr", "invest"},
    "pattern": {"P1", "P2", "P3", "P4", "P5"},
    "answer_type": {"fact", "number", "date", "list", "status", "refusal"},
    "freshness": {"static", "slow", "volatile", "breaking"},
    "difficulty": {"easy", "med", "hard"},
    "trap": {None, "stale", "ambiguous", "paywall", "nonexistent", "contested", "premium"},
    "origin": {"claude", "human"},
    "workflow": {None, "sourcing_signal", "crm_enrichment", "news_briefing"},
}
REQUIRED = [
    "id", "split", "team", "sub_team", "persona_role", "pattern", "query",
    "intent_note", "answer_type", "gold_answer", "required_facts",
    "acceptable_variants", "gold_sources", "authoritative_domains", "as_of",
    "freshness", "expires_at", "hops", "difficulty", "trap", "verified_by",
    "verification_notes", "origin", "point_in_time", "workflow",
]
LIST_FIELDS = {"required_facts", "acceptable_variants", "gold_sources", "authoritative_domains"}
ID_PREFIX = {"tech": "TECH", "legal_rc": "LRC", "tax_hr": "TAX", "invest": "INV"}
EXPIRY_DAYS = {"static": None, "slow": 180, "volatile": 30, "breaking": 7}
OFFICIAL_RE = re.compile(r"(\.gov$|\.gov\.|europa\.eu$|uscourts|courtlistener|finra\.org$|"
                         r"federalreserve|nist\.gov|cve\.org|bls\.gov|treasury|irs\.gov|ny\.gov)")
MIN_KEEPGATE_LEN = 4  # don't keep-gate on tiny tokens like "Yes" or "2"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).lower()
    return re.sub(r"[^a-z0-9$%.]+", " ", s).strip()


def parse_date(s):
    return dt.date.fromisoformat(s) if s else None


def validate(rows, today):
    errors, warnings = [], []
    seen = set()
    for i, r in enumerate(rows, 1):
        rid = r.get("id", f"<line {i}>")
        missing = [f for f in REQUIRED if f not in r]
        if missing:
            errors.append(f"{rid}: missing fields {missing}")
            continue
        if rid in seen:
            errors.append(f"{rid}: duplicate id")
        seen.add(rid)
        for f, allowed in ENUMS.items():
            if r[f] not in allowed:
                errors.append(f"{rid}: {f}={r[f]!r} not in {sorted(map(str, allowed))}")
        for f in LIST_FIELDS:
            if not isinstance(r[f], list):
                errors.append(f"{rid}: {f} must be a list")
        if not r["required_facts"]:
            errors.append(f"{rid}: required_facts is empty")
        if not r["gold_sources"]:
            errors.append(f"{rid}: gold_sources is empty")
        if not all(str(u).startswith("http") for u in r["gold_sources"]):
            errors.append(f"{rid}: gold_sources must be URLs")
        if not isinstance(r["hops"], int) or r["hops"] < 1:
            errors.append(f"{rid}: hops must be int >= 1")
        prefix = ID_PREFIX.get(r["team"])
        if prefix and not rid.startswith(prefix + "-"):
            errors.append(f"{rid}: id prefix should be {prefix}- for team {r['team']}")
        # dates
        try:
            as_of = parse_date(r["as_of"])
            exp = parse_date(r["expires_at"])
        except ValueError as e:
            errors.append(f"{rid}: bad date ({e})")
            continue
        if r["freshness"] == "static" and exp is not None:
            warnings.append(f"{rid}: static row has expires_at")
        if r["freshness"] != "static" and exp is None:
            errors.append(f"{rid}: {r['freshness']} row needs expires_at")
        if exp and exp < today:
            warnings.append(f"{rid}: EXPIRED on {exp} — re-verify before running")
        if as_of and as_of > today:
            errors.append(f"{rid}: as_of in the future")
        if r["point_in_time"] is not None:
            try:
                pit = parse_date(r["point_in_time"])
            except ValueError as e:
                errors.append(f"{rid}: bad point_in_time ({e})")
            else:
                if as_of and pit >= as_of:
                    errors.append(f"{rid}: point_in_time must be before as_of")
                if r["freshness"] != "static":
                    warnings.append(f"{rid}: point-in-time row should be static (a past state doesn't change)")
        if r["trap"] == "contested" and len(r["required_facts"]) < 2:
            errors.append(f"{rid}: contested row must require at least two sides in required_facts")
        # keep-gate: query must not contain the answer
        q = norm(r["query"])
        for cand in [r["gold_answer"], *r["acceptable_variants"]]:
            c = norm(str(cand))
            if len(c) >= MIN_KEEPGATE_LEN and re.search(rf"(^| ){re.escape(c)}( |$)", q):
                errors.append(f"{rid}: KEEP-GATE — query contains answer {cand!r}")
        if r["origin"] == "human":
            if r["verified_by"] in {"", "claude-research"}:
                errors.append(f"{rid}: human-researched row must name a human in verified_by")
            if r["split"] != "test":
                errors.append(f"{rid}: human-researched hard rows must be split=test")
        if r["answer_type"] == "refusal" and r["trap"] != "nonexistent":
            warnings.append(f"{rid}: refusal answer without trap=nonexistent")
    return errors, warnings


def crosstab(rows, a, b):
    keys_b = sorted({str(r[b]) for r in rows})
    table = collections.defaultdict(collections.Counter)
    for r in rows:
        table[str(r[a])][str(r[b])] += 1
    label = f"{a} x {b}"
    w = max(len(label), *(len(k) for k in table))
    out = [f"{label:<{w}} " +" ".join(f"{k:>9}" for k in keys_b) + f" {'total':>7}"]
    for ka in sorted(table):
        row = table[ka]
        out.append(f"{ka:<{w}} " + " ".join(f"{row[k]:>9}" for k in keys_b) + f" {sum(row.values()):>7}")
    return "\n".join(out)


def mix_checks(rows):
    n = len(rows)
    fresh = sum(r["freshness"] in {"volatile", "breaking"} for r in rows)
    official = sum(r["pattern"] == "P2" or any(OFFICIAL_RE.search(d) for d in r["authoritative_domains"])
                   for r in rows)
    multihop = sum(r["hops"] >= 2 for r in rows)
    traps = sum(r["trap"] in {"stale", "ambiguous", "paywall", "nonexistent"} for r in rows)
    contested = sum(r["trap"] == "contested" for r in rows)
    pit = sum(r["point_in_time"] is not None for r in rows)
    dev = sum(r["split"] == "dev" for r in rows)
    checks = [
        ("rows in 50..100", 50 <= n <= 100, n),
        ("volatile+breaking >= 30%", fresh / n >= 0.30, f"{fresh}/{n} = {fresh / n:.0%}"),
        ("official-source >= 30%", official / n >= 0.30, f"{official}/{n} = {official / n:.0%}"),
        ("multi-hop ~25% (>=18%)", multihop / n >= 0.18, f"{multihop}/{n} = {multihop / n:.0%}"),
        ("classic traps (stale/ambiguous/paywall/nonexistent) 8..16", 8 <= traps <= 16, traps),
        ("contested rows >= 4", contested >= 4, contested),
        ("point-in-time twins >= 6", pit >= 6, pit),
        ("dev rows 12..20", 12 <= dev <= 20, dev),
        ("teams >= 3", len({r['team'] for r in rows}) >= 3, len({r['team'] for r in rows})),
    ]
    return checks


def export_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=REQUIRED)
        w.writeheader()
        for r in rows:
            w.writerow({k: (" | ".join(map(str, r[k])) if isinstance(r[k], list) else r[k]) for k in REQUIRED})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--csv")
    ap.add_argument("--today", default=dt.date.today().isoformat())
    args = ap.parse_args()
    today = dt.date.fromisoformat(args.today)

    rows = []
    with open(args.path, encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"ERROR line {ln}: invalid JSON ({e})")
                    return 1

    errors, warnings = validate(rows, today)
    print(f"Rows: {len(rows)}  (today={today})\n")
    if not errors:
        for a, b in [("team", "pattern"), ("team", "freshness"), ("team", "split"), ("team", "trap"), ("team", "origin")]:
            print(crosstab(rows, a, b), "\n")
        print("Mix targets:")
        for name, ok, val in mix_checks(rows):
            print(f"  [{'OK' if ok else 'MISS'}] {name}: {val}")
            if not ok:
                warnings.append(f"mix target missed: {name} ({val})")
        print()
    for w_ in warnings:
        print("WARN ", w_)
    for e in errors:
        print("ERROR", e)
    if args.csv and not errors:
        export_csv(rows, args.csv)
        print(f"\nWrote {args.csv}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

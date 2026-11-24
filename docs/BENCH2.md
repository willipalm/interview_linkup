# Benchmark 2: public benchmarks + 8-K executive changes

Benchmark 1 (`gold/gold_set.jsonl`) is 98 questions written for this fund. Benchmark 2 (`gold/bench2/bench2_set.jsonl`)
tests Linkup's own published strengths on the parts that match the fund's work, in the same harness and grading. It is
reported separately: its own run, its own `scorecard.md` and `research_scorecard.md`.

## What's in it (104 rows, all test split)

| Slice | Rows | Fund team | Gold | Research arms? |
|---|---|---|---|---|
| FinSearchComp T2: one figure from a company filing | 28 | credit, PE | FinSearchComp analysts, verified against filings | yes |
| FinSearchComp T2: macro, rates, commodity, index | 12 | macro | same | yes |
| FinSearchComp T3: multi-year calculations from filings | 14 | credit | same | yes |
| Private-company total funding | 30 | private markets | Crunchbase, July 2026; correct within ±25% | yes |
| 8-K executive changes (CEO, CFO, GC), Oct 12 to Nov 20, 2026 | 20 | credit, legal | the 8-K itself | no |

Sources, licences and what was left out: `gold/bench2/sources/README.md`.

## Arms

Search arms run on every row, one call each, answer written from the results by the blinded Claude Code session:
`linkup-standard`, `linkup-deep`, `linkup-tuned`, `linkup-fast` (Linkup's recommended default), `linkup-rewritten`
(standard depth, query rewritten per Linkup's guidance, dates only in `toDate`), `perplexity`, `parallel`.

Research arms (`configs/research_arms.json`) run only on research rows (the same rows for all three vendors), and the
vendor's own answer is graded:

| Arm | Endpoint | Tier | List price / question |
|---|---|---|---|
| linkup-research | `POST /v1/research` | mode `answer`, reasoningDepth `XL` | $2.50 |
| parallel-research | `POST /v1/tasks/runs` | processor `ultra` | $0.30 |
| perplexity-research | `POST /v1/agent`, background | effort `xhigh` (includes finance_search) | metered; actual cost recorded |

Linkup XL and Parallel ultra are the tiers Linkup used for its published FinSearchComp numbers. They aren't price-matched,
so the research scorecard reports $ / correct. To compare at similar spend, set Parallel to `ultra8x` ($2.40) or Linkup
to `L` ($1.50). Perplexity retired Sonar chat completions on 2026-09-27, so Linkup's own runner (which used `sonar-pro`)
no longer reflects Perplexity's research product.

Research rows in benchmark 1 use the same rule: multi-hop (hops ≥ 2) or an investment-team numeric question, never a
point-in-time row (27 rows).

## Run it

```bash
# 1. Blind query rewrites for linkup-rewritten (fresh Claude Code session; it must not have seen the gold):
.venv/bin/python scripts/retrieval_run.py rewrite-prompts --gold bench2
#    session follows gold/rewrites/bench2_INSTRUCTIONS.md -> gold/rewrites/bench2.jsonl
# 2. Searches + research jobs (research jobs take minutes each; ~$235 list for Linkup+Parallel research, plus Perplexity):
.venv/bin/python scripts/retrieval_run.py run --gold bench2 --tuned configs/linkup_tuned.json --dry-run
.venv/bin/python scripts/retrieval_run.py run --gold bench2 --tuned configs/linkup_tuned.json
# 3-5. Answer, grade-prompts, grade, ingest: same as benchmark 1 (handoff/INSTRUCTIONS.md in the run folder).
```

To add the new arms to the existing benchmark 1 run (keeps its answers and grades; new pairs get new task ids):

```bash
.venv/bin/python scripts/retrieval_run.py rewrite-prompts --gold bench1   # then a fresh session writes gold/rewrites/bench1.jsonl
.venv/bin/python scripts/retrieval_run.py run --resume runs/20261124-144120-all-retrieval \
    --arms linkup-fast linkup-rewritten linkup-research parallel-research perplexity-research
```

## Caveats

- **Vendor-chosen benchmarks.** These come from Linkup's benchmark hub, so they lean towards what Linkup is good at. That's
  the point (testing Linkup's claims), but report benchmark 1 as the fund's own test.
- **Funding gold is a July 2026 snapshot.** Companies keep raising; the grader accepts a higher total only when the answer
  dates the extra round after 2026-07-10.
- **8-K rows go stale fast.** Each has an `expires_at`; EDGAR full-text search covered filings through 2026-11-22, so
  re-check before each run (`validate_gold.py` warns on expired rows).
- **FinSearchComp phrasing is formal** ("answer in millions, rounded to…"), unlike how fund users type. It tests retrieval
  of primary-source figures, not query understanding.
- **linkup-fast on point-in-time rows** gets the same as-of sentence as every arm, but Fast treats it as keywords and adds
  the current date itself; linkup-rewritten is the arm that follows Linkup's date guidance.

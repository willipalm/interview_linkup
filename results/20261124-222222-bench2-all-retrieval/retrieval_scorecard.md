# Retrieval scorecard: 20261124-222222-bench2-all-retrieval

Questions: **bench2** · split: **all** · rows: 104 · one search per question and arm, query as typed · no LLM · as-of date in query text on point-in-time rows: all · run date: 2026-11-24

These metrics need no model. Correctness comes after the Claude Code session answers and grades (see handoff/INSTRUCTIONS.md), in scorecard.md.

| Arm | Errors | Results / q | Evidence in results | Chance match | Gold source in results | Benchmark page returned | Authoritative share of results | Metadata complete | Point-in-time leaks | p50 search ms | Search $ / q (list) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| linkup-standard | 0 | 10.0 | 69/104 | 22 | 4/50 | 0/104 | 3% | 37% | no point-in-time rows | 1597 | 0.005 |
| linkup-deep | 0 | 10.0 | 72/104 | 21 | 15/50 | 0/104 | 8% | 0% | no point-in-time rows | 8149 | 0.050 |
| linkup-tuned | 0 | 10.0 | 71/104 | 22 | 16/50 | 0/104 | 9% | 0% | no point-in-time rows | 7886 | 0.050 |
| linkup-fast | 0 | 10.0 | 70/104 | 23 | 4/50 | 1/104 | 2% | 34% | no point-in-time rows | 1064 | 0.005 |
| linkup-rewritten | 0 | 10.0 | 47/104 | 19 | 33/50 | 0/104 | 16% | 25% | no point-in-time rows | 1826 | 0.005 |
| perplexity | 0 | 8.7 | 73/104 | 29 | 13/50 | 41/104 | 25% | 53% | no point-in-time rows | 405 | 0.005 |
| parallel | 0 | 9.9 | 84/104 | 26 | 15/50 | 2/104 | 18% | 62% | no point-in-time rows | 3766 | 0.005 |

- **Evidence in results**: a required fact or acceptable variant appears word for word in a result's title or content, or, for numeric facts ("rounding errors are allowed", "accept $X to $Y"), the gold number does (±0.5%, any thousand/million scale) or a money amount inside the accepted range does. A rough recall proxy: it misses paraphrases, and on number-heavy pages it can hit by luck.
- **Chance match**: the same check with each question's facts tested against a different question's results (same question type). Read evidence as the gap above this, not the raw count.
- **Benchmark page returned**: questions where the arm returned a page that republishes the source benchmark with its answers (the dataset, a mirror, a published results file). Those results are removed from every other column and from the handoff, so no arm gets credit for finding the answer key.
- **Gold source in results**: a result's domain matches a gold source's domain, over the questions that have a gold source other than the benchmark itself.
- **Point-in-time leaks**: results whose publish date is after the row's cutoff. Results with no date can't be checked, and pages rewritten after publication keep their old date, so this is a lower bound.

## Research jobs (research rows only)

| Arm | Jobs | Errors | p50 minutes | Sources / answer | $ total | $ / job |
|---|---|---|---|---|---|---|
| linkup-research | 84 | 41 | 1.6 | 15.4 | 107.50 | 2.500 |
| parallel-research | 84 | 52 | 0.4 | 1.5 | 9.60 | 0.300 |
| perplexity-research | 84 | 84 | — | 0.0 | 0.00 | 0.000 |

## Evidence in results, by team

Chance match in brackets where it is above zero.

| Slice | linkup-standard | linkup-deep | linkup-tuned | linkup-fast | linkup-rewritten | perplexity | parallel |
|---|---|---|---|---|---|---|---|
| invest (n=102) | 67/102 (22) | 70/102 (20) | 69/102 (21) | 68/102 (22) | 45/102 (18) | 71/102 (28) | 82/102 (25) |
| legal_rc (n=2) | 2/2 | 2/2 | 2/2 | 2/2 (1) | 2/2 | 2/2 | 2/2 |

## Evidence in results, by question type

Chance match in brackets where it is above zero.

| Slice | linkup-standard | linkup-deep | linkup-tuned | linkup-fast | linkup-rewritten | perplexity | parallel |
|---|---|---|---|---|---|---|---|
| P1 (n=20) | 18/20 (1) | 18/20 (1) | 18/20 (1) | 18/20 (1) | 16/20 (1) | 17/20 (1) | 19/20 (1) |
| P2 (n=40) | 22/40 (5) | 23/40 (2) | 21/40 (2) | 21/40 (4) | 8/40 (4) | 25/40 (8) | 31/40 (7) |
| P3 (n=30) | 26/30 (16) | 28/30 (17) | 29/30 (19) | 30/30 (18) | 23/30 (14) | 30/30 (19) | 30/30 (16) |
| P4 (n=14) | 3/14 | 3/14 (1) | 3/14 | 1/14 | 0/14 | 1/14 (1) | 4/14 (2) |

## Evidence in results, by origin

Chance match in brackets where it is above zero.

| Slice | linkup-standard | linkup-deep | linkup-tuned | linkup-fast | linkup-rewritten | perplexity | parallel |
|---|---|---|---|---|---|---|---|
| edgar-8k-exec (n=20) | 18/20 (1) | 18/20 (1) | 18/20 (1) | 18/20 (1) | 16/20 (1) | 17/20 (1) | 19/20 (1) |
| finsearchcomp-t2 (n=40) | 22/40 (5) | 23/40 (2) | 21/40 (2) | 21/40 (4) | 8/40 (4) | 25/40 (8) | 31/40 (7) |
| finsearchcomp-t3 (n=14) | 3/14 | 3/14 (1) | 3/14 | 1/14 | 0/14 | 1/14 (1) | 4/14 (2) |
| linkup-gtm-funding (n=30) | 26/30 (16) | 28/30 (17) | 29/30 (19) | 30/30 (18) | 23/30 (14) | 30/30 (19) | 30/30 (16) |

## Evidence in results, by workflow

Chance match in brackets where it is above zero.

| Slice | linkup-standard | linkup-deep | linkup-tuned | linkup-fast | linkup-rewritten | perplexity | parallel |
|---|---|---|---|---|---|---|---|
| chat Q&A (n=104) | 69/104 (22) | 72/104 (21) | 71/104 (22) | 70/104 (23) | 47/104 (19) | 73/104 (29) | 84/104 (26) |

# Retrieval scorecard: 20261124-144120-all-retrieval

Split: **all** · rows: 98 · one search per question and arm, query as typed · no LLM · as-of date in query text on point-in-time rows: all · run date: 2026-11-24

These metrics need no model. Correctness comes after the Claude Code session answers and grades (see handoff/INSTRUCTIONS.md), in scorecard.md.

| Arm | Errors | Results / q | Evidence in results | Gold source in results | Authoritative share of results | Metadata complete | Point-in-time leaks | p50 search ms | Search $ / q (list) |
|---|---|---|---|---|---|---|---|---|---|
| linkup-standard | 0 | 10.0 | 70/98 | 30/98 | 7% | 67% | 0/110 dated after cutoff | 1695 | 0.005 |
| linkup-deep | 0 | 10.0 | 73/98 | 47/98 | 16% | 0% | 0/110 dated after cutoff | 7396 | 0.050 |
| linkup-tuned | 0 | 9.9 | 61/98 | 52/98 | 34% | 12% | 0/102 dated after cutoff | 6719 | 0.036 |
| perplexity | 0 | 10.0 | 75/98 | 63/98 | 29% | 78% | 0/110 dated after cutoff | 403 | — |
| parallel | 0 | 10.0 | 77/98 | 66/98 | 28% | 88% | 11/110 dated after cutoff | 2401 | — |

- **Evidence in results**: a required fact or acceptable variant appears word for word in a result's title or content. A rough recall proxy: it misses paraphrases, so it undercounts for every arm.
- **Gold source in results**: a result's domain matches a gold source's domain.
- **Point-in-time leaks**: results whose publish date is after the row's cutoff. Results with no date can't be checked, and pages rewritten after publication keep their old date, so this is a lower bound.

## Evidence in results, by team

| Slice | linkup-standard | linkup-deep | linkup-tuned | perplexity | parallel |
|---|---|---|---|---|---|
| invest (n=46) | 30/46 | 33/46 | 32/46 | 34/46 | 35/46 |
| legal_rc (n=21) | 17/21 | 18/21 | 12/21 | 17/21 | 19/21 |
| tax_hr (n=14) | 11/14 | 11/14 | 5/14 | 12/14 | 11/14 |
| tech (n=17) | 12/17 | 11/17 | 12/17 | 12/17 | 12/17 |

## Evidence in results, by question type

| Slice | linkup-standard | linkup-deep | linkup-tuned | perplexity | parallel |
|---|---|---|---|---|---|
| P1 (n=29) | 24/29 | 25/29 | 22/29 | 25/29 | 24/29 |
| P2 (n=28) | 17/28 | 18/28 | 13/28 | 17/28 | 20/28 |
| P3 (n=16) | 13/16 | 13/16 | 12/16 | 14/16 | 14/16 |
| P4 (n=14) | 9/14 | 10/14 | 7/14 | 12/14 | 12/14 |
| P5 (n=11) | 7/11 | 7/11 | 7/11 | 7/11 | 7/11 |

## Evidence in results, by origin

| Slice | linkup-standard | linkup-deep | linkup-tuned | perplexity | parallel |
|---|---|---|---|---|---|
| claude (n=81) | 63/81 | 65/81 | 54/81 | 65/81 | 66/81 |
| human (n=17) | 7/17 | 8/17 | 7/17 | 10/17 | 11/17 |

## Evidence in results, by workflow

| Slice | linkup-standard | linkup-deep | linkup-tuned | perplexity | parallel |
|---|---|---|---|---|---|
| chat Q&A (n=85) | 58/85 | 61/85 | 50/85 | 63/85 | 65/85 |
| crm_enrichment (n=5) | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| news_briefing (n=6) | 5/6 | 5/6 | 4/6 | 5/6 | 5/6 |
| sourcing_signal (n=2) | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |

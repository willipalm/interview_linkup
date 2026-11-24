# Scorecard: 20261124-143155-test

Split: **test** · rows: 82 · agent: `claude-sonnet-5-5` (effort medium) · judge: `claude-opus-5-5` · date filter on point-in-time rows: on · as-of date in query text: all · run date: 2026-11-24

## Summary

| Arm | Correct | Incorrect | Not attempted | Accuracy when attempted | F1 | Errors | Authoritative citations | Gold-source hit | Result metadata complete | Searches / q | p50 search ms | p50 answer s | LLM $ / q | Search $ / q (list) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| linkup-standard | **6/82** | 0 | 0 | 100% | 1.00 | 76 | 13/49 | 5/82 | 47% of 110 | 0.1 | 1628 | 13.3 | 0.003 | 0.001 |
| linkup-deep | **5/82** | 0 | 0 | 100% | 1.00 | 77 | 11/31 | 4/82 | 0% of 110 | 0.1 | 7647 | 26.3 | 0.002 | 0.007 |
| linkup-native | **6/82** | 0 | 0 | 100% | 1.00 | 76 | 8/36 | 3/82 | 82% of 60 | 0.1 | 1432 | 9.7 | 0.002 | 0.000 |
| linkup-tuned | **6/82** | 0 | 0 | 100% | 1.00 | 76 | 10/41 | 4/82 | 52% of 100 | 0.1 | 1189 | 10.7 | 0.002 | 0.001 |
| perplexity | **5/82** | 0 | 0 | 100% | 1.00 | 77 | 18/35 | 4/82 | 67% of 109 | 0.1 | 382 | 8.9 | 0.003 | — |

Grading: SimpleQA grader (openai/simple-evals) plus this benchmark's required-facts rules. Not attempted = the answer doesn't give the required facts but contradicts nothing (an honest "couldn't find it" lands here). Accuracy when attempted = correct / (correct + incorrect); F1 is SimpleQA's harmonic mean of that and overall correct. An API that guesses less scores higher on accuracy when attempted.

Result metadata complete = the result has a URL, a title and a publish date (publisher comes from the URL). Search $ = vendor list price per call x calls (Linkup: $0.005 fast/standard, $0.05 deep, searchResults). — = no checked list price; use your contract. Contract pricing will differ.

> **linkup-native** uses a Linkup-specific tool (depth, dates and domain priority chosen by the agent) and Linkup's query guidance. The other arms use the generic web_search tool, so linkup-native vs a generic competitor arm isn't like-for-like. Compare it with linkup-standard to see what Linkup's best practices add, and with perplexity-native / parallel-native (built the same way from their docs) for the vendor decision.

## Head-to-head (paired, same questions)

| Linkup arm | vs | Only Linkup right | Only competitor right | Both right | Both wrong |
|---|---|---|---|---|---|
| linkup-standard | perplexity | 1 | 0 | 5 | 76 |
| linkup-deep | perplexity | 0 | 0 | 5 | 77 |
| linkup-native | perplexity | 1 | 0 | 5 | 76 |
| linkup-tuned | perplexity | 1 | 0 | 5 | 76 |

## By team

| Team | linkup-standard | linkup-deep | linkup-native | linkup-tuned | perplexity |
|---|---|---|---|---|---|
| tech (n=14) | 6/14 | 5/14 | 6/14 | 6/14 | 5/14 |
| legal_rc (n=17) | 0/17 | 0/17 | 0/17 | 0/17 | 0/17 |
| tax_hr (n=11) | 0/11 | 0/11 | 0/11 | 0/11 | 0/11 |
| invest (n=40) | 0/40 | 0/40 | 0/40 | 0/40 | 0/40 |

## By question type

| Question type | linkup-standard | linkup-deep | linkup-native | linkup-tuned | perplexity |
|---|---|---|---|---|---|
| P1 news / freshness (n=27) | 4/27 | 3/27 | 4/27 | 4/27 | 3/27 |
| P2 official source (n=22) | 0/22 | 0/22 | 0/22 | 0/22 | 0/22 |
| P3 entity lookup (n=15) | 0/15 | 0/15 | 0/15 | 0/15 | 0/15 |
| P4 multi-hop (n=9) | 0/9 | 0/9 | 0/9 | 0/9 | 0/9 |
| P5 technical docs (n=9) | 2/9 | 2/9 | 2/9 | 2/9 | 2/9 |

## By freshness

| Freshness | linkup-standard | linkup-deep | linkup-native | linkup-tuned | perplexity |
|---|---|---|---|---|---|
| breaking (n=34) | 4/34 | 3/34 | 4/34 | 4/34 | 3/34 |
| volatile (n=16) | 1/16 | 1/16 | 1/16 | 1/16 | 1/16 |
| slow (n=17) | 1/17 | 1/17 | 1/17 | 1/17 | 1/17 |
| static (n=5) | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| point-in-time twin (n=10) | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 |

## By workflow

| Workflow | linkup-standard | linkup-deep | linkup-native | linkup-tuned | perplexity |
|---|---|---|---|---|---|
| sourcing signal check (n=2) | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| CRM enrichment (n=5) | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| fintech news briefing (n=6) | 0/6 | 0/6 | 0/6 | 0/6 | 0/6 |
| chat Q&A (no workflow) (n=69) | 6/69 | 5/69 | 6/69 | 6/69 | 5/69 |

Cells: correct/n, with (k✗) = answers graded INCORRECT. Freshness: breaking = event in the last ~7 days, volatile = can change within weeks, point-in-time twin = asked as of a past date with the date filter on.

## linkup-native: depth chosen per search, by question type

| Question type | fast | standard | deep | from_date set | domains prioritised |
|---|---|---|---|---|---|
| P1 news / freshness | 0 | 5 | 0 | 4 | 1 |
| P5 technical docs | 0 | 2 | 0 | 1 | 1 |

## Per question

✅ correct · ❌ incorrect · ➖ not attempted · ⚠️ error

| ID | Team | Pattern | Trap | linkup-standard | linkup-deep | linkup-native | linkup-tuned | perplexity | Linkup only? |
|---|---|---|---|---|---|---|---|---|---|
| INV-01 | invest | P1 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-02 | invest | P4 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-03 | invest | P1 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-04 | invest | P3 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-05 | invest | P1 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-07 | invest | P1 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-08 | invest | P4 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-09 | invest | P3 | stale | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-09-PIT | invest | P3 | point-in-time | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-09-PIT2 | invest | P3 | point-in-time | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-10 | invest | P1 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-11 | invest | P1 | paywall | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-13 | invest | P2 | stale | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-13-PIT | invest | P1 | point-in-time | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-14 | invest | P2 | nonexistent | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-20 | invest | P1 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-23 | invest | P3 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-25 | invest | P4 | contested | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-26 | invest | P1 | contested | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-27 | invest | P1 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-28 | invest | P1 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-29 | invest | P1 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-31 | invest | P1 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-32 | invest | P4 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-33 | invest | P3 | ambiguous | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-34 | invest | P3 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-35 | invest | P4 | stale | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-35-PIT | invest | P3 | point-in-time | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-36 | invest | P1 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-37 | invest | P1 | contested | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-H01 | invest | P1 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-H01-PIT | invest | P1 | point-in-time | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-H02 | invest | P2 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-H03 | invest | P3 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-H04 | invest | P2 | nonexistent | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-H05 | invest | P3 | premium | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-H06 | invest | P3 | premium | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-H07 | invest | P2 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-H08 | invest | P2 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-H09 | invest | P3 | ambiguous | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-01 | legal_rc | P2 | stale | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-01-PIT | legal_rc | P2 | point-in-time | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-02 | legal_rc | P2 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-04 | legal_rc | P2 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-05 | legal_rc | P1 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-06 | legal_rc | P1 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-07 | legal_rc | P1 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-09 | legal_rc | P3 | stale | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-09-PIT | legal_rc | P3 | point-in-time | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-10 | legal_rc | P3 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-11 | legal_rc | P4 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-15 | legal_rc | P4 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-19 | legal_rc | P2 | contested | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-20 | legal_rc | P2 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-21 | legal_rc | P2 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-22 | legal_rc | P2 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-H01 | legal_rc | P2 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TAX-05 | tax_hr | P2 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TAX-07 | tax_hr | P2 | stale | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TAX-07-PIT | tax_hr | P2 | point-in-time | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TAX-08 | tax_hr | P4 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TAX-09 | tax_hr | P1 | contested | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TAX-10 | tax_hr | P2 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TAX-12 | tax_hr | P4 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TAX-13 | tax_hr | P1 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TAX-H01 | tax_hr | P2 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TAX-H02 | tax_hr | P2 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TAX-H03 | tax_hr | P2 | premium | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TECH-04 | tech | P5 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-06 | tech | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-08 | tech | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-10 | tech | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-11 | tech | P5 | stale | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-11-PIT | tech | P5 | point-in-time | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TECH-12 | tech | P1 | stale | ✅ | ⚠️ | ✅ | ✅ | ⚠️ | **Linkup wins** |
| TECH-12-PIT | tech | P5 | point-in-time | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TECH-13 | tech | P5 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TECH-14 | tech | P5 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TECH-16 | tech | P1 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TECH-H01 | tech | P5 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TECH-H02 | tech | P5 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TECH-H03 | tech | P5 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |

# Scorecard: 20261123-164852-dev

Split: **dev** · rows: 16 · agent: `claude-sonnet-5-5` (effort medium) · judge: `claude-opus-5-5` · date filter on point-in-time rows: on · run date: 2026-11-23

> Dev split: for tuning and a first look only. With this few rows, one question is ~6 points. Don't report these numbers as results.

## Summary

| Arm | Correct | Incorrect | Not attempted | Accuracy when attempted | F1 | Errors | Authoritative citations | Gold-source hit | Result metadata complete | Searches / q | p50 search ms | p50 answer s | LLM $ / q | Search $ / q (list) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| linkup-standard | **15/16** | 1 | 0 | 94% | 0.94 | 0 | 11/109 | 8/16 | 64% of 250 | 1.6 | 1933 | 13.2 | 0.038 | 0.008 |
| linkup-deep | **16/16** | 0 | 0 | 100% | 1.00 | 0 | 26/100 | 9/16 | 0% of 290 | 1.8 | 5853 | 22.3 | 0.038 | 0.091 |
| linkup-tuned | **14/16** | 0 | 2 | 100% | 0.93 | 0 | 38/91 | 9/16 | 8% of 343 | 2.2 | 5880 | 23.4 | 0.042 | 0.073 |
| linkup-native | **14/16** | 1 | 1 | 93% | 0.90 | 0 | 19/71 | 6/16 | 69% of 287 | 2.0 | 1870 | 12.7 | 0.042 | 0.010 |

Grading: SimpleQA grader (openai/simple-evals) plus this benchmark's required-facts rules. Not attempted = the answer doesn't give the required facts but contradicts nothing (an honest "couldn't find it" lands here). Accuracy when attempted = correct / (correct + incorrect); F1 is SimpleQA's harmonic mean of that and overall correct. An API that guesses less scores higher on accuracy when attempted.

Result metadata complete = the result has a URL, a title and a publish date (publisher comes from the URL). Search $ = vendor list price per call x calls (Linkup: $0.005 fast/standard, $0.05 deep, searchResults). — = no checked list price; use your contract. Contract pricing will differ.

> **linkup-native** uses a Linkup-specific tool (depth, dates and domain priority chosen by the agent) and Linkup's query guidance. The other arms use the generic web_search tool, so linkup-native vs a generic competitor arm isn't like-for-like. Compare it with linkup-standard to see what Linkup's best practices add, and with perplexity-native / parallel-native (built the same way from their docs) for the vendor decision.

## By team

| Team | linkup-standard | linkup-deep | linkup-tuned | linkup-native |
|---|---|---|---|---|
| tech (n=3) | 3/3 | 3/3 | 3/3 | 3/3 |
| legal_rc (n=5) | 4/5 (1✗) | 5/5 | 4/5 | 3/5 (1✗) |
| tax_hr (n=3) | 3/3 | 3/3 | 2/3 | 3/3 |
| invest (n=5) | 5/5 | 5/5 | 5/5 | 5/5 |

## By question type

| Question type | linkup-standard | linkup-deep | linkup-tuned | linkup-native |
|---|---|---|---|---|
| P1 news / freshness (n=2) | 2/2 | 2/2 | 2/2 | 2/2 |
| P2 official source (n=7) | 6/7 (1✗) | 7/7 | 5/7 | 5/7 (1✗) |
| P3 entity lookup (n=1) | 1/1 | 1/1 | 1/1 | 1/1 |
| P4 multi-hop (n=4) | 4/4 | 4/4 | 4/4 | 4/4 |
| P5 technical docs (n=2) | 2/2 | 2/2 | 2/2 | 2/2 |

## By freshness

| Freshness | linkup-standard | linkup-deep | linkup-tuned | linkup-native |
|---|---|---|---|---|
| breaking (n=4) | 4/4 | 4/4 | 4/4 | 4/4 |
| volatile (n=4) | 4/4 | 4/4 | 4/4 | 4/4 |
| slow (n=4) | 4/4 | 4/4 | 3/4 | 4/4 |
| static (n=3) | 3/3 | 3/3 | 2/3 | 2/3 |
| point-in-time twin (n=1) | 0/1 (1✗) | 1/1 | 1/1 | 0/1 (1✗) |

Cells: correct/n, with (k✗) = answers graded INCORRECT. Freshness: breaking = event in the last ~7 days, volatile = can change within weeks, point-in-time twin = asked as of a past date with the date filter on.

## linkup-native: depth chosen per search, by question type

| Question type | fast | standard | deep | from_date set | domains prioritised |
|---|---|---|---|---|---|
| P1 news / freshness | 0 | 3 | 0 | 3 | 1 |
| P2 official source | 0 | 19 | 0 | 11 | 19 |
| P3 entity lookup | 0 | 1 | 0 | 1 | 0 |
| P4 multi-hop | 0 | 7 | 0 | 5 | 3 |
| P5 technical docs | 0 | 2 | 0 | 1 | 0 |

## Per question

✅ correct · ❌ incorrect · ➖ not attempted · ⚠️ error · no competitor arms in this run, so no win/lose flags

| ID | Team | Pattern | Trap | linkup-standard | linkup-deep | linkup-tuned | linkup-native | Linkup only? |
|---|---|---|---|---|---|---|---|---|
| INV-06 | invest | P3 | ambiguous | ✅ | ✅ | ✅ | ✅ |  |
| INV-16 | invest | P1 |  | ✅ | ✅ | ✅ | ✅ |  |
| INV-18 | invest | P4 |  | ✅ | ✅ | ✅ | ✅ |  |
| INV-19 | invest | P4 |  | ✅ | ✅ | ✅ | ✅ |  |
| INV-21 | invest | P1 |  | ✅ | ✅ | ✅ | ✅ |  |
| LRC-03 | legal_rc | P2 | stale | ✅ | ✅ | ✅ | ✅ |  |
| LRC-03-PIT | legal_rc | P2 | point-in-time | ❌ | ✅ | ✅ | ❌ |  |
| LRC-12 | legal_rc | P2 | nonexistent | ✅ | ✅ | ✅ | ✅ |  |
| LRC-13 | legal_rc | P2 |  | ✅ | ✅ | ➖ | ➖ |  |
| LRC-17 | legal_rc | P2 |  | ✅ | ✅ | ✅ | ✅ |  |
| TAX-01 | tax_hr | P2 |  | ✅ | ✅ | ✅ | ✅ |  |
| TAX-03 | tax_hr | P2 |  | ✅ | ✅ | ➖ | ✅ |  |
| TAX-11 | tax_hr | P4 |  | ✅ | ✅ | ✅ | ✅ |  |
| TECH-02 | tech | P5 |  | ✅ | ✅ | ✅ | ✅ |  |
| TECH-03 | tech | P5 |  | ✅ | ✅ | ✅ | ✅ |  |
| TECH-07 | tech | P4 |  | ✅ | ✅ | ✅ | ✅ |  |

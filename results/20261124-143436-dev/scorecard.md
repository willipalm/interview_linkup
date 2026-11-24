# Scorecard: 20261124-143436-dev

Split: **dev** · rows: 16 · agent: `claude-sonnet-5-5` (effort medium) · judge: `claude-opus-5-5` · date filter on point-in-time rows: on · as-of date in query text: all · run date: 2026-11-24

> Dev split: for tuning and a first look only. With this few rows, one question is ~6 points. Don't report these numbers as results.

## Summary

| Arm | Correct | Incorrect | Not attempted | Accuracy when attempted | F1 | Errors | Authoritative citations | Gold-source hit | Result metadata complete | Searches / q | p50 search ms | p50 answer s | LLM $ / q | Search $ / q (list) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| linkup-standard | **0/16** | 0 | 0 | 0% | 0.00 | 16 | 0/0 | 0/16 | 0% of 0 | 0.0 | — | — | 0.000 | — |
| linkup-deep | **0/16** | 0 | 0 | 0% | 0.00 | 16 | 0/0 | 0/16 | 0% of 0 | 0.0 | — | — | 0.000 | — |
| linkup-native | **0/16** | 0 | 0 | 0% | 0.00 | 16 | 0/0 | 0/16 | 0% of 0 | 0.0 | — | — | 0.000 | — |
| linkup-tuned | **0/16** | 0 | 0 | 0% | 0.00 | 16 | 0/0 | 0/16 | 0% of 0 | 0.0 | — | — | 0.000 | — |
| perplexity | **0/16** | 0 | 0 | 0% | 0.00 | 16 | 0/0 | 0/16 | 0% of 0 | 0.0 | — | — | 0.000 | — |

Grading: SimpleQA grader (openai/simple-evals) plus this benchmark's required-facts rules. Not attempted = the answer doesn't give the required facts but contradicts nothing (an honest "couldn't find it" lands here). Accuracy when attempted = correct / (correct + incorrect); F1 is SimpleQA's harmonic mean of that and overall correct. An API that guesses less scores higher on accuracy when attempted.

Result metadata complete = the result has a URL, a title and a publish date (publisher comes from the URL). Search $ = vendor list price per call x calls (Linkup: $0.005 fast/standard, $0.05 deep, searchResults). — = no checked list price; use your contract. Contract pricing will differ.

> **linkup-native** uses a Linkup-specific tool (depth, dates and domain priority chosen by the agent) and Linkup's query guidance. The other arms use the generic web_search tool, so linkup-native vs a generic competitor arm isn't like-for-like. Compare it with linkup-standard to see what Linkup's best practices add, and with perplexity-native / parallel-native (built the same way from their docs) for the vendor decision.

## Head-to-head (paired, same questions)

| Linkup arm | vs | Only Linkup right | Only competitor right | Both right | Both wrong |
|---|---|---|---|---|---|
| linkup-standard | perplexity | 0 | 0 | 0 | 16 |
| linkup-deep | perplexity | 0 | 0 | 0 | 16 |
| linkup-native | perplexity | 0 | 0 | 0 | 16 |
| linkup-tuned | perplexity | 0 | 0 | 0 | 16 |

## By team

| Team | linkup-standard | linkup-deep | linkup-native | linkup-tuned | perplexity |
|---|---|---|---|---|---|
| tech (n=3) | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| legal_rc (n=4) | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| tax_hr (n=3) | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| invest (n=6) | 0/6 | 0/6 | 0/6 | 0/6 | 0/6 |

## By question type

| Question type | linkup-standard | linkup-deep | linkup-native | linkup-tuned | perplexity |
|---|---|---|---|---|---|
| P1 news / freshness (n=2) | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| P2 official source (n=6) | 0/6 | 0/6 | 0/6 | 0/6 | 0/6 |
| P3 entity lookup (n=1) | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| P4 multi-hop (n=5) | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| P5 technical docs (n=2) | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |

## By freshness

| Freshness | linkup-standard | linkup-deep | linkup-native | linkup-tuned | perplexity |
|---|---|---|---|---|---|
| breaking (n=4) | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| volatile (n=4) | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| slow (n=4) | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| static (n=3) | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| point-in-time twin (n=1) | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |

## By workflow

| Workflow | linkup-standard | linkup-deep | linkup-native | linkup-tuned | perplexity |
|---|---|---|---|---|---|
| chat Q&A (no workflow) (n=16) | 0/16 | 0/16 | 0/16 | 0/16 | 0/16 |

Cells: correct/n, with (k✗) = answers graded INCORRECT. Freshness: breaking = event in the last ~7 days, volatile = can change within weeks, point-in-time twin = asked as of a past date with the date filter on.

## linkup-native: depth chosen per search, by question type

| Question type | fast | standard | deep | from_date set | domains prioritised |
|---|---|---|---|---|---|

## Per question

✅ correct · ❌ incorrect · ➖ not attempted · ⚠️ error

| ID | Team | Pattern | Trap | linkup-standard | linkup-deep | linkup-native | linkup-tuned | perplexity | Linkup only? |
|---|---|---|---|---|---|---|---|---|---|
| INV-06 | invest | P3 | ambiguous | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-16 | invest | P1 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-18 | invest | P4 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-18-PIT | invest | P4 | point-in-time | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-19 | invest | P4 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| INV-21 | invest | P1 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-03 | legal_rc | P2 | stale | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-12 | legal_rc | P2 | nonexistent | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-13 | legal_rc | P2 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| LRC-17 | legal_rc | P2 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TAX-01 | tax_hr | P2 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TAX-03 | tax_hr | P2 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TAX-11 | tax_hr | P4 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TECH-02 | tech | P5 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TECH-03 | tech | P5 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |
| TECH-07 | tech | P4 |  | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |  |

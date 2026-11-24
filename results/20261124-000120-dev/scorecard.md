# Scorecard: 20261124-000120-dev

Split: **dev** · rows: 1 · agent: `claude-sonnet-5-5` (effort medium) · judge: `claude-opus-5-5` · date filter on point-in-time rows: on · run date: 2026-11-24

> Dev split: for tuning and a first look only. With this few rows, one question is ~6 points. Don't report these numbers as results.

## Summary

| Arm | Correct | Incorrect | Not attempted | Accuracy when attempted | F1 | Errors | Authoritative citations | Gold-source hit | Result metadata complete | Searches / q | p50 search ms | p50 answer s | LLM $ / q | Search $ / q (list) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| linkup-standard | **1/1** | 0 | 0 | 100% | 1.00 | 0 | 3/8 | 0/1 | 100% of 20 | 2.0 | 1663 | 12.7 | 0.038 | 0.010 |
| linkup-deep | **1/1** | 0 | 0 | 100% | 1.00 | 0 | 0/6 | 0/1 | 0% of 20 | 2.0 | 5339 | 19.3 | 0.041 | 0.100 |
| linkup-native | **1/1** | 0 | 0 | 100% | 1.00 | 0 | 1/5 | 0/1 | 100% of 10 | 1.0 | 2247 | 9.7 | 0.027 | 0.005 |
| linkup-tuned | **1/1** | 0 | 0 | 100% | 1.00 | 0 | 1/7 | 0/1 | 0% of 20 | 2.0 | 5353 | 19.2 | 0.042 | 0.100 |

Grading: SimpleQA grader (openai/simple-evals) plus this benchmark's required-facts rules. Not attempted = the answer doesn't give the required facts but contradicts nothing (an honest "couldn't find it" lands here). Accuracy when attempted = correct / (correct + incorrect); F1 is SimpleQA's harmonic mean of that and overall correct. An API that guesses less scores higher on accuracy when attempted.

Result metadata complete = the result has a URL, a title and a publish date (publisher comes from the URL). Search $ = vendor list price per call x calls (Linkup: $0.005 fast/standard, $0.05 deep, searchResults). — = no checked list price; use your contract. Contract pricing will differ.

> **linkup-native** uses a Linkup-specific tool (depth, dates and domain priority chosen by the agent) and Linkup's query guidance. The other arms use the generic web_search tool, so linkup-native vs a generic competitor arm isn't like-for-like. Compare it with linkup-standard to see what Linkup's best practices add, and with perplexity-native / parallel-native (built the same way from their docs) for the vendor decision.

## By team

| Team | linkup-standard | linkup-deep | linkup-native | linkup-tuned |
|---|---|---|---|---|
| invest (n=1) | 1/1 | 1/1 | 1/1 | 1/1 |

## By question type

| Question type | linkup-standard | linkup-deep | linkup-native | linkup-tuned |
|---|---|---|---|---|
| P4 multi-hop (n=1) | 1/1 | 1/1 | 1/1 | 1/1 |

## By freshness

| Freshness | linkup-standard | linkup-deep | linkup-native | linkup-tuned |
|---|---|---|---|---|
| point-in-time twin (n=1) | 1/1 | 1/1 | 1/1 | 1/1 |

## By workflow

| Workflow | linkup-standard | linkup-deep | linkup-native | linkup-tuned |
|---|---|---|---|---|
| chat Q&A (no workflow) (n=1) | 1/1 | 1/1 | 1/1 | 1/1 |

Cells: correct/n, with (k✗) = answers graded INCORRECT. Freshness: breaking = event in the last ~7 days, volatile = can change within weeks, point-in-time twin = asked as of a past date with the date filter on.

## linkup-native: depth chosen per search, by question type

| Question type | fast | standard | deep | from_date set | domains prioritised |
|---|---|---|---|---|---|
| P4 multi-hop | 0 | 1 | 0 | 1 | 0 |

## Per question

✅ correct · ❌ incorrect · ➖ not attempted · ⚠️ error · no competitor arms in this run, so no win/lose flags

| ID | Team | Pattern | Trap | linkup-standard | linkup-deep | linkup-native | linkup-tuned | Linkup only? |
|---|---|---|---|---|---|---|---|---|
| INV-18-PIT | invest | P4 | point-in-time | ✅ | ✅ | ✅ | ✅ |  |

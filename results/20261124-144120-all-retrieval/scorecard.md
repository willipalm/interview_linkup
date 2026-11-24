# Scorecard: 20261124-144120-all-retrieval

Questions: **bench1** · split: **all** · rows: 98 · agent: `claude-opus-5-5 via Claude Code (1 search, results given)` (effort n/a) · judge: `claude-opus-5-5 via Claude Code` · date filter on point-in-time rows: on · as-of date in query text: all · run date: 2026-11-24

> All rows, dev and test together. The dev rows were used for tuning linkup-tuned, so report test-split numbers for that arm.

## Summary

| Arm | Correct | Incorrect | Not attempted | Accuracy when attempted | F1 | Errors | Authoritative citations | Gold-source hit | Result metadata complete | Searches / q | p50 search ms | p50 answer s | LLM $ / q | Search $ / q (list) | Search $ / correct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| linkup-standard | **88/98** | 4 | 6 | 96% | 0.93 | 0 | 38/403 | 22/98 | 67% of 980 | 1.0 | 1695 | 1.7 | 0.000 | 0.005 | 0.0056 |
| linkup-deep | **89/98** | 2 | 7 | 98% | 0.94 | 0 | 77/399 | 38/98 | 0% of 980 | 1.0 | 7396 | 7.4 | 0.000 | 0.050 | 0.0551 |
| linkup-tuned | **82/98** | 2 | 14 | 98% | 0.90 | 0 | 122/365 | 41/98 | 12% of 972 | 1.0 | 6719 | 6.7 | 0.000 | 0.036 | 0.0427 |
| perplexity | **95/98** | 2 | 1 | 98% | 0.97 | 0 | 125/400 | 51/98 | 78% of 980 | 1.0 | 403 | 0.4 | 0.000 | 0.005 | 0.0052 |
| parallel | **95/98** | 1 | 2 | 99% | 0.98 | 0 | 170/476 | 60/98 | 88% of 980 | 1.0 | 2401 | 2.4 | 0.000 | 0.005 | 0.0052 |

Grading: SimpleQA grader (openai/simple-evals) plus this benchmark's required-facts rules. Not attempted = the answer doesn't give the required facts but contradicts nothing (an honest "couldn't find it" lands here). Accuracy when attempted = correct / (correct + incorrect); F1 is SimpleQA's harmonic mean of that and overall correct. An API that guesses less scores higher on accuracy when attempted.

Result metadata complete = the result has a URL, a title and a publish date (publisher comes from the URL). Search $ = vendor list price per call x calls: Linkup $0.005 fast/standard, $0.05 deep (searchResults); Perplexity Search API $0.005 per request; Parallel Search API $0.005 per request in its default advanced mode with 10 results (pricing pages read 2026-11-24). Search $ / correct = total search spend / correct answers; it leaves out the answering model, which is the same for every arm. — = no checked list price. Contract pricing will differ.

## Head-to-head (paired, same questions)

| Linkup arm | vs | Only Linkup right | Only competitor right | Both right | Both wrong |
|---|---|---|---|---|---|
| linkup-standard | perplexity | 0 | 7 | 88 | 3 |
| linkup-standard | parallel | 0 | 7 | 88 | 3 |
| linkup-deep | perplexity | 1 | 7 | 88 | 2 |
| linkup-deep | parallel | 1 | 7 | 88 | 2 |
| linkup-tuned | perplexity | 1 | 14 | 81 | 2 |
| linkup-tuned | parallel | 1 | 14 | 81 | 2 |

## By team

| Team | linkup-standard | linkup-deep | linkup-tuned | perplexity | parallel |
|---|---|---|---|---|---|
| tech (n=17) | 17/17 | 16/17 (1✗) | 17/17 | 17/17 | 17/17 |
| legal_rc (n=21) | 19/21 | 20/21 | 14/21 | 21/21 | 21/21 |
| tax_hr (n=14) | 13/14 (1✗) | 13/14 | 10/14 (1✗) | 13/14 (1✗) | 13/14 |
| invest (n=46) | 39/46 (3✗) | 40/46 (1✗) | 41/46 (1✗) | 44/46 (1✗) | 44/46 (1✗) |

## By question type

| Question type | linkup-standard | linkup-deep | linkup-tuned | perplexity | parallel |
|---|---|---|---|---|---|
| P1 news / freshness (n=29) | 25/29 (2✗) | 27/29 (1✗) | 25/29 (2✗) | 27/29 (1✗) | 27/29 (1✗) |
| P2 official source (n=28) | 24/28 (1✗) | 24/28 | 18/28 | 27/28 (1✗) | 27/28 |
| P3 entity lookup (n=16) | 14/16 (1✗) | 15/16 | 14/16 | 16/16 | 16/16 |
| P4 multi-hop (n=14) | 14/14 | 13/14 | 14/14 | 14/14 | 14/14 |
| P5 technical docs (n=11) | 11/11 | 10/11 (1✗) | 11/11 | 11/11 | 11/11 |

## By freshness

| Freshness | linkup-standard | linkup-deep | linkup-tuned | perplexity | parallel |
|---|---|---|---|---|---|
| breaking (n=38) | 33/38 (2✗) | 35/38 (1✗) | 33/38 (1✗) | 37/38 (1✗) | 37/38 (1✗) |
| volatile (n=20) | 19/20 | 19/20 | 17/20 (1✗) | 20/20 | 20/20 |
| slow (n=21) | 20/21 (1✗) | 19/21 (1✗) | 19/21 | 20/21 (1✗) | 20/21 |
| static (n=8) | 7/8 | 7/8 | 5/8 | 8/8 | 8/8 |
| point-in-time twin (n=11) | 9/11 (1✗) | 9/11 | 8/11 | 10/11 | 10/11 |

## By workflow

| Workflow | linkup-standard | linkup-deep | linkup-tuned | perplexity | parallel |
|---|---|---|---|---|---|
| sourcing signal check (n=2) | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 |
| CRM enrichment (n=5) | 4/5 (1✗) | 5/5 | 5/5 | 5/5 | 5/5 |
| fintech news briefing (n=6) | 5/6 | 5/6 | 4/6 | 6/6 | 6/6 |
| chat Q&A (no workflow) (n=85) | 77/85 (3✗) | 77/85 (2✗) | 71/85 (2✗) | 82/85 (2✗) | 82/85 (1✗) |

Cells: correct/n, with (k✗) = answers graded INCORRECT. Freshness: breaking = event in the last ~7 days, volatile = can change within weeks, point-in-time twin = asked as of a past date with the date filter on.

## Per question

✅ correct · ❌ incorrect · ➖ not attempted · ⚠️ error

| ID | Team | Pattern | Trap | linkup-standard | linkup-deep | linkup-tuned | perplexity | parallel | Linkup only? |
|---|---|---|---|---|---|---|---|---|---|
| INV-01 | invest | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-02 | invest | P4 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-03 | invest | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-04 | invest | P3 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-05 | invest | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-06 | invest | P3 | ambiguous | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-07 | invest | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-08 | invest | P4 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-09 | invest | P3 | stale | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-09-PIT | invest | P3 | point-in-time | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-09-PIT2 | invest | P3 | point-in-time | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-10 | invest | P1 |  | ❌ | ✅ | ✅ | ✅ | ✅ |  |
| INV-11 | invest | P1 | paywall | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-13 | invest | P2 | stale | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-13-PIT | invest | P1 | point-in-time | ✅ | ➖ | ✅ | ✅ | ✅ |  |
| INV-14 | invest | P2 | nonexistent | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-16 | invest | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-18 | invest | P4 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-18-PIT | invest | P4 | point-in-time | ✅ | ➖ | ✅ | ✅ | ✅ |  |
| INV-19 | invest | P4 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-20 | invest | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-21 | invest | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-23 | invest | P3 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-25 | invest | P4 | contested | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-26 | invest | P1 | contested | ❌ | ❌ | ❌ | ❌ | ❌ |  |
| INV-27 | invest | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-28 | invest | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-29 | invest | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-31 | invest | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-32 | invest | P4 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-33 | invest | P3 | ambiguous | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-34 | invest | P3 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-35 | invest | P4 | stale | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-35-PIT | invest | P3 | point-in-time | ❌ | ✅ | ✅ | ✅ | ✅ |  |
| INV-36 | invest | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-37 | invest | P1 | contested | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-H01 | invest | P1 |  | ✅ | ✅ | ➖ | ✅ | ✅ |  |
| INV-H01-PIT | invest | P1 | point-in-time | ➖ | ✅ | ✅ | ➖ | ➖ | **Linkup wins** |
| INV-H02 | invest | P2 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-H03 | invest | P3 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-H04 | invest | P2 | nonexistent | ➖ | ➖ | ➖ | ✅ | ✅ | **Linkup loses** |
| INV-H05 | invest | P3 | premium | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-H06 | invest | P3 | premium | ➖ | ➖ | ➖ | ✅ | ✅ | **Linkup loses** |
| INV-H07 | invest | P2 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| INV-H08 | invest | P2 |  | ➖ | ➖ | ➖ | ✅ | ✅ | **Linkup loses** |
| INV-H09 | invest | P3 | ambiguous | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| LRC-01 | legal_rc | P2 | stale | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| LRC-01-PIT | legal_rc | P2 | point-in-time | ✅ | ✅ | ➖ | ✅ | ✅ |  |
| LRC-02 | legal_rc | P2 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| LRC-03 | legal_rc | P2 | stale | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| LRC-04 | legal_rc | P2 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| LRC-05 | legal_rc | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| LRC-06 | legal_rc | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| LRC-07 | legal_rc | P1 |  | ➖ | ✅ | ➖ | ✅ | ✅ |  |
| LRC-09 | legal_rc | P3 | stale | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| LRC-09-PIT | legal_rc | P3 | point-in-time | ✅ | ✅ | ➖ | ✅ | ✅ |  |
| LRC-10 | legal_rc | P3 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| LRC-11 | legal_rc | P4 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| LRC-12 | legal_rc | P2 | nonexistent | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| LRC-13 | legal_rc | P2 |  | ✅ | ✅ | ➖ | ✅ | ✅ |  |
| LRC-15 | legal_rc | P4 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| LRC-17 | legal_rc | P2 |  | ✅ | ✅ | ➖ | ✅ | ✅ |  |
| LRC-19 | legal_rc | P2 | contested | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| LRC-20 | legal_rc | P2 |  | ➖ | ➖ | ➖ | ✅ | ✅ | **Linkup loses** |
| LRC-21 | legal_rc | P2 |  | ✅ | ✅ | ➖ | ✅ | ✅ |  |
| LRC-22 | legal_rc | P2 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| LRC-H01 | legal_rc | P2 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TAX-01 | tax_hr | P2 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TAX-03 | tax_hr | P2 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TAX-05 | tax_hr | P2 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TAX-07 | tax_hr | P2 | stale | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TAX-07-PIT | tax_hr | P2 | point-in-time | ✅ | ✅ | ➖ | ✅ | ✅ |  |
| TAX-08 | tax_hr | P4 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TAX-09 | tax_hr | P1 | contested | ✅ | ✅ | ❌ | ✅ | ✅ |  |
| TAX-10 | tax_hr | P2 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TAX-11 | tax_hr | P4 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TAX-12 | tax_hr | P4 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TAX-13 | tax_hr | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TAX-H01 | tax_hr | P2 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TAX-H02 | tax_hr | P2 |  | ✅ | ✅ | ➖ | ✅ | ✅ |  |
| TAX-H03 | tax_hr | P2 | premium | ❌ | ➖ | ➖ | ❌ | ➖ |  |
| TECH-02 | tech | P5 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-03 | tech | P5 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-04 | tech | P5 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-06 | tech | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-07 | tech | P4 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-08 | tech | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-10 | tech | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-11 | tech | P5 | stale | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-11-PIT | tech | P5 | point-in-time | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-12 | tech | P1 | stale | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-12-PIT | tech | P5 | point-in-time | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-13 | tech | P5 |  | ✅ | ❌ | ✅ | ✅ | ✅ |  |
| TECH-14 | tech | P5 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-16 | tech | P1 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-H01 | tech | P5 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-H02 | tech | P5 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |
| TECH-H03 | tech | P5 |  | ✅ | ✅ | ✅ | ✅ | ✅ |  |

## Where Linkup loses (a competitor got it right)

Root-cause each one (retrieval miss, stale index, wrong entity, LLM synthesis) and send it to Linkup engineering.

- **INV-10** (linkup-standard): Revenue and data center figures match, but the Q4 guide range is stated as ±2%, contradicting the gold's ±3%. Missing: —
- **INV-13-PIT** (linkup-deep): Says it couldn't find the latest meeting; the 2024 meeting is explicitly labeled as not the latest. Missing: held / no change, 3.50-3.75%
- **INV-18-PIT** (linkup-deep): Gives Blackstone's $1,346.3B but not Apollo's Q2 2026 AUM; its own disclaimed mixed-date gap estimate isn't graded, per the notes. Missing: Apollo ~$1.05T (Q2 2026)
- **INV-35-PIT** (linkup-standard): Point-in-time leak: although it answers 'independent', it names the post-as-of-date Capital One acquisition, which the notes count as INCORRECT. Missing: —
- **INV-H01** (linkup-tuned): Gives the CFR cut to Caa1 from B2 but dates it only as 'a Monday in mid-November', not Nov 16, 2026. Missing: November 16, 2026
- **INV-H04** (linkup-standard): Only says it couldn't find a bar date; doesn't say none has been set. Missing: no general claims bar date has been set
- **INV-H04** (linkup-deep): Only says it couldn't find a bar date; doesn't say none has been set. Missing: no general claims bar date has been set
- **INV-H04** (linkup-tuned): Only says it couldn't find a bar date, without saying none has been set; no contradiction. Missing: no general claims bar date has been set
- **INV-H06** (linkup-standard): Says it couldn't find S&P's rating; only Moody's and Fitch actions cited. Missing: S&P lowered Mercer's issuer credit rating to 'D', on November 13, 2026
- **INV-H06** (linkup-deep): Says it couldn't find the post-filing S&P rating; only cites other agencies and an older 2025 S&P action, no contradiction. Missing: S&P lowered Mercer's issuer credit rating to 'D', on November 13, 2026
- **INV-H06** (linkup-tuned): Correctly says S&P cut Mercer to 'D' but omits the Nov 13, 2026 date; nothing contradicts the gold. Missing: on November 13, 2026
- **INV-H08** (linkup-standard): Only says it couldn't find a go-shop and mentions commentary on a possible one; never states there is no go-shop. Missing: no go-shop period
- **INV-H08** (linkup-deep): Only says no result describes a go-shop; never states the agreement has none. Missing: no go-shop period
- **INV-H08** (linkup-tuned): Only says no result mentions a go-shop; never states the agreement has none. Missing: no go-shop period
- **LRC-01-PIT** (linkup-tuned): Says the results don't state the current date as of June 1, 2026; no leak. Missing: October 1, 2026
- **LRC-07** (linkup-standard): Identifies the India-based network but says the results don't give designation counts. Missing: 4 individuals, 9 entities
- **LRC-07** (linkup-tuned): Identifies the India-based network but says the results don't give the designation counts. Missing: 4 individuals, 9 entities
- **LRC-09-PIT** (linkup-tuned): Says it couldn't find who leads Enforcement as of Jan 15, 2026; no leak. Missing: Margaret Ryan
- **LRC-13** (linkup-tuned): Gives the reinstatement but says the reduced fee amount is not stated in the results. Missing: fee cut to $54M
- **LRC-17** (linkup-tuned): Gives the 16 April 2026 deadline but says it can't confirm the numeric leverage caps. Missing: 175% open-ended, 300% closed-ended
- **LRC-20** (linkup-standard): Lists counter-narcotics and cyber designations and the GLs generically, but names none of the required targets. Missing: Comancheros, 'Ndrangheta, Southeast Asia cyber-scam designations
- **LRC-20** (linkup-deep): Says it couldn't find the Nov 19, 2026 actions and labels the 2024 items as reference only, so no contradiction. Missing: Comancheros, 'Ndrangheta, Southeast Asia cyber-scam designations
- **LRC-20** (linkup-tuned): Names the Comanchero OMCG but only 'Canadian-based mafia' (not 'Ndrangheta) and one Burma cyber designee, without the scam-centre action; no contradiction. Missing: 'Ndrangheta, Southeast Asia cyber-scam designations
- **LRC-21** (linkup-tuned): Says it couldn't find the OCC charter status; no contradicting claim. Missing: final approval granted, early November 2026
- **TAX-07-PIT** (linkup-tuned): Says it couldn't find the general NYC minimum wage; no contradiction. Missing: $16.50
- **TAX-09** (linkup-tuned): Contested question: gives only the D. Mass. ruling against the fee and omits the D.D.C. decision upholding it. Missing: D.D.C. upheld the fee (Dec 2025)
- **TAX-H02** (linkup-tuned): Says it couldn't find New York's treatment. Missing: no add-back of the federal overtime deduction on the 2026 NY return, the deduction never enters the NY tax calculation
- **TECH-13** (linkup-deep): Has the three required features but presents reverted SQL/PGQ as shipped in PG19, which the answer key flags as wrong. Missing: —

## Caveats

- parallel: `to_date` not supported, so the filter wasn't applied (capability gap)

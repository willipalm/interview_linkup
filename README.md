# Search API benchmark: Linkup, Perplexity, Parallel

A harness for comparing search APIs as the retrieval tool behind an internal research assistant at an investment fund. Every arm gets the same questions and the same answering and grading setup. Only the search backend changes.

## Question sets

### bench1: built by hand for this fund

98 questions written from scratch around how each team at the fund would use search. Nothing comes from a public benchmark.

- Questions are organised by persona and by usage pattern (tables below). The full taxonomy is in `gold/TAXONOMY.md`.
- Each question has a gold answer written for it, the required facts an answer must contain, acceptable variants, the gold sources and an as-of date. Answers were checked against primary sources (EDGAR, regulator sites, court dockets, vendor release notes).
- 81 questions were drafted and verified with AI-assisted research. The other 17 are hard questions that AI search couldn't settle. Those were researched manually from primary sources, without any AI search tools, following the rules in `gold/HARD_QUESTIONS.md`.
- Some questions have traps: stale facts, contested facts, events that never happened, look-alike names, paywalled or premium sources. 11 point-in-time variants ask the same question as of a past date.
- 16 questions form a dev split used for tuning `linkup-tuned`. The rest are test.
- The set is defined in `scripts/build_gold.py`, written to `gold/gold_set.jsonl` and checked with `scripts/validate_gold.py`.

Personas:

| Persona | Sub-teams | Questions | Typical questions |
|---|---|---|---|
| Investing | private markets, credit, distressed, macro | 46 | Deal and restructuring news, rating actions, court dockets, fund and company facts |
| Legal and compliance | compliance, legal, risk | 21 | Rules and deadlines from primary sources, enforcement actions, sanctions, rulings |
| Tech and engineering | platform, security, data | 17 | Versions, changelogs, CVEs, API limits, vendor security |
| Tax and HR | HR, tax | 14 | IRS and state guidance, annual limits, employment-law changes |

Usage patterns:

| Pattern | Questions | What a good answer does |
|---|---|---|
| News and freshness | 29 | Finds the recent event with the right date, not an older one |
| Official source | 28 | Grounds the answer in a primary source (sec.gov, irs.gov, federalregister.gov, dockets, company IR) |
| Entity lookup | 16 | Gets a fact about a specific company, person or security, and tells look-alike names apart |
| Multi-hop | 14 | Combines two or more retrieved facts correctly |
| Technical docs | 11 | Gives the exact version, limit or date from vendor docs, release notes or a CVE record |

13 questions also mirror automated workflows: news briefings (6), CRM enrichment (5) and sourcing signal checks (2).

### bench2: assembled from public sources

104 questions taken from existing benchmarks, picked for the parts that match the fund's work. It tests Linkup on benchmarks it publishes itself. All rows are test split.

| Slice | Rows | Source | Gold |
|---|---|---|---|
| Financial statement and macro figures | 40 | FinSearchComp T2, seeded sample | FinSearchComp's answers |
| Multi-year calculations from filings | 14 | FinSearchComp T3 (company-filing questions only) | FinSearchComp's answers |
| Private-company total funding | 30 | Linkup's GTM funding set, seeded sample | Crunchbase total, correct within ±25% |
| 8-K executive changes (CEO, CFO, GC) | 20 | SEC 8-K filings, Oct 12 to Nov 20, 2026 | The 8-K itself |

bench2 is investing-heavy by design: credit analysts (60 questions), private markets associates (30), macro analysts (12) and in-house counsel (2). The four slices are also its four question types in the scorecards: P1 is 8-K executive changes, P2 statement and macro figures, P3 funding totals and P4 multi-year calculations.

The set is built by `scripts/build_bench2.py`. Sources, licences and what was left out are listed in `gold/bench2/sources/README.md`, and design notes are in `docs/BENCH2.md`.

## Arms

| Arm | What it is |
|---|---|
| `linkup-standard` | Linkup, standard depth |
| `linkup-fast` | Linkup, fast depth |
| `linkup-deep` | Linkup, deep depth |
| `linkup-tuned` | Linkup with per-team depth and domain filters (`configs/linkup_tuned.json`) |
| `linkup-rewritten` | Linkup standard, with the query rewritten to follow Linkup's query guidance |
| `perplexity` | Perplexity Search API |
| `parallel` | Parallel Search API |
| `*-research` | Each vendor's deep-research endpoint, on research questions only (`configs/research_arms.json`) |

## Results so far

bench1, graded (98 questions, one search per question):

| Arm | Correct | p50 search ms | $ / search |
|---|---|---|---|
| parallel | 95 | 2401 | 0.005 |
| perplexity | 95 | 403 | 0.005 |
| linkup-deep | 89 | 7396 | 0.050 |
| linkup-standard | 88 | 1695 | 0.005 |
| linkup-tuned | 82 | 6719 | 0.036 |

bench2 has been run for retrieval but not graded yet. Its scorecard measures whether the gold fact appears in the results, compared against a chance baseline:

| Arm | Evidence found | By chance | Above chance |
|---|---|---|---|
| parallel | 84 / 104 | 26 | 58 |
| linkup-deep | 72 / 104 | 21 | 51 |
| linkup-tuned | 71 / 104 | 22 | 49 |
| linkup-fast | 70 / 104 | 23 | 47 |
| linkup-standard | 69 / 104 | 22 | 47 |
| perplexity | 73 / 104 | 29 | 44 |
| linkup-rewritten | 47 / 104 | 19 | 28 |

Perplexity returned pages that republish the benchmark's own answers (FinSearchComp copies on Hugging Face) on 41 bench2 questions. Those results are removed before scoring.

## Where Linkup does better and worse

Better or level:

- Technical docs and multi-hop questions on bench1: `linkup-standard` got all 11 tech-doc and all 14 multi-hop questions right, level with both competitors.
- 8-K executive changes on bench2: `linkup-standard`, `linkup-fast`, `linkup-deep` and `linkup-tuned` each found the evidence on 18 of 20, level with Perplexity (17) and Parallel (19).
- Clean results: Linkup never returned a page republishing the benchmark's answers. Perplexity did on 41 bench2 questions.
- Above chance on bench2, `linkup-deep` (51) is ahead of Perplexity (44), though behind Parallel (58).
- One point-in-time question on bench1 (INV-H01-PIT) was answered only by `linkup-deep` and `linkup-tuned`.
- Primary sources: `linkup-rewritten` reached the gold source most often of any arm on bench2 (33 of 50).

Worse:

- Overall on bench1, Linkup gets 88 to 89 of 98 against 95 for Perplexity and Parallel. In head-to-head pairs `linkup-standard` was right only where a competitor was also right, while each competitor was right on 7 questions where Linkup wasn't.
- Questions whose answer is that something doesn't exist: "no claims bar date has been set" (INV-H04), "the deal has no go-shop" (INV-H08). Linkup's results led to "couldn't find it" instead of confirming the absence.
- Premium or ratings content: on S&P's downgrade of Mercer (INV-H06), `linkup-standard` and `linkup-deep` didn't find it and `linkup-tuned` found it without the date. Both competitors got it fully.
- Official-source questions on bench1: 24 of 28 for `linkup-standard` against 27 for each competitor.
- Financial statement lookups on bench2: Linkup arms found the number on 21 to 23 of 40, Parallel on 31.
- `linkup-tuned` scored lowest on bench1 (82). It restricts legal and tax searches to allowlisted domains, and legal and compliance fell to 14 of 21. Most of those misses say the results didn't contain the fact, which points to the allowlist cutting out the pages that had it.
- Rewriting queries to name the source document hurt on bench2 (`linkup-rewritten`, 8 of 40 statement lookups). The rewrite pulled up 10-K cover pages and Crunchbase paywall pages instead of pages showing the figure.
- Speed and metadata: `linkup-deep` takes about 7 to 8 seconds per search at 10 times the standard price, and returns no publish dates.

Full scorecards are in `results/`. Only the bench2 scorecard (`results/20261124-222222-bench2-all-retrieval/`) uses the current retrieval scoring. The older retrieval scorecards were built before that change and aren't directly comparable with it.

## Layout

```
scripts/
  run_eval.py           agent loop: a fixed LLM calls one search backend, then a judge grades
  retrieval_run.py      retrieval-only runs: one search per question, no LLM; blinded handoff for grading
  search_backends.py    Linkup, Perplexity and Parallel search clients, normalised to one result format
  research_backends.py  deep-research endpoints for the three vendors
  simpleqa_grader.py    grading rubric (SimpleQA grader plus required-facts rules)
  build_gold.py, build_bench2.py, validate_gold.py
configs/                linkup-tuned config, research arm settings
gold/                   question sets, sources and query rewrites
docs/                   eval design, bench2 notes, vendor due diligence
results/                scorecards from each run
```

## Setup

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env    # add API keys; arms without a key are skipped
```

## Running

Agent eval (needs an Anthropic key for the agent and the judge):

```
.venv/bin/python scripts/run_eval.py --ping        # one test search per backend
.venv/bin/python scripts/run_eval.py --dry-run     # show the plan
.venv/bin/python scripts/run_eval.py --tuned configs/linkup_tuned.json
```

Retrieval-only run, graded afterwards from a blinded handoff folder:

```
.venv/bin/python scripts/retrieval_run.py run --gold bench2 --tuned configs/linkup_tuned.json
.venv/bin/python scripts/retrieval_run.py run --resume runs/<run_id>    # retry failed jobs
.venv/bin/python scripts/retrieval_run.py grade-prompts runs/<run_id>
.venv/bin/python scripts/retrieval_run.py ingest runs/<run_id> --model "<model>"
```

Runs are written to `runs/<run_id>/`. That folder is not committed because it holds raw API responses.

## Notes

- `linkup-tuned` was tuned on the dev split. Report its test-split numbers.
- The research arms didn't finish on bench2: each vendor ran out of credit at a different point, so they can't be compared yet.
- Vendor security and compliance checks are in `docs/VENDOR_DUE_DILIGENCE.md`.

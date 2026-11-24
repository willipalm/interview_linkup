# Search API benchmark: Linkup, Perplexity, Parallel

A harness for comparing search APIs as the retrieval tool behind an internal research assistant at an investment fund. Every arm gets the same questions and the same answering and grading setup. Only the search backend changes.

## Question sets

- **bench1**: 98 questions written for the fund's teams (investing, legal and compliance, tax and HR, tech), including point-in-time variants. See `gold/gold_set.jsonl` and `gold/TAXONOMY.md`.
- **bench2**: 104 questions from public benchmarks plus recent 8-K executive changes: FinSearchComp T2 and T3, Linkup's GTM funding set, and EDGAR 8-Ks. See `docs/BENCH2.md`.

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

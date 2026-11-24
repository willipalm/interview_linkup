# Hard questions: human research worksheet

`gold/hard_worksheet.csv` holds 19 questions that Claude's own search could not settle. Each was checked on 2026-11-24: Claude ran a web search for the answer, and the row was kept only if search found nothing, or found sources that disagree or stop short of the fact asked. `why_hard` records what search turned up, without the values. These are the questions most likely to separate the search APIs, and the Claude-built set under-represents them because it only kept what Claude's own search could answer.

Rows from the previous draft that search could now answer were removed: TPL/EagleRock terms, the Children's Place DIP size and lenders, Python 3.10's EOL date, the Node 26 codename, the AWS DynamoDB outage window, the proposed NYC 2027 wage, Moody's Nvidia rationale, Nvidia's Q3 call supply comments and Gemspring Fund IV's target.

Three rows (`INV-H05`, `INV-H06`, `TAX-H03`, pre-tagged `trap=premium`) are best answered from a licensed source: Octus or Debtwire, S&P, a state tax-conformity tracker. They test whether an API that claims premium content actually gets those answers, and they need someone at the fund with those subscriptions.

Five rows carry a fintech `workflow` tag (`sourcing_signal`, `crm_enrichment`, `news_briefing`; see `gold/TAXONOMY.md`). Leave it as is.

The worksheet gives the question, why it's hard and where to look. It deliberately contains **no candidate answers**, so your research isn't anchored to Claude's.

## Research rules

1. **No AI search.** Don't use Claude, ChatGPT, Perplexity, Linkup, Parallel or Google's AI answers to find the answer, since those are the systems under test or close to them. Use primary sources directly: EDGAR, dockets (PACER, CourtListener, claims-agent sites), regulator pages, vendor advisories, rating-agency sites, and plain Google or Bing results that you open and read yourself.
2. **Primary source or two independent ones.** This is the same bar as the rest of the set. Put the primary source first in `gold_sources`.
3. **If the premise is false** (for example, no Caa1 downgrade happened), keep the row. Set `trap=nonexistent` and `answer_type=refusal`, and write the true state in `gold_answer` (for example, "No; Moody's rating is still X as of <date>").
4. **If it can't be settled**, set `status=drop` and write one line in `verification_notes` saying why. Don't guess.
5. **Premium rows:** write the gold from the licensed source (that's the point), and add the free primary source too if one exists (Form D, the docket exhibit, the IR webcast). Note in `verification_notes` which facts are only in the licensed source. The judge uses that to tell "couldn't reach it" from "got it wrong".
6. **Record the date.** Answers on `breaking` rows expire 7 days after `as_of`.

## Columns

The worksheet has every column of `gold/gold_set.csv`, in the same order, followed by four research-only columns (`status`, `relates_to`, `why_hard`, `where_to_look`). Pre-filled and fixed: `split=test`, `origin=human`. Leave `expires_at` blank: the build computes it from `as_of` and `freshness`. Leave `point_in_time` blank unless you are writing a point-in-time twin.

## Columns you fill in

| Column | What to put |
|---|---|
| `status` | `todo` (default), `keep` or `drop` |
| `trap` | blank, or `stale` / `ambiguous` / `paywall` / `nonexistent` / `contested` (credible sources disagree, so list both sides in `required_facts`) / `premium` (pre-filled on the licensed-source rows) |
| `answer_type` | pre-filled; change it if needed (`fact`, `number`, `date`, `list`, `status`, `refusal`) |
| `gold_answer` | short canonical answer |
| `required_facts` | every fact needed to count as CORRECT, separated by ` \| ` |
| `acceptable_variants` | other equivalent phrasings, separated by ` \| ` (optional) |
| `gold_sources` | URLs, primary first, separated by ` \| ` |
| `authoritative_domains` | domains whose citation counts as authoritative, e.g. `sec.gov \| uscourts.gov` |
| `as_of` | the date you researched it, `YYYY-MM-DD` |
| `verified_by` | your name or initials (anything except `claude-research`) |
| `verification_notes` | caveats and what you checked; the "why hard" text is appended automatically |

Don't change `id`, `team`, `pattern` or `workflow`. You can reword `query` if it reads unnaturally, as long as it doesn't contain the answer (the validator checks this).

## Rebuild

```
python scripts/build_gold.py
python scripts/validate_gold.py gold/gold_set.jsonl --csv gold/gold_set.csv
```

Rows marked `keep` are added with `origin=human` and `split=test`. They're never used for tuning, and the 15-row dev split stays as it is. The build stops if a `keep` row is missing a required column.

## Reporting

Report results separately for `origin=claude` and `origin=human`. If Linkup's lead (or deficit) holds on both, the result is robust. If it shows up only on the Claude-built rows, the gold set was biased.

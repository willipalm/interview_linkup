# Search eval design: Linkup vs Perplexity vs Parallel

**Audience:** the fund's Head of Engineering and platform team, plus Linkup FDE/engineering.
**Decision it supports:** which search API to plug into the internal assistant, and how to configure it per team.
**Gold set:** `gold/gold_set.jsonl` (81 rows, 4 personas, built 2026-11-23: 71 questions plus 10 point-in-time twins; 11 rows are also tagged with a fintech `workflow`), plus up to 20 human-researched rows from `gold/hard_worksheet.csv`. See `gold/TAXONOMY.md`.
**Vendor security and compliance:** `docs/VENDOR_DUE_DILIGENCE.md`. These are document checks, not queries.

## 1. What we measure, and why it's fair

The assistant is an open-source chat UI on top of an LLM. Search is a **tool** the LLM calls. So the fair test holds the LLM, prompt and tool contract constant, and swaps **only** the search backend.

```
query ─► fixed LLM agent (same model, system prompt, effort, max 6 tool calls)
              │  search(query) -> [ {url, title, snippet/content, published_date} x k ]
              ▼
         ┌──────────────┬────────────────────┬──────────────────┐
         │ Linkup       │ Perplexity Search  │ Parallel Search  │   ← the only variable
         └──────────────┴────────────────────┴──────────────────┘
              ▼
         final answer + cited URLs ─► judge (frozen rubric) ─► scores
```

### Arms

| Arm | Backend config | Purpose |
|---|---|---|
| A1 `linkup-standard` | `depth=standard`, `outputType=searchResults`, defaults | Out-of-the-box Linkup |
| A2 `linkup-deep` | `depth=deep`, `outputType=searchResults` | Linkup agentic retrieval |
| B `perplexity-search` | Perplexity Search API, defaults | Competitor |
| C `parallel-search` | Parallel Search API, defaults | Competitor |
| T `linkup-tuned` | Per-team config tuned **on dev split only** (see §5) | "How to set it up so users feel the difference" |
| N `linkup-native` | Linkup-specific `linkup_search` tool: the agent picks `depth` (fast/standard/deep), `from_date`/`to_date`, `prioritize_domains` and `include_domains` per call, with a system-prompt section taken from Linkup's best-practices and for-agents docs. Team defaults in `configs/linkup_native.json` | "Linkup used the way Linkup recommends". Compare with A1 to see what the best practices add. The fair vendor comparison is against Perplexity and Parallel native arms built the same way from their own docs |

**Gold labels never reach the agent or the search call.** Arms may use the user's team (the fund knows it from the login), but never `pattern`, `trap` or `freshness`. An earlier tuned rule that set a 30-day `fromDate` on P1 rows was removed for this reason; in linkup-native the agent decides the date window from the question text.

**Domain priority without a hard filter.** Linkup's filtering tutorial documents a `<guidance><priority>` block in the query. In our probes (2026-11-23) it didn't change standard-depth results. A plain instruction appended to the query ("Prioritise official primary sources: sec.gov, federalregister.gov.") did: the top 8 results became sec.gov or federalregister.gov. `fast` ignores instructions and its results got worse, so the line is added only at standard and deep (`Linkup.PRIORITY_LINE` in `scripts/search_backends.py`).

**Held constant across arms:** LLM model and version (Claude Sonnet 5.5, `claude-sonnet-5-5`, standing in for the fund's production model), system prompt, effort (`medium`; Sonnet 5.5 doesn't accept a temperature setting, so runs aren't fully deterministic, which is why §4 runs each arm twice), max 6 search calls per query, top-k = 10 results, roughly 1,500 characters of content per result (truncated the same way for every arm), same region (us-east), same time window.

**The agent sees only `query`** (plus "today"). `intent_note`, `gold_answer`, `required_facts` and `verification_notes` go to the judge only. Several intent notes hint at the answer (e.g. "before the Nov 12 resignation"), so sending them to the agent would leak it.

**The agent's "today" for each row:** the run date, or `point_in_time` on twin rows. It goes in the system prompt, identical for every arm. On twin rows the arm also passes `point_in_time` as its upper date bound where the API has one (§5b). Parallel's Search API has no upper bound (only `source_policy.after_date`; checked 2026-11-24), so on twin rows the harness also appends "As of <date>: only use sources published on or before that date." to every search query, identically for every arm (`--pit-query all`, the default). The query text stays the same across arms and only each backend's own filter differs. Perplexity has `search_before_date_filter` and Linkup has `toDate`.

Optional reference arm (not a candidate): the same LLM with its native web search. Run it only if the Head of Eng wants a like-for-like answer to the "comparable to Claude" question.

## 2. Metrics (per query, per arm)

| Metric | Definition | Why the fund cares |
|---|---|---|
| **Correctness** (headline, SimpleQA grading) | Each answer is graded CORRECT / INCORRECT / NOT_ATTEMPTED with the SimpleQA grader (openai/simple-evals). CORRECT also requires **every** `required_facts` item, with no partial credit. Report % correct, % incorrect, % not attempted, accuracy when attempted (correct / attempted) and SimpleQA's F1. | Users judge on whether the answer is right. A half-right answer still produces a wrong memo, and a confident wrong answer is worse than "couldn't find it", which the three-way split shows. |
| **Source authority** | Share of cited URLs whose domain is in `authoritative_domains`; plus `gold_source_hit` = any cited URL matches a `gold_sources` URL/domain. | Legal, Tax and Compliance can't rely on content-farm sources. |
| **Citation support** | Judge checks that the cited page actually supports the key claim (sampled: fetch the cited page). | Catches answers that cite a source which doesn't say what's claimed. |
| **Trap handling** | On `trap` rows: correct refusal or status, or avoided the stale value. | Shows whether the API is fresh and doesn't make things up. |
| **Contested: both sides** | On `trap=contested` rows, CORRECT only if every side in `required_facts` appears. Also report the share of answers that *collapse to one side*. | A one-sided answer on a live legal or macro question is worse than no answer. |
| **Premium-source reach** | On `trap=premium` rows (human worksheet), graded CORRECT / NOT_ATTEMPTED (honest gap: "couldn't find it", or gave only the free part) / INCORRECT (made-up or wrong figure). | Tests whether premium-content claims hold up. An honest gap is acceptable; inventing an answer isn't. |
| **Result metadata completeness** | From the raw search results, not the answer: share of results with a URL, title, a publisher or site name (derived from the URL if the API has no field for it) and a publish date. No gold needed. | Every result has to be a named, citable source the user can check. |
| **Point-in-time accuracy** | Correctness on `point_in_time` twin rows. Answering the post-change value is graded as a leak. | Research "as of" a past date without look-ahead, e.g. for memos and backtests. |
| **Date-filter accuracy** | Share of returned results whose real publish date falls inside the requested window. Check 20 per arm by hand, because pages edited after publication show an old date with new content. | Tells you whether the filter can be trusted or only looks right. |
| **Freshness lift** | Correctness on P1 rows when the agent sets a lower date bound itself (linkup-native) minus without (linkup-standard). | Whether the date filter helps on news monitoring. |
| **Latency** | p50 / p95 per search call and per end-to-end answer. | User experience in chat. |
| **Cost per correct answer** | (search fees + LLM tokens) / # CORRECT | The ROI figure for the decision. |

## 3. Judge

- **Model:** Claude Opus 5.5 (`claude-opus-5-5`, effort high, fixed JSON output): a different model from the agent, though the same family. If the fund has another provider's key, a cross-family judge on a sample is a useful check. Rubric frozen before any results are seen; the judge never sees which arm wrote the answer.
- **Prompt:** the SimpleQA grader template, verbatim (MIT, `scripts/simpleqa_grader.py`), followed by this benchmark's override rules, which win where they conflict.
- **Inputs:** query (as SimpleQA "question"), `gold_answer` ("gold target"), agent answer; then in the overrides: `intent_note`, the as-of date, `required_facts`, `acceptable_variants`, `verification_notes` and trap type.
- **Output (JSON, structured output):** `{"grade": "A|B|C", "missing_facts": [...], "contradictions": [...], "stale_or_leaked": bool, "one_sided": bool, "reason": "..."}` with A = CORRECT, B = INCORRECT, C = NOT_ATTEMPTED (the SimpleQA mapping). JSON replaces SimpleQA's bare-letter reply because its letter regex mis-parses replies like "CORRECT".
- **SimpleQA rules kept:** hedging is fine if the gold is fully there and nothing contradicts it; a hedged *wrong* statement is INCORRECT; missing information with no contradiction is NOT_ATTEMPTED; numbers must match to the gold's last significant figure.
- **Overrides:** every required fact is needed for CORRECT (this replaces SimpleQA's "only the information in the question"); a stale or post-as-of value counts as a contradiction; on `contested` rows a one-sided answer is INCORRECT; on `nonexistent` traps an invented answer is INCORRECT; on `ambiguous` traps the wrong entity is INCORRECT.
- **Human audit:** 20 random judgments plus every query where the arms disagree. If humans disagree with the judge more than twice, fix the rubric and regrade **all** arms.

## 4. Statistics: how to read the numbers honestly

- Test split n ≈ 57. A 95% Wilson CI at p = 0.6 is about ±12 points. **Overall gaps under ~15 points aren't significant on their own.**
- So the main read is **paired**: for each arm pair, count queries where only A is correct vs only B is correct (McNemar test).
- Slice by team, pattern (P1–P5), freshness, workflow (sourcing signal / CRM enrichment / fintech news briefing), trap type (incl. `contested`, `premium`), point-in-time twins vs the rest, and **origin** (`claude` vs `human`). The Claude-built rows only include questions Claude's own search could answer, so a result that holds only on `origin=claude` is suspect. The `human` rows are the hard questions researched without AI search (`gold/HARD_QUESTIONS.md`). Slices are directional evidence ("where Linkup wins and loses"), not proof.
- Fix in advance: first-run results only, no best-of-N, same rule for every arm.
- Run each arm **twice** on different days. Report run-to-run variance; any query that flips between runs is flagged unstable.

## 5. Tuning protocol (arm T): dev split only

Allowed knobs (Linkup): `depth`; `includeDomains` per team (e.g. Legal/Tax: sec.gov, irs.gov, federalregister.gov, eur-lex.europa.eu, fincen.gov, ftc.gov; Investment distressed: sec.gov, claims-agent sites); `fromDate` for queries marked P1; the query-rewrite instruction in the tool description.

Process: iterate on the 15 dev rows only → freeze config → run once on test → report alongside A1/A2/B/C. Never look at test rows while tuning.

## 5b. Capability tests: source control and date filters

These compare what each API lets the fund *configure*, not only default quality. Parameters are from each vendor's API reference, read on 2026-11-23. Re-check them before the run.

| Capability | Linkup `/v1/search` | Perplexity Search API | Parallel Search API |
|---|---|---|---|
| Restrict to domains | `includeDomains` (up to 100) | `search_domain_filter` (up to 200, include and exclude mixed) | `source_policy.include_domains` (200 across include and exclude) |
| Exclude domains | `excludeDomains` | `-domain` entries in `search_domain_filter` | `source_policy.exclude_domains` |
| Soft preference (boost, not filter) | Not documented | Not documented | Not documented; docs suggest steering through the `objective` text |
| Lower date bound | `fromDate` | `search_after_date_filter`, `last_updated_after_filter`, `search_recency_filter` | `source_policy.after_date` |
| Upper date bound | `toDate` | `search_before_date_filter`, `last_updated_before_filter` | **None documented** |
| Index snapshot ("as of" time travel) | Not documented | `snapshot_as_of` | `fetch_policy.as_of` (contact sales) |
| Result fields | `name`, `url`, `content`, `favicon`, `publishedAt` | `title`, `url`, `snippet`, `date`, `last_updated` | `url`, `title`, `publish_date` (estimated), `excerpts` |

What this means:
- **No API has a real "weight this source higher" option.** All three only offer hard include and exclude lists. So "prioritise our sources" means either restricting (risky: answers outside the list disappear) or steering through the query or prompt. Test both.
- **Point-in-time is not a guaranteed Linkup win.** Perplexity has before-date filters on both publish and last-updated dates, plus an index snapshot option, which could beat a publish-date-only filter on edited pages. Parallel has no upper bound, so its twin rows run with the prompt date only, which is reported as a capability gap. Let the twin rows decide.

**Source-control test.** For each team, use one preferred-domain list (e.g. Legal/Tax: sec.gov, irs.gov, federalregister.gov, eur-lex.europa.eu, fincen.gov, ftc.gov) and one exclude list (content farms and SEO aggregators seen in the default runs). Run the test rows of that team's P2 queries three ways on each API: default, prompt steering only ("prefer official sources"), and hard include. Report:
- **preferred-domain share** of results and of citations;
- **correctness change** compared with default: hard include often loses answers that only exist off-list;
- **coverage loss**: queries that return zero useful results under hard include.

**Date-filter test.** Run every twin row two ways per arm. First, with "today" in the prompt plus the API's upper date bound. Second, with "today" in the prompt only, which shows what the filter adds. Run Perplexity a third time with `snapshot_as_of`. Report point-in-time accuracy, leak rate and date-filter accuracy per arm. For freshness lift, compare linkup-native (where the agent sets `from_date` itself) with linkup-standard on P1 rows; the harness never sets a lower bound from the P1 label.

## 6. End-user layer (supports "end-user scoring")

The fund will decide partly on how users rate the answers, so we add a blind preference study:
- 2–3 users per team, ~10 test queries each from their own persona.
- Show the answers from 2 arms side by side, anonymized and in random order. Ask "Which would you rather act on?" plus a 1–5 trust rating.
- Report win rate per team. This is the number the rollout owners will care about most.

## 7. Runbook

1. `python scripts/validate_gold.py gold/gold_set.jsonl --today <run date>`, then re-verify every row flagged EXPIRED and update `scripts/build_gold.py`.
   Runner (`scripts/run_eval.py`, keys in `.env`): `--ping` checks the keys, the default runs the dev split, `--tuned configs/linkup_tuned.json` adds arm T, `--no-date-filter` runs the twins with the prompt date only, and `--split test` runs the frozen test. Output goes to `runs/<run_id>/` (`agent.jsonl`, `judgments.jsonl`, `scorecard.md`).
2. Run each arm over **all 72 rows** and log raw results as JSONL. Record `run_id`, arm, query id, tool calls with request/response, answer, citations, latency, tokens and cost.
3. Judge all rows. Report on **test rows only** for the headline; dev rows are reported separately.
4. Human audit (§3), then compute metrics (§2) and stats (§4).
5. Produce the report (§8). Commit the harness, gold set, raw logs and report together, so every number traces back to its inputs.

## 8. Report template (what the Head of Eng gets)

1. **One-line verdict per team:** where Linkup is better, tied, or worse, with paired win/loss counts.
2. **Scorecard table:** arms × {correctness, authority, trap handling, p50 latency, cost per correct}, with CIs.
3. **Slices:** by team, pattern and freshness.
4. **Where Linkup loses:** every query Linkup gets wrong that another arm gets right, with a root cause (retrieval miss, stale index, wrong entity, LLM synthesis error). These go back to Linkup engineering.
5. **Recommended config per team** (arm T settings) and the lift it delivers over default.
6. **Methodology appendix:** everything held constant, known limitations (n, vendor-run, live-web drift), build dates.

## 9. Known limitations (state them up front)

- Security and compliance aren't measured by this benchmark. They're checked on documents in `docs/VENDOR_DUE_DILIGENCE.md`, and vendor claims (including Linkup's) count only with evidence.

- 72 queries is a quick read, not a leaderboard. Use it to decide on direction, then expand to 200+ from real assistant logs after rollout starts.
- Most gold rows were researched with Claude's web search, which favours questions that search can answer and tilts any comparison with Claude native search. Mitigation: the human-researched hard rows, reported as their own slice.
- The gold set was researched by the Linkup side. Mitigations: dev/test split, a frozen rubric, the fund's SMEs reviewing gold rows, and every source URL published for audit.
- Live-web answers drift. `breaking` rows expire after 7 days and must be re-verified before each run.
- Some gold rows rely on secondary sources and are marked so in `verification_notes`. They must be checked against the primary source before the set is frozen.

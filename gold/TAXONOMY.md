# Gold set taxonomy

Build date: 2026-11-23. Scope: web search inside a ~200-person NY investment fund's internal AI assistant.

## Personas (rollout order)

| Code | Persona | Sub-teams | Target n | Why they search |
|---|---|---|---|---|
| `tech` | Tech / Engineering | platform, data, security | 16 | Versions, changelogs, CVEs, API limits, vendor security posture. First to roll out, so they are the first users the assistant has to win over. |
| `legal_rc` | Legal + Risk & Compliance | legal, compliance, risk | 18 | Primary-source rules and deadlines, enforcement actions, sanctions, court rulings. Wrong or secondary-source answers are a liability. |
| `tax_hr` | Tax + HR (corporate functions) | tax, hr | 14 | IRS / state guidance, annual limits and thresholds, employment-law changes. Answers change every year, so stale indexes fail. |
| `invest` | Investment | credit, distressed, private_markets, macro | 24 | Entity facts, fresh deal and restructuring news, rating actions, docket details, multi-step synthesis. Drives the ROI case. |

## Usage patterns (cross-team)

| Code | Pattern | What good looks like |
|---|---|---|
| `P1` | Freshness / news monitoring | Finds the event from the last days or weeks, with the right date, and doesn't return an older one. |
| `P2` | Official source / regulatory | Answer grounded in a primary source (sec.gov, irs.gov, federalregister.gov, eur-lex, court/claims-agent sites, company IR). |
| `P3` | Entity lookup | Correct structured fact about a specific company, person, fund or security. Disambiguates names that look alike. |
| `P4` | Multi-hop / synthesis | Combines 2+ retrieved facts correctly. |
| `P5` | Technical / documentation | Exact version, limit, date or identifier from vendor docs, release notes or a CVE record. |

Each query has one **primary** pattern. Multi-hop is also captured by `hops`.

## Fintech workflows (`workflow`)

Linkup's /search also runs inside three automated workflows. Rows shaped like them carry a `workflow` tag on top of their persona, and the scorecard slices on it. Untagged rows are chat Q&A.

| Code | Workflow | What the question looks like | What good looks like |
|---|---|---|---|
| `sourcing_signal` | Signal qualification at sourcing | A company plus a claimed signal (a round, an IPO filing) | Confirms or rejects the signal for the right company, with the date and a citable source. |
| `crm_enrichment` | CRM enrichment | A company name or domain, asking for record fields (last round, valuation, lead, owner, CEO) | Current values, not the stale ones; the right entity when names collide. |
| `news_briefing` | Weekly fintech news briefing | A fintech event from the last week or two (earnings, M&A, charters, rules) | The latest status, both sides where disputed, dated correctly. |

These rows test answers one question at a time. They don't measure briefing recall (share of a week's events found) or CRM fill rate across many fields; those need their own suites.

## Freshness classes

| Class | Meaning | `expires_at` |
|---|---|---|
| `static` | Will not change (historical fact). | null |
| `slow` | Changes at most yearly (annual limits, rule text). | as_of + 180d |
| `volatile` | Can change within weeks (latest release, current officeholder, latest data print). | as_of + 30d |
| `breaking` | Event in the last ~30 days, which an index without fresh crawling will miss. | as_of + 7d |

Rows past `expires_at` must be re-verified before a run (`validate_gold.py` flags them).

## Traps (`trap`)

- `stale`: the fact changed recently, so an outdated index returns the old value.
- `ambiguous`: entity name collides with another entity, so the right one must be picked.
- `paywall`: the event mostly shows up in paywalled press, but a free primary source exists.
- `nonexistent`: the premise is false or the thing hasn't happened yet. The correct answer says so instead of making something up.
- `contested`: credible sources or courts disagree, or the outcome is still open. `required_facts` lists every side, so an answer that collapses to one side is INCORRECT.
- `premium`: a licensed source (rating research, transcripts, Octus or Debtwire, PitchBook, tax trackers) answers it best. These rows are human-researched only (`gold/hard_worksheet.csv`).

## Point-in-time twins

Most `stale` traps have a twin (`<ID>-PIT`) asking the same thing as of `point_in_time`, a date before the change. Other rows can have one too (INV-18-PIT). Pick twins whose old value lives on dated pages that aren't rewritten later (earnings releases, 8-Ks, press releases, news). Avoid facts mostly found on explainer or timeline pages that get updated in place: those keep their old publish date with new text, so the date filter can't exclude them. LRC-03-PIT was dropped for that reason. The gold is the *old* value, and returning the new value counts as a leak. Twins are `static` (a past state doesn't change), inherit their parent's split, and let the date filters be graded instead of trusted (see `docs/EVAL_DESIGN.md` §5b).

## Mix targets (checked by the validator)

- ≥ 30% `volatile` + `breaking`
- ≥ 30% `P2` or rows with non-empty `authoritative_domains` that are official (`.gov`, `europa.eu`, courts, regulators)
- ~25% `hops >= 2`
- 8–16 classic trap rows (stale / ambiguous / paywall / nonexistent), ≥ 4 `contested`, ≥ 6 point-in-time twins
- ~15 `dev` rows (Linkup config tuning only) / rest `test` (reported). The dev list is frozen in `build_gold.py` (`DEV_IDS`), and new rows go to test.

## Field definitions (`gold_set.jsonl`)

| Field | Type | Notes |
|---|---|---|
| `id` | str | `<TEAM>-<NN>`, e.g. `INV-07` |
| `split` | `dev`\|`test` | stratified by team |
| `team` | enum | `tech`, `legal_rc`, `tax_hr`, `invest` |
| `sub_team` | str | e.g. `distressed`, `security`, `tax` |
| `persona_role` | str | who would type this, e.g. "credit analyst" |
| `pattern` | `P1`..`P5` | primary usage pattern |
| `query` | str | exactly as a user would type it (terse or conversational) |
| `intent_note` | str | what the user actually needs; helps the judge |
| `answer_type` | enum | `fact`, `number`, `date`, `list`, `status`, `refusal` |
| `gold_answer` | str | short canonical answer |
| `required_facts` | list[str] | every one must be present for CORRECT (no partial credit) |
| `acceptable_variants` | list[str] | equivalent phrasings / formats |
| `gold_sources` | list[url] | where the gold was verified (primary first) |
| `authoritative_domains` | list[str] | domains whose citation counts as "authoritative" |
| `as_of` | date | when the gold was verified |
| `freshness` | enum | see above |
| `expires_at` | date\|null | re-verify after this date |
| `hops` | int | 1 or 2+ |
| `difficulty` | `easy`\|`med`\|`hard` | |
| `trap` | null\|enum | `stale`, `ambiguous`, `paywall`, `nonexistent`, `contested`, `premium` |
| `verified_by` | str | `claude-research` until a human signs off |
| `verification_notes` | str | caveats, conflicting sources, judgment calls |
| `point_in_time` | date\|null | twins only: the date the question is asked "as of". The harness sets the agent's today and the upper date bound to it |
| `workflow` | null\|enum | `sourcing_signal`, `crm_enrichment`, `news_briefing` (see above) |
| `origin` | `claude`\|`human` | who researched the gold answer. `human` rows come from `gold/hard_worksheet.csv` (see `HARD_QUESTIONS.md`) and are always `test` |

## Build rules

1. **Keep-gate** (from OB-News-Websearch): a query that contains its gold answer (or a variant of it) is dropped.
2. **Verification bar:** one primary official source, or two independent reputable sources.
3. **No public-benchmark items** (SimpleQA, FreshQA, FinSearchComp, OB-*), so no answer key can leak.
4. **Realistic phrasing:** keep typos, shorthand and keyword-style queries. Don't clean them up to look like benchmark questions.
5. **Dev/test separation:** only `dev` rows may be looked at while tuning Linkup parameters.

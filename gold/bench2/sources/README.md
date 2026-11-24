# Benchmark 2 sources

`scripts/build_bench2.py` builds `../bench2_set.jsonl` from these files. Copied on 2026-11-24; unmodified except where noted.

| File | From | Licence | Used for |
|---|---|---|---|
| `finsearchcomp_t2_global.csv`, `finsearchcomp_t3_global.csv` | FinSearchComp (ByteDance Seed; arXiv 2509.13160; dataset at huggingface.co/datasets/ByteSeedXpert/FinSearchComp), as packaged in github.com/LinkupPlatform/linkup-finance-benchmark @ `036246366f3e` | CC BY 4.0 (dataset) | `INV-FSC2-*` (40 of 119, seeded sample: 28 company-filing, 12 macro/market) and `INV-FSC3-*` (the 14 of 84 built on company filings) |
| `linkup_gtm_funding_golden_set.csv` | github.com/LinkupPlatform/Search-Benchmarks-on-GTM-Usecases @ `f8d9228f81d3`, `company/research-evals/funding-retrieval/data/golden_set.csv` (Crunchbase totals, committed 2026-07-10) | MIT | `INV-FUND-*` (30 of 93, seeded sample). The file also holds each vendor's answer from Linkup's own run; the builder reads only `company`, `hq`, `founded` and `golden`. |
| `edgar_8k_exec_changes.json` | Written for this eval from SEC 8-K Item 5.02 filings (public domain), found with EDGAR full-text search and read 2026-11-24 | — | `INV-EXEC-*`, `LRC-EXEC-*` (20 rows) |

Left out of Linkup's benchmark hub (github.com/LinkupPlatform/linkup-benchmarks), and why:
- **GTM people (enrichment, freshness, meeting briefs):** randomly sampled private individuals matched by LinkedIn URL. Not a task the fund does, and sending their personal data to three vendors has no business purpose here. The freshness idea is kept, rebuilt on public officers from 8-K filings.
- **GTM company research (offers, pain/solution, case studies, CTAs):** sales-prospecting sections, judged without a gold answer.
- **RedlineBench:** an agentic contract-redlining benchmark that needs Crosby's harness and GPT-5.5, with no Perplexity or Parallel arm.
- **General consumer & places:** not a fund use case.
- **FinSearchComp T3 market-data questions** (prices, volumes, turnover, FX, index constituents): a fund answers those from its market-data terminal, not web search.

# Vendor due diligence: Linkup vs Perplexity vs Parallel

**Owner:** the fund's security / vendor-risk team. **Status:** public claims collected 2026-11-23. Nothing here is verified until the evidence column is filled in.

A query can't test any of this, so it isn't in the gold set. Each row is a vendor claim, and it counts only once the fund holds the evidence: the report, the contract clause or the signed DPA. That applies to Linkup too. Note that Linkup's own docs contradict a common Linkup talking point (see ZDR below).

## 1. What each vendor states publicly

| Item | Linkup | Perplexity (API) | Parallel |
|---|---|---|---|
| SOC 2 | Type II; report in Trust Center ([trust.linkup.so](https://trust.linkup.so/)) | Type II; report in Trust Center ([trust.perplexity.ai](https://trust.perplexity.ai/)) | "SOC-II Type 1 and Type II certified as of April 2025"; report on request via partnerships@parallel.ai ([FAQ](https://docs.parallel.ai/resources/faqs)) |
| Zero Data Retention | **Not default.** "ZDR can be requested on demand. It is not enabled by default" ([data privacy](https://docs.linkup.so/pages/security-and-privacy/data-privacy)). Some Linkup blog posts say "on by default", which contradicts the docs. | **Not default.** "ZDR is available only to eligible customers through an account-level configuration under a written agreement"; the Embeddings API is ZDR by default ([privacy & security](https://docs.perplexity.ai/docs/resources/privacy-security)) | Enterprise plans "with zero data retention"; EU endpoint ZDR by default. The US default isn't stated ([FAQ](https://docs.parallel.ai/resources/faqs), [EU residency](https://docs.parallel.ai/resources/eu-data-residency)) |
| Training on API queries | Not stated in the security docs | "Does not use Customer Content to train generative AI models" (API terms) | Standard terms: "may use inputs and outputs, not linked to any individual, to train and improve" its models, except under enterprise ZDR and on the EU endpoint |
| GDPR / DPA | GDPR Art. 28 DPA, signed via DocuSign | DPA ([perplexity.ai/hub/legal/dpa](https://www.perplexity.ai/hub/legal/dpa)); GDPR not named on the page | DPA reflects the EU residency commitments; GDPR not named |
| Data residency | US, EU, Canada and APAC infrastructure. "Local query processing is not guaranteed" by default; guaranteed locality is enterprise only | Not stated | US by default; EU endpoint (enterprise only; Search and Extract only) |
| BYOC / VPC | BYOC "for selected high-tier partner deployments"; index and processing run in the customer's environment | Not stated | "Private-cloud and on-prem options … for qualified enterprise customers" |
| Other | ISO 27001 and "HIPAA compliant" listed; TLS 1.2+ and AES-256; incident notice within 72h | 2025 HIPAA gap assessment (not a compliance claim); CAIQ-Lite | TLS 1.2+, encryption at rest in US data centres |

Sources: [Linkup security & compliance](https://docs.linkup.so/pages/security-and-privacy/security-compliance), [Linkup overview](https://docs.linkup.so/pages/security-and-privacy/overview), [Perplexity privacy & security](https://docs.perplexity.ai/docs/resources/privacy-security), [Parallel FAQ](https://docs.parallel.ai/resources/faqs). Parallel's Trust Center ([trust.parallel.ai](https://trust.parallel.ai)) didn't render its content when fetched.

## 2. Checklist: get evidence for every vendor

| # | Question | Why the fund cares | Evidence to obtain | Linkup | Perplexity | Parallel |
|---|---|---|---|---|---|---|
| 1 | Current SOC 2 Type II: audit period, auditor, scope covers the search API, exceptions | Baseline vendor-risk requirement | Report under NDA; bridge letter if the period has ended | | | |
| 2 | Are query text and results retained? How long, where, and who can access them? | Queries reveal positions, deals and counterparties: material non-public information (MNPI) risk | ZDR clause **in the contract or order form**, not a blog post | | | |
| 3 | Are queries or results used for training or product improvement? | The same MNPI risk | Contract clause with an opt-out or prohibition | | | |
| 4 | Where are queries processed? Can US-only processing be guaranteed? | Regulatory and contractual data-location commitments | Residency clause; list of regions | | | |
| 5 | Subprocessors (LLM providers, index, crawling, cloud) | Queries may pass through third parties | Current subprocessor list and change-notice terms | | | |
| 6 | BYOC / VPC deployment: availability, minimum contract, what still leaves the VPC (e.g. live crawling) | Strongest MNPI control | Architecture doc and pricing | | | |
| 7 | DPA, GDPR and NY SHIELD Act coverage | Legal and compliance sign-off | Signed DPA | | | |
| 8 | Logging, audit trail, SSO and API-key controls | Internal access governance | Admin docs or a demo | | | |
| 9 | Incident notification window and breach history | Vendor-risk policy | Contract clause; disclosure | | | |
| 10 | Pen-test summary and vulnerability disclosure | Security assurance | Latest pen-test letter | | | |
| 11 | SLA (uptime, latency) and rate limits at ~200 users | Rollout capacity | SLA in the order form | | | |
| 12 | Content licensing: is premium content in results licensed for the fund's internal use? | Copyright / licensing exposure | Terms covering premium sources | | | |

Fill each vendor column with **Yes / No / Partial + link to the evidence**. Any "No" on items 2–4 for a vendor is a blocker for the Investment team's rollout, whatever its benchmark score.

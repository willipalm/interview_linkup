# Claude Code task: rewrite queries for Linkup (`bench2`)

`gold/rewrites/bench2_tasks.jsonl` holds 104 questions as fund users typed them (id, team, question). Write one rewritten query per line to
`gold/rewrites/bench2.jsonl`: `{"id": "...", "q": "..."}`. These feed the `linkup-rewritten` arm (Linkup standard depth), which tests
whether following Linkup's query guidance helps. Work **blind**: don't open the gold files, `runs/`, or search the web,
and don't use what you know about the answer. Ideally use a fresh session.

Linkup's guidance for standard depth (docs.linkup.so, search best practices), which the rewrite must follow:
- Standard depth follows natural-language instructions literally, so write the query as a retrieval instruction.
- Name the evidence to retrieve instead of asking for an answer: the document types and sources that would hold it
  (e.g. the company's 8-K or press release, the 10-K, the regulator's rule page, the court docket, the vendor's
  release notes), the full entity name (and ticker when the question gives it or it's unambiguous), and the fields
  to extract.
- **No dates or date ranges in the text** ("as of", "in 2026", "latest as of ..."): the harness sends the date bound
  as `toDate`. Keep relative words the user wrote ("current", "latest", "now") and any period the question itself
  asks about (e.g. "fiscal year 2019", "Q3 FY27"), since those identify the fact, not a search window.
- Don't add facts that could be the answer: no names, numbers, outcomes or dates of the event you think happened.
  If you recognise the answer, still write the query as if you didn't.
- One query, at most ~60 words. Keep the user's intent and scope; don't add sub-questions.

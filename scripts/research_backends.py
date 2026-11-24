"""Deep-research endpoints behind one interface: submit a question, poll until done, return the vendor's answer.

Each backend returns:
    {"answer": str, "sources": [{"url", "title", "published_date", "snippet"}], "latency_ms", "request",
     "job_id", "status", "fee_usd", "raw"}

Endpoints and fields from each vendor's docs, read 2026-11-24:
  Linkup      POST /v1/research, GET /v1/research/{id}            Bearer  (pending|processing|completed|failed)
              body: q, outputType=sourcedAnswer, mode (answer|auto|investigate|research), reasoningDepth (S|M|L|XL)
              price per successful call: S $0.25, M $0.50, L $1.50, XL $2.50
  Parallel    POST /v1/tasks/runs, GET /v1/tasks/runs/{id}, GET /v1/tasks/runs/{id}/result     x-api-key
              body: input, processor, task_spec.output_schema {type: text}; answer in output.content,
              citations in output.basis[].citations[] {url, title, excerpts}
              price per run: lite $0.005, base $0.01, core $0.025, core2x $0.05, pro $0.10, ultra $0.30,
              ultra2x $0.60, ultra4x $1.20, ultra8x $2.40
  Perplexity  POST /v1/agent (background: true), GET /v1/agent/{id}     Bearer
              body: input, effort (fast|low|medium|high|xhigh|ultra); answer in the output item of type "message"
              (content[].type == "output_text"), sources in the item of type "search_results"; actual cost in
              usage.cost.total_cost (no per-request list price). Sonar chat completions ended 2026-09-27.

The question is sent as typed, identically to every vendor. Research rows are never point-in-time rows, so no date
filters are sent.
"""
from __future__ import annotations

import os
import time

import httpx

HTTP_TIMEOUT_S = 60.0
LINKUP_RESEARCH_FEE = {"S": 0.25, "M": 0.50, "L": 1.50, "XL": 2.50}
PARALLEL_TASK_FEE = {"lite": 0.005, "base": 0.01, "core": 0.025, "core2x": 0.05, "pro": 0.10, "ultra": 0.30,
                     "ultra2x": 0.60, "ultra4x": 1.20, "ultra8x": 2.40}
PARALLEL_TEXT_SPEC = ("Answer the question. Lead with the direct answer, then the key supporting facts with dates. "
                      "Say plainly if the sources don't settle it.")


class ResearchError(Exception):
    pass


class ResearchBackend:
    name = "base"
    key_env = ""
    poll_s = 5.0
    max_wait_s = 3600.0

    def __init__(self, **opts):
        self.opts = opts
        self.key = os.environ.get(self.key_env, "").strip()

    @property
    def available(self) -> bool:
        return bool(self.key)

    def _req(self, method, url, **kw):
        for attempt in range(4):
            try:
                r = httpx.request(method, url, headers=self._headers(), timeout=HTTP_TIMEOUT_S, **kw)
            except httpx.HTTPError as e:
                if attempt == 3:
                    raise ResearchError(f"{self.name}: network error: {e}") from e
                time.sleep(5 * (attempt + 1))
                continue
            if r.status_code == 429 or r.status_code >= 500:
                if attempt == 3:
                    raise ResearchError(f"{self.name}: HTTP {r.status_code}: {r.text[:300]}")
                time.sleep(float(r.headers.get("retry-after") or 10 * (attempt + 1)))
                continue
            if r.status_code >= 400:
                raise ResearchError(f"{self.name}: HTTP {r.status_code}: {r.text[:500]}")
            return r.json()
        raise ResearchError(f"{self.name}: retries exhausted")

    def run(self, question: str) -> dict:
        t0 = time.perf_counter()
        body = self._body(question)
        job = self._req("POST", self.create_url, json=body)
        job_id = self._job_id(job)
        while True:
            if time.perf_counter() - t0 > self.max_wait_s:
                raise ResearchError(f"{self.name}: job {job_id} not done after {self.max_wait_s:.0f}s")
            time.sleep(self.poll_s)
            state = self._req("GET", self.status_url.format(id=job_id))
            status = self._status(state)
            if status in self.failed_states:
                raise ResearchError(f"{self.name}: job {job_id} {status}: {str(state.get('error'))[:300]}")
            if status in self.done_states:
                break
        final = self._final(job_id, state)
        answer, sources = self._parse(final)
        if not answer.strip():
            raise ResearchError(f"{self.name}: job {job_id} returned an empty answer")
        return {"answer": answer, "sources": sources, "latency_ms": round((time.perf_counter() - t0) * 1000),
                "request": body, "job_id": job_id, "status": status, "fee_usd": self._fee(body, final), "raw": final}

    def _final(self, job_id, state):
        return state


class LinkupResearch(ResearchBackend):
    name = "linkup-research"
    key_env = "LINKUP_API_KEY"
    create_url = "https://api.linkup.so/v1/research"
    status_url = "https://api.linkup.so/v1/research/{id}"
    done_states, failed_states = {"completed"}, {"failed"}
    poll_s = 5.0  # docs: polling faster than 1 request/second is rate-limited

    def _headers(self):
        return {"Authorization": f"Bearer {self.key}"}

    def _body(self, q):
        return {"q": q, "outputType": "sourcedAnswer", "mode": self.opts.get("mode", "answer"),
                "reasoningDepth": self.opts.get("reasoningDepth", "XL")}

    def _job_id(self, job):
        return job["id"]

    def _status(self, s):
        return s.get("status")

    def _parse(self, s):
        out = s.get("output") or {}
        src = [{"url": x.get("url"), "title": x.get("name"), "published_date": x.get("publishedAt"), "snippet": x.get("snippet")}
               for x in out.get("sources") or []]
        return out.get("answer") or "", src

    def _fee(self, body, final):
        return LINKUP_RESEARCH_FEE.get(body["reasoningDepth"])


class ParallelResearch(ResearchBackend):
    name = "parallel-research"
    key_env = "PARALLEL_API_KEY"
    create_url = "https://api.parallel.ai/v1/tasks/runs"
    status_url = "https://api.parallel.ai/v1/tasks/runs/{id}"
    done_states, failed_states = {"completed"}, {"failed", "cancelled", "action_required"}
    poll_s = 10.0
    max_wait_s = 7200.0  # ultra8x can take up to 2h

    def _headers(self):
        return {"x-api-key": self.key}

    def _body(self, q):
        return {"input": q, "processor": self.opts.get("processor", "ultra"),
                "task_spec": {"output_schema": {"type": "text", "description": PARALLEL_TEXT_SPEC}}}

    def _job_id(self, job):
        if "run_id" not in job:
            raise ResearchError(f"{self.name}: create response has no run_id: {str(job)[:300]}")
        return job["run_id"]

    def _status(self, s):
        return s.get("status")

    def _final(self, job_id, state):
        return self._req("GET", f"https://api.parallel.ai/v1/tasks/runs/{job_id}/result", params={"timeout": 60})

    def _parse(self, res):
        out = res.get("output") or {}
        content = out.get("content")
        answer = content if isinstance(content, str) else (str(content) if content else "")
        src, seen = [], set()
        for b in out.get("basis") or []:
            for c in b.get("citations") or []:
                if c.get("url") and c["url"] not in seen:
                    seen.add(c["url"])
                    src.append({"url": c["url"], "title": c.get("title"), "published_date": None,
                                "snippet": " ".join(c.get("excerpts") or [])[:500]})
        return answer, src

    def _fee(self, body, final):
        return PARALLEL_TASK_FEE.get(body["processor"])


class PerplexityResearch(ResearchBackend):
    name = "perplexity-research"
    key_env = "PERPLEXITY_API_KEY"
    create_url = "https://api.perplexity.ai/v1/agent"
    status_url = "https://api.perplexity.ai/v1/agent/{id}"
    done_states, failed_states = {"completed"}, {"failed", "cancelled", "incomplete"}
    poll_s = 5.0  # Agent API QPS limits count every poll

    def _headers(self):
        return {"Authorization": f"Bearer {self.key}"}

    def _body(self, q):
        return {"input": q, "effort": self.opts.get("effort", "xhigh"), "background": True}

    def _job_id(self, job):
        return job["id"]

    def _status(self, s):
        return s.get("status")

    def _parse(self, s):
        texts, src, seen = [], [], set()
        for item in s.get("output") or []:
            if item.get("type") == "message":
                texts += [c.get("text") or "" for c in item.get("content") or [] if c.get("type") == "output_text"]
            elif item.get("type") == "search_results":
                for x in item.get("results") or []:
                    if x.get("url") and x["url"] not in seen:
                        seen.add(x["url"])
                        src.append({"url": x["url"], "title": x.get("title"), "published_date": x.get("date"),
                                    "snippet": (x.get("snippet") or "")[:500]})
        return "\n".join(t for t in texts if t), src

    def _fee(self, body, final):
        cost = ((final.get("usage") or {}).get("cost") or {}).get("total_cost")
        return float(cost) if cost is not None else None


RESEARCH_BACKENDS = {"linkup": LinkupResearch, "parallel": ParallelResearch, "perplexity": PerplexityResearch}

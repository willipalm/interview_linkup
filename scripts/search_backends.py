"""Search backends behind one interface, so the agent sees an identical tool whatever the arm.

Each backend returns the same normalized result list:
    {"url", "title", "content", "published_date", "last_updated"}
`content` is truncated to the same length for every backend (CONTENT_CHARS), so no arm wins on
context size alone. The raw vendor response is kept too, for metadata scoring.

Request parameters come from each vendor's API reference, read 2026-11-23:
  Linkup      POST https://api.linkup.so/v1/search     Authorization: Bearer
  Perplexity  POST https://api.perplexity.ai/search    Authorization: Bearer
  Parallel    POST https://api.parallel.ai/v1/search   x-api-key
"""
from __future__ import annotations

import datetime as dt
import os
import time

import httpx

CONTENT_CHARS = 1500
TIMEOUT_S = 60.0

# List prices per call, from each vendor's pricing page:
#   Linkup, outputType=searchResults (docs.linkup.so search overview, read 2026-11-23)
#   Perplexity Search API: $5 per 1,000 requests, up to 20 results; $1 per 1,000 with search_type "fast", which this
#     harness doesn't send (docs.perplexity.ai pricing, read 2026-11-24)
#   Parallel Search API, mode advanced (the default when mode is unset, as here): $5 per 1,000 requests with 10
#     results included, +$0.001 per extra result; excerpt length doesn't change the price (docs.parallel.ai pricing,
#     read 2026-11-24)
LINKUP_FEE_USD = {"flash": 0.005, "fast": 0.005, "standard": 0.005, "deep": 0.05}
PERPLEXITY_SEARCH_FEE_USD = 0.005
PARALLEL_SEARCH_FEE_USD = 0.005
PARALLEL_EXTRA_RESULT_FEE_USD = 0.001


def _date(s: str | None) -> dt.date | None:
    return dt.date.fromisoformat(s) if s else None


class SearchError(Exception):
    pass


class Backend:
    name = "base"
    key_env = ""
    supports = {"include": True, "exclude": True, "from_date": True, "to_date": True, "prioritize": False}

    def __init__(self, **opts):
        self.opts = opts
        self.key = os.environ.get(self.key_env, "").strip()

    @property
    def available(self) -> bool:
        return bool(self.key)

    def fee_usd(self, request: dict) -> float | None:
        """List price of one call, when the vendor publishes one we've checked. None = not known."""
        return None

    def search(self, query: str, *, k: int = 10, include=None, exclude=None,
               from_date: str | None = None, to_date: str | None = None,
               depth: str | None = None, prioritize=None) -> dict:
        """Returns {"results": [...], "raw": <vendor json>, "latency_ms", "request", "unsupported": [...], "fee_usd"}.

        depth: per-call override of the backend's depth (Linkup only).
        prioritize: domains to favour without hiding others (Linkup only; see Linkup._body)."""
        unsupported = [f for f, v in (("include", include), ("exclude", exclude),
                                      ("from_date", from_date), ("to_date", to_date), ("prioritize", prioritize))
                       if v and not self.supports[f]]
        body = self._body(query, k=k, include=include, exclude=exclude,
                          from_date=_date(from_date), to_date=_date(to_date), depth=depth, prioritize=prioritize)
        t0 = time.perf_counter()
        try:
            r = httpx.post(self.url, json=body, headers=self._headers(), timeout=TIMEOUT_S)
        except httpx.HTTPError as e:
            raise SearchError(f"{self.name}: network error: {e}") from e
        latency_ms = round((time.perf_counter() - t0) * 1000)
        if r.status_code >= 400:
            raise SearchError(f"{self.name}: HTTP {r.status_code}: {r.text[:500]}")
        raw = r.json()
        results = [self._normalize(x) for x in self._items(raw)][:k]
        for x in results:
            x["content"] = (x["content"] or "")[:CONTENT_CHARS]
        return {"results": results, "raw": raw, "latency_ms": latency_ms,
                "request": body, "unsupported": unsupported, "fee_usd": self.fee_usd(body)}


class Linkup(Backend):
    name = "linkup"
    key_env = "LINKUP_API_KEY"
    url = "https://api.linkup.so/v1/search"
    supports = {**Backend.supports, "prioritize": True}
    # Linkup documents a <guidance><priority> block for this, but in our probes (2026-11-23) it didn't
    # change standard-depth results. A plain instruction did: Linkup's standard/deep agent follows
    # instructions in the query. fast/flash are keyword-only and ignore instructions, so the line is
    # left off there (adding it made fast results worse).
    PRIORITY_LINE = "Prioritise official primary sources: {}."

    def _headers(self):
        return {"Authorization": f"Bearer {self.key}"}

    def fee_usd(self, request):
        return LINKUP_FEE_USD.get(request.get("depth"))

    def _body(self, query, *, k, include, exclude, from_date, to_date, depth=None, prioritize=None):
        depth = depth or self.opts.get("depth", "standard")
        if prioritize and depth in ("standard", "deep"):
            q = query.rstrip()
            query = f"{q}{'' if q.endswith(('.', '?', '!')) else '.'} {self.PRIORITY_LINE.format(', '.join(prioritize))}"
        body = {"q": query, "depth": depth, "outputType": "searchResults", "maxResults": k}
        if include:
            body["includeDomains"] = list(include)[:100]
        if exclude:
            body["excludeDomains"] = list(exclude)
        if from_date:
            body["fromDate"] = from_date.isoformat()
        if to_date:
            body["toDate"] = to_date.isoformat()
        return body

    def _items(self, raw):
        return [x for x in raw.get("results", []) if x.get("type", "text") == "text"]

    def _normalize(self, x):
        return {"url": x.get("url"), "title": x.get("name"), "content": x.get("content"),
                "published_date": x.get("publishedAt"), "last_updated": None}


class Perplexity(Backend):
    name = "perplexity"
    key_env = "PERPLEXITY_API_KEY"
    url = "https://api.perplexity.ai/search"

    def _headers(self):
        return {"Authorization": f"Bearer {self.key}"}

    def fee_usd(self, request):
        return PERPLEXITY_SEARCH_FEE_USD

    @staticmethod
    def _mdy(d: dt.date) -> str:  # Perplexity wants M/D/YYYY; ISO dates return a 400
        return f"{d.month}/{d.day}/{d.year}"

    def _body(self, query, *, k, include, exclude, from_date, to_date, **_):
        body = {"query": query, "max_results": min(k, 20)}
        domains = [*(include or []), *(f"-{d}" for d in (exclude or []))]
        if domains:
            body["search_domain_filter"] = domains[:200]
        if from_date:
            body["search_after_date_filter"] = self._mdy(from_date)
        if to_date:
            body["search_before_date_filter"] = self._mdy(to_date)
        return body

    def _items(self, raw):
        return raw.get("results", [])

    def _normalize(self, x):
        return {"url": x.get("url"), "title": x.get("title"), "content": x.get("snippet"),
                "published_date": x.get("date"), "last_updated": x.get("last_updated")}


class Parallel(Backend):
    name = "parallel"
    key_env = "PARALLEL_API_KEY"
    url = "https://api.parallel.ai/v1/search"
    # No upper date bound is documented (source_policy has after_date only).
    supports = {**Backend.supports, "to_date": False}

    def _headers(self):
        return {"x-api-key": self.key}

    def fee_usd(self, request):
        k = ((request or {}).get("advanced_settings") or {}).get("max_results") or 10
        return PARALLEL_SEARCH_FEE_USD + PARALLEL_EXTRA_RESULT_FEE_USD * max(0, k - 10)

    def _body(self, query, *, k, include, exclude, from_date, to_date, **_):
        policy = {}
        if include:
            policy["include_domains"] = list(include)
        if exclude:
            policy["exclude_domains"] = list(exclude)
        if from_date:
            policy["after_date"] = from_date.isoformat()
        adv = {"max_results": min(k, 20)}
        if policy:
            adv["source_policy"] = policy
        return {"objective": query, "search_queries": [query], "advanced_settings": adv}

    def _items(self, raw):
        return raw.get("results", [])

    def _normalize(self, x):
        return {"url": x.get("url"), "title": x.get("title"),
                "content": "\n".join(x.get("excerpts") or []),
                "published_date": x.get("publish_date"), "last_updated": None}


BACKENDS = {"linkup": Linkup, "perplexity": Perplexity, "parallel": Parallel}

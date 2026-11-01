"""Shared helpers for the e-commerce scenario scripts in this repo.

Two harness modes for wiring You.com's Web Search / Contents APIs into any LLM
that supports tool calling:
  - server-side: pass You.com's Inference Router a `web_search` tool and let the
    model decide when to search; the router executes it inline (one round trip).
  - client-side: call Web Search / Contents yourself, assemble results into the
    prompt, call your model separately. Full control over search parameters.

These scripts default to You.com's Inference Router (api.you.com) purely for
convenience — it proxies a number of open-weight models behind an OpenAI-compatible
interface, so no separate model API key is needed to try the examples. Swap
`DEFAULT_MODEL` below, or point `chat()` at your own model endpoint, to use any
LLM with tool-calling / long-context support.

Auth: set YDC_API_KEY in your environment. Never hardcode the key.

Gotcha (confirmed root cause, not a retry-and-hope issue): api.you.com/v1/chat/completions
sits behind Cloudflare, which rejects Python's default `Python-urllib/3.x` /
`python-requests/x.x` User-Agent with `403 error code: 1010` (Cloudflare's bot/browser-
integrity-check rejection). Setting a normal-looking User-Agent (e.g. "curl/8.0" or any
real browser string) fixes it immediately and reproducibly — this is not a transient
rate-limit; retrying with the default UA will keep failing.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

SEARCH_URL = "https://ydc-index.io/v1/search"
CONTENTS_URL = "https://ydc-index.io/v1/contents"
CHAT_URL = "https://api.you.com/v1/chat/completions"

# Any model your target LLM provider supports tool-calling with. This is just the
# default used for runnable examples in this repo — swap for your own.
DEFAULT_MODEL = os.environ.get("YDC_EXAMPLE_MODEL", "deepseek-v4.1-flash")


def _api_key() -> str:
    key = os.environ.get("YDC_API_KEY")
    if not key:
        raise RuntimeError("Set YDC_API_KEY in your environment before running this script.")
    return key


def _post(url: str, body: dict, headers: dict, retries: int = 4, timeout: int = 90) -> dict:
    data = json.dumps(body).encode()
    headers = {"User-Agent": "curl/8.0", **headers}  # avoid Cloudflare's 1010 on default urllib UA
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            err_body = e.read().decode(errors="replace")
            print(f"  [{url}] attempt {attempt}/{retries} failed: HTTP {e.code} — {err_body[:300]}", file=sys.stderr)
            last_err = e
            if attempt < retries:
                time.sleep(3 * attempt)
    raise last_err


def web_search(query: str, extraction_mode: str | None = None, **params) -> dict:
    """POST /v1/search. Returns the raw response; hits live at results['web']."""
    body = {"query": query, "count": params.pop("count", 10), **params}
    if extraction_mode:
        body["extraction"] = {"extraction_mode": extraction_mode}
    return _post(SEARCH_URL, body, {"X-API-Key": _api_key(), "Content-Type": "application/json"})


def web_search_hits(resp: dict) -> list[dict]:
    r = resp.get("results", {})
    return r.get("web", []) if isinstance(r, dict) else r


def contents(urls: list[str], formats: tuple[str, ...] = ("markdown",)) -> list[dict]:
    """POST /v1/contents. Batch full-page fetch for a list of URLs."""
    body = {"urls": urls, "formats": list(formats)}
    return _post(CONTENTS_URL, body, {"X-API-Key": _api_key(), "Content-Type": "application/json"})


def chat(prompt: str, model: str = DEFAULT_MODEL) -> dict:
    """Plain chat completion via You.com's Inference Router (client-side harness).

    Swap this for a direct call to your own LLM provider if you're not using the
    Inference Router — the rest of the scenario scripts only depend on getting back
    an OpenAI-compatible `choices[0].message.content` response.
    """
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    return _post(
        CHAT_URL, payload,
        {"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"},
    )


def chat_with_search(query: str, model: str = DEFAULT_MODEL) -> dict:
    """Chat completion with server-side web_search tool enabled — the model decides when to search."""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": query}],
        "tools": [{"type": "web_search"}],
    }
    return _post(
        CHAT_URL, payload,
        {"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"},
    )


def content_text(content_item: dict) -> str:
    """Extract markdown body from a /v1/contents response item, tolerant of response shape."""
    if "markdown" in content_item:
        return content_item["markdown"]
    return content_item.get("contents", {}).get("markdown", "")

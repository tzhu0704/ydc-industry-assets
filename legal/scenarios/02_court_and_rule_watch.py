"""Scenario 2 — Court & rule watch (client-side harness mode)

A weekly brief on new rulings/regulatory developments is only useful if it's
actually new. Domain-scoping to legal-news aggregators (Lexology, National Law
Review, JD Supra) surfaces more substantive legal content than an unscoped search —
but even scoped results can include older background articles mixed in with
genuinely recent ones.

This scenario's prompt explicitly asks the model to flag items where the source's
own dates don't clearly support "new this week" rather than silently presenting a
stale article as current. That's the difference between a brief someone can trust
and one that requires independent verification of every line anyway.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from you_api import chat, web_search, web_search_hits

QUERY = "new rulings on cross-border data transfers"
LEGAL_NEWS_DOMAINS = ["lexology.com", "natlawreview.com", "jdsupra.com"]

PROMPT_TEMPLATE = """You are a legal research assistant producing a weekly brief on new court
rulings and regulatory developments affecting cross-border data transfers. Based on the search
results below, write a dated, sourced brief: only include items that are genuinely recent/new
rulings or guidance, and explicitly flag or exclude older background articles that are not
actually new developments — check each result's own publish date rather than assuming recency.
Cite each item.

{context}
"""


def build_context(hits: list[dict]) -> str:
    blocks = []
    for i, hit in enumerate(hits[:6], 1):
        title = hit.get("title", "")
        url = hit.get("url", "")
        highlights = hit.get("contents", {}).get("highlights", [])
        text = " ".join(highlights[:2]) if highlights else hit.get("description", "")
        blocks.append(f"[{i}] {title} — {url}\n{text[:500]}")
    return "\n\n".join(blocks)


def main() -> None:
    print(f"Query: {QUERY}", file=sys.stderr)
    print(f"Domain scope: {LEGAL_NEWS_DOMAINS}\n", file=sys.stderr)

    search_result = web_search(
        QUERY,
        freshness="week",
        extraction_mode="highlights",
        include_domains=LEGAL_NEWS_DOMAINS,
        count=6,
    )
    hits = web_search_hits(search_result)
    print(f"{len(hits)} hits", file=sys.stderr)

    prompt = PROMPT_TEMPLATE.format(context=build_context(hits))
    brief = chat(prompt)

    with open("scenario2_search_result.json", "w") as f:
        json.dump(search_result, f, indent=2, ensure_ascii=False)
    with open("scenario2_brief.json", "w") as f:
        json.dump(brief, f, indent=2, ensure_ascii=False)

    print(brief["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()

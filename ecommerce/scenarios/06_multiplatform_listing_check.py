"""Scenario 6 — Multi-platform listing & pricing check (client-side harness mode)

A seller deciding where to list a new product needs to know: which platforms show
real demand for this product category, what price range is competitive there, and
who else is already selling it. This is a single Web Search call (highlights mode,
no domain scoping needed — the point is breadth across platforms) handed to the
model for a cross-platform comparison.

This is a different question from scenario 5 (competitor platform intelligence):
scenario 5 asks "how healthy is this named competitor," this scenario asks "where
should I list this product and at what price," for any product category.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from you_api import chat, web_search, web_search_hits

QUERY = "best-selling portable blenders on Amazon and TikTok Shop main suppliers price range"

PROMPT_TEMPLATE = """You are a cross-border e-commerce seller deciding where to list a new product.
Based on the search results below, answer: which platforms (Amazon, TikTok Shop, etc.) show
strong demand for this product category, what price range is competitive there, and who are
the visible suppliers/sellers. Cite sources.

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
    print(f"Query: {QUERY}\n", file=sys.stderr)
    search_result = web_search(QUERY, extraction_mode="highlights", count=6)
    hits = web_search_hits(search_result)
    print(f"{len(hits)} hits", file=sys.stderr)

    prompt = PROMPT_TEMPLATE.format(context=build_context(hits))
    answer = chat(prompt)

    with open("scenario6_search_result.json", "w") as f:
        json.dump(search_result, f, indent=2, ensure_ascii=False)
    with open("scenario6_answer.json", "w") as f:
        json.dump(answer, f, indent=2, ensure_ascii=False)

    print(answer["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()

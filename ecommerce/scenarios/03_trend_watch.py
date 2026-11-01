"""Scenario 3 — Trend & competitor-price watch (client-side harness mode)

Full chain: Search (discover candidate pages) -> Contents (batch-fetch full page
bodies) -> model synthesis (structured per-source extraction + cross-source trend
summary).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from you_api import chat, content_text, contents, web_search, web_search_hits

DISCOVERY_QUERY = "portable blender trending products Amazon 2026"
NUM_SOURCES = 3
MAX_CHARS_PER_SOURCE = 3000

SYNTHESIS_PROMPT_TEMPLATE = """You are a trend/price monitoring agent. Based on the full page content below from
{n} retailer/review sites, extract a structured trend report for "portable blender" as a product category.

For each source, output: product name, price (if mentioned), key trend/sentiment signal, source URL.
Then give one summary line on the overall trend.

{context}
"""


def main() -> None:
    print(f"Step 1: discover candidate pages — query: {DISCOVERY_QUERY!r}", file=sys.stderr)
    discovery = web_search(DISCOVERY_QUERY, freshness="week", count=5)
    hits = web_search_hits(discovery)
    urls = [h["url"] for h in hits[:NUM_SOURCES]]
    print(f"Found {len(urls)} candidate URLs: {urls}", file=sys.stderr)

    print("\nStep 2: Contents API batch fetch", file=sys.stderr)
    pages = contents(urls)

    print("\nStep 3: model synthesis across sources", file=sys.stderr)
    context_blocks = [
        f"SOURCE: {item.get('url', '')}\n{content_text(item)[:MAX_CHARS_PER_SOURCE]}"
        for item in pages
    ]
    prompt = SYNTHESIS_PROMPT_TEMPLATE.format(n=len(context_blocks), context="\n\n---\n\n".join(context_blocks))
    synthesis = chat(prompt)

    with open("scenario3_discovery.json", "w") as f:
        json.dump(discovery, f, indent=2, ensure_ascii=False)
    with open("scenario3_contents.json", "w") as f:
        json.dump(pages, f, indent=2, ensure_ascii=False)
    with open("scenario3_synthesis.json", "w") as f:
        json.dump(synthesis, f, indent=2, ensure_ascii=False)

    print("\n=== Synthesis output ===", file=sys.stderr)
    print(synthesis["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()

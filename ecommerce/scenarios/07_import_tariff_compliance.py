"""Scenario 7 — Import tariff / HS code compliance check (client-side harness mode)

Before importing a product, a cross-border seller needs the HS classification and
current tariff rate — and needs it from official sources, not a blog post. Domain
scoping (`include_domains` limited to government trade/customs sites) is what makes
this usable: it keeps the model's answer grounded in rulings and bulletins instead
of SEO content, and it tends to surface trade-remedy complications (e.g. Section 201
tariff-rate quotas, antidumping/countervailing duty orders) that a generic search
wouldn't reliably catch.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from you_api import chat, web_search, web_search_hits

QUERY = "current US import tariffs and HS codes for portable solar panels"
GOVERNMENT_TRADE_DOMAINS = ["cbp.gov", "usitc.gov", "trade.gov"]

PROMPT_TEMPLATE = """You are a customs compliance agent for a cross-border e-commerce importer.
Based on the search results below (official US government sources only), answer: what HS
code(s) apply to this product, what is the current general tariff rate, and are there any
additional trade-remedy measures (Section 201/301, antidumping/countervailing duties) that
could apply depending on country of origin. Cite sources, and be explicit about what is NOT
confirmed by the provided sources rather than guessing.

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
    print(f"Domain scope: {GOVERNMENT_TRADE_DOMAINS}\n", file=sys.stderr)

    search_result = web_search(
        QUERY,
        extraction_mode="highlights",
        include_domains=GOVERNMENT_TRADE_DOMAINS,
        count=6,
    )
    hits = web_search_hits(search_result)
    print(f"{len(hits)} hits", file=sys.stderr)

    prompt = PROMPT_TEMPLATE.format(context=build_context(hits))
    answer = chat(prompt)

    with open("scenario7_search_result.json", "w") as f:
        json.dump(search_result, f, indent=2, ensure_ascii=False)
    with open("scenario7_answer.json", "w") as f:
        json.dump(answer, f, indent=2, ensure_ascii=False)

    print(answer["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()

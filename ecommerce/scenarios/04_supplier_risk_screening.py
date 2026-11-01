"""Scenario 4 — Supplier risk/compliance screening (client-side harness mode)

Full chain: domain-scoped Search (highlights mode) -> model risk determination
(CLEAR / RISK FOUND / INCONCLUSIVE, with citations).

Uses a FICTIONAL company name ("GlobalPack Trading Co Ltd") deliberately — no real
customer's data is used anywhere in this scenario.

Scoping the query to known public-record domains, combined with highlights mode to
surface the matching passage directly, is what lets the model find an actual
relevant filing when one exists instead of a desk full of near-identical company
names to sort through manually.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from you_api import chat, web_search, web_search_hits

QUERY = '"GlobalPack Trading Co Ltd" lawsuit OR compliance OR violation'
TARGET_ENTITY = "GlobalPack Trading Co Ltd"
PUBLIC_RECORD_DOMAINS = ["dockets.justia.com", "courtlistener.com", "sec.gov"]

SCREENING_PROMPT_TEMPLATE = """You are a supplier risk/compliance screening agent. A procurement team asked:
"Does {entity} have any lawsuit or compliance records?"

Below are the search results returned for this query. Based ONLY on these results, answer:
1. Does {entity} specifically appear as a party in any of these results?
2. What is your risk determination: CLEAR (no records found), RISK FOUND (named in a legal/compliance matter), or INCONCLUSIVE (results don't clearly address the named company)?
3. Cite which result numbers support your answer.

Search results:
{context}
"""


def build_context(hits: list[dict]) -> str:
    blocks = []
    for i, hit in enumerate(hits[:10], 1):
        title = hit.get("title", "")
        url = hit.get("url", "")
        highlights = hit.get("contents", {}).get("highlights", [])
        text = " ".join(highlights[:2]) if highlights else hit.get("description", "")
        blocks.append(f"[{i}] {title} — {url}\n{text[:600]}")
    return "\n\n".join(blocks)


def main() -> None:
    print(f"Query: {QUERY}", file=sys.stderr)
    print(f"Target entity (fictional): {TARGET_ENTITY}", file=sys.stderr)
    print(f"Domain scope: {PUBLIC_RECORD_DOMAINS}\n", file=sys.stderr)

    search_result = web_search(
        QUERY,
        extraction_mode="highlights",
        include_domains=PUBLIC_RECORD_DOMAINS,
    )
    hits = web_search_hits(search_result)
    print(f"{len(hits)} hits", file=sys.stderr)

    prompt = SCREENING_PROMPT_TEMPLATE.format(entity=TARGET_ENTITY, context=build_context(hits))
    verdict = chat(prompt)

    with open("scenario4_search_results.json", "w") as f:
        json.dump(search_result, f, indent=2, ensure_ascii=False)
    with open("scenario4_verdict.json", "w") as f:
        json.dump(verdict, f, indent=2, ensure_ascii=False)

    print("\n=== Verdict ===")
    print(verdict["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()

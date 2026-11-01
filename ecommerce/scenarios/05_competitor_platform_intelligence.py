"""Scenario 5 — Competitor platform intelligence (one call, knowledge + highlights)

A single Web Search call with both `knowledge=core` and `extraction_mode=highlights`
enabled returns, in one response:
  - a structured, licensed financial record for a named public company (via knowledge)
  - the specific recent news passages behind the story (via highlights)

The model is handed both and asked to write a one-paragraph competitor health brief:
stock trend, valuation signal, and material recent events that could affect the
competitor's posture next quarter.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from you_api import chat, web_search, web_search_hits

QUERY = "PDD Holdings Temu stock price and recent news"

PROMPT_TEMPLATE = """You are a competitive intelligence agent for a cross-border e-commerce
seller who competes with Temu. Using the structured financial data and news below,
write a 1-paragraph competitor health brief: stock trend, valuation signal, and any
material recent events (legal, operational) that could affect Temu's competitive
posture in the next quarter. Cite sources.

{context}
"""


def build_context(search_result: dict) -> str:
    blocks = []
    for record in search_result.get("results", {}).get("knowledge", []):
        source = record.get("attribution", [{}])[0].get("name", "")
        blocks.append(
            f"[KNOWLEDGE] {record.get('title', '')}: {record.get('description', '')} "
            f"(as of {record.get('as_of', 'N/A')}, source: {source})"
        )

    for i, hit in enumerate(web_search_hits(search_result)[:5], 1):
        highlights = hit.get("contents", {}).get("highlights", [])
        text = " ".join(highlights[:2]) if highlights else hit.get("description", "")
        blocks.append(f"[{i}] {hit.get('title', '')} — {hit.get('url', '')}\n{text[:400]}")

    return "\n\n".join(blocks)


def main() -> None:
    print(f"Query: {QUERY}", file=sys.stderr)
    search_result = web_search(QUERY, knowledge="core", extraction_mode="highlights", count=8)

    knowledge_count = len(search_result.get("results", {}).get("knowledge", []))
    web_count = len(web_search_hits(search_result))
    print(f"knowledge records: {knowledge_count}, web hits: {web_count}", file=sys.stderr)

    prompt = PROMPT_TEMPLATE.format(context=build_context(search_result))
    brief = chat(prompt)

    with open("scenario5_search_result.json", "w") as f:
        json.dump(search_result, f, indent=2, ensure_ascii=False)
    with open("scenario5_brief.json", "w") as f:
        json.dump(brief, f, indent=2, ensure_ascii=False)

    print(brief["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()

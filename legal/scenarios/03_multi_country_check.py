"""Scenario 3 — Multi-country compliance check (client-side harness mode)

A client needs the same question answered across several jurisdictions: one search
per country, combined into a single comparison table. The model is explicitly asked
to flag any country where the provided sources don't support a confident answer,
rather than producing a uniform-looking table that papers over gaps in coverage.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from you_api import chat, web_search, web_search_hits

COUNTRIES = ["European Union", "United Kingdom", "Singapore", "Brazil"]
TOPIC = "financial data localization rules"

PROMPT_TEMPLATE = """You are a legal research assistant. A client needs a comparison of {topic}
across {countries}. Based on the search results below, produce one row per country with:
whether localization is required, key requirement, and source citation. Flag any country where
the provided sources are insufficient to give a confident answer rather than guessing.

{context}
"""


def build_context(per_country_hits: dict[str, list[dict]]) -> str:
    sections = []
    for country, hits in per_country_hits.items():
        blocks = []
        for i, hit in enumerate(hits[:3], 1):
            title = hit.get("title", "")
            url = hit.get("url", "")
            highlights = hit.get("contents", {}).get("highlights", [])
            text = " ".join(highlights[:2]) if highlights else hit.get("description", "")
            blocks.append(f"  [{i}] {title} — {url}\n  {text[:400]}")
        sections.append(f"== {country} ==\n" + "\n\n".join(blocks))
    return "\n\n".join(sections)


def main() -> None:
    print(f"Topic: {TOPIC}", file=sys.stderr)
    print(f"Countries: {COUNTRIES}\n", file=sys.stderr)

    per_country_results: dict[str, dict] = {}
    per_country_hits: dict[str, list[dict]] = {}
    for country in COUNTRIES:
        query = f"{TOPIC} {country}"
        print(f"Searching: {query!r}", file=sys.stderr)
        result = web_search(query, extraction_mode="highlights", count=3)
        per_country_results[country] = result
        per_country_hits[country] = web_search_hits(result)

    prompt = PROMPT_TEMPLATE.format(
        topic=TOPIC,
        countries=", ".join(COUNTRIES),
        context=build_context(per_country_hits),
    )
    comparison = chat(prompt)

    with open("scenario3_search_results.json", "w") as f:
        json.dump(per_country_results, f, indent=2, ensure_ascii=False)
    with open("scenario3_comparison.json", "w") as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)

    print(comparison["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()

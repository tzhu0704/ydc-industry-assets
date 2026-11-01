"""Scenario 1 — Sourcing agent with landed-cost math (client-side harness mode)

Two Web Search calls, combined by the model into one answer:
  1. Supplier discovery (highlights mode) — find suppliers outside your own catalog.
  2. Live FX rate (knowledge=core) — a precise, dated currency value for landed-cost math.

The model is handed both result sets and asked to produce a supplier shortlist plus
a landed-cost conversion using the live rate — including reasoning about what the
number does and doesn't represent (goods cost only, not duties/freight).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from you_api import chat, web_search, web_search_hits

SUPPLIER_QUERY = "recycled PET packaging suppliers in Vietnam FDA compliant"
FX_QUERY = "Vietnamese Dong to US Dollar exchange rate"
HYPOTHETICAL_QUOTE_VND = 500_000_000

PROMPT_TEMPLATE = """You are a sourcing agent for a US-based e-commerce buyer. Using the supplier
search results and the live FX rate below, produce a short supplier shortlist with a
landed-cost note: for each supplier, state what we know about pricing/MOQ if mentioned,
and compute what a hypothetical {quote:,} VND quoted price would be in USD using the
live rate provided. Cite sources.

[LIVE FX RATE]
{fx_description}

[SUPPLIER SEARCH RESULTS]
{supplier_context}
"""


def build_supplier_context(hits: list[dict]) -> str:
    blocks = []
    for i, hit in enumerate(hits[:6], 1):
        title = hit.get("title", "")
        url = hit.get("url", "")
        highlights = hit.get("contents", {}).get("highlights", [])
        text = " ".join(highlights[:2]) if highlights else hit.get("description", "")
        blocks.append(f"[{i}] {title} — {url}\n{text[:500]}")
    return "\n\n".join(blocks)


def main() -> None:
    print(f"Supplier query: {SUPPLIER_QUERY!r}", file=sys.stderr)
    supplier_search = web_search(SUPPLIER_QUERY, extraction_mode="highlights", count=6)
    supplier_hits = web_search_hits(supplier_search)

    print(f"FX query: {FX_QUERY!r}", file=sys.stderr)
    fx_search = web_search(FX_QUERY, knowledge="core", count=2)
    fx_records = fx_search.get("results", {}).get("knowledge", [])
    if not fx_records:
        raise RuntimeError("No knowledge record returned for the FX query — try again or check the query.")
    fx_description = fx_records[0]["description"]

    prompt = PROMPT_TEMPLATE.format(
        quote=HYPOTHETICAL_QUOTE_VND,
        fx_description=fx_description,
        supplier_context=build_supplier_context(supplier_hits),
    )
    answer = chat(prompt)

    with open("scenario1_supplier_search.json", "w") as f:
        json.dump(supplier_search, f, indent=2, ensure_ascii=False)
    with open("scenario1_fx_search.json", "w") as f:
        json.dump(fx_search, f, indent=2, ensure_ascii=False)
    with open("scenario1_result.json", "w") as f:
        json.dump(answer, f, indent=2, ensure_ascii=False)

    print(answer["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()

"""Scenario 4 — Reference-image search for a creative tool (text -> image, no model in the loop)

Creative tools need a reference image for a text brief. This script runs four kinds of brief through the image
engine and reports measurable properties of the top 20 results: how many are on-topic (key-term match, a cheap
proxy and not human judgment), how many carry a direct image-file URL, how many distinct sources, and how many come
from stock-photo sites. It then builds a shortlist: direct image URL, not stock, on-topic.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from media_utils import host, is_direct_image, is_stock, on_topic
from you_api import custom_search, save_sample

BRIEFS = [  # (kind, query, key terms for the on-topic proxy)
    ("location-specific", "Islamabad night city blurred background", ["islamabad"]),
    ("generic background", "blurred city lights bokeh vertical background", ["bokeh", "blur", "city"]),
    ("named subject", "Neymar Jr photo", ["neymar"]),
    ("style reference", "minimalist product photography white background", ["minimal", "product", "white"]),
]
TOP = 20


def measure(results: list[dict], terms: list[str]) -> dict:
    rows = results[:TOP]
    text = lambda r: f"{r.get('title','')} {r.get('source','')} {r.get('link','')}"
    return {
        "n": len(rows),
        "on_topic": sum(on_topic(text(r), terms) for r in rows),
        "direct_image": sum(is_direct_image(r.get("original", "")) for r in rows),
        "sources": len({r.get("source") or host(r.get("link", "")) for r in rows}),
        "stock": sum(is_stock(r.get("link", "")) or is_stock(r.get("source", "")) for r in rows),
    }


def main() -> None:
    table, first_results = [], None
    for kind, q, terms in BRIEFS:
        req = {"q": q, "country": "US"}
        resp = custom_search("google_images", **req)
        results = resp.get("images_results", [])
        save_sample(f"04_{kind.split()[0]}", {"engine": "google_images", **req},
                    {"images_results": results[:3], "total_returned": len(results)})
        m = measure(results, terms)
        table.append((kind, q, m))
        if first_results is None:
            first_results = results
        print(f"{kind:18} {m}", file=sys.stderr)

    print(f"{'brief':18} {'n':>3} {'on-topic':>9} {'direct img':>11} {'sources':>8} {'stock':>6}")
    for kind, _, m in table:
        print(f"{kind:18} {m['n']:>3} {m['on_topic']:>9} {m['direct_image']:>11} {m['sources']:>8} {m['stock']:>6}")
    save_sample("04_table", {"top": TOP}, {"rows": [{"brief": k, "query": q, **m} for k, q, m in table]})

    short = [r for r in first_results[:TOP] if is_direct_image(r.get("original", ""))
             and not (is_stock(r.get("link", "")) or is_stock(r.get("source", "")))
             and on_topic(f"{r.get('title','')} {r.get('source','')}", BRIEFS[0][2])][:5]
    print(f"\nShortlist for {BRIEFS[0][1]!r}: {len(short)} of {min(TOP, len(first_results))}")
    for r in short:
        print(f"- {r.get('title','')[:60]} | {r.get('source')} | {r['original'][:80]} | {r.get('original_width')}x{r.get('original_height')}")


if __name__ == "__main__":
    main()

"""Scenario 7 — Where did this image come from? (reverse image search, no model)

Before a generated or retrieved image goes into a template, ask where else it appears. Reverse image search
(`engine=google_lens`) returns visual matches; grouping them by source tells you quickly whether the image is
sold on stock sites (licence needed) or only appears elsewhere (unknown, check manually). The result is a triage
signal, not a licence determination.
"""

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from media_utils import host, is_direct_image, is_stock
from you_api import custom_search, save_sample

QUERY = "Tokyo Tower at night photo"


def candidates() -> list[str]:
    res = custom_search("google_images", q=QUERY, country="US").get("images_results", [])
    return [r["original"] for r in res if is_direct_image(r.get("original", ""))][:8]


def main() -> None:
    for url in candidates():
        try:
            resp = custom_search("google_lens", type="visual_matches", url=url)
        except Exception as e:  # a host may block fetching; try the next candidate
            print(f"skip {host(url)}: {type(e).__name__}", file=sys.stderr)
            continue
        matches = resp.get("visual_matches", [])
        if not matches:
            print(f"skip {host(url)}: no matches ({resp.get('error','')[:50]})", file=sys.stderr)
            continue
        stock = [m for m in matches if is_stock(m.get("link", "")) or is_stock(m.get("source", ""))]
        by_source = Counter(m.get("source") or host(m.get("link", "")) for m in matches)
        save_sample("07_provenance", {"engine": "google_lens", "type": "visual_matches", "url": "<candidate image>"},
                    {"visual_matches": matches[:3], "total_matches": len(matches)})
        print(f"image host      : {host(url)}")
        print(f"visual matches  : {len(matches)}")
        print(f"on stock sites  : {len(stock)}  ({100 * len(stock) // len(matches)}%)")
        print("top sources     :", by_source.most_common(6))
        verdict = ("visual matches include stock-photo sites (they may be similar images, not copies): "
                   "confirm the licence before use" if stock else
                   "no stock-site matches found: provenance unknown, check the original page manually")
        print("triage          :", verdict)
        return
    sys.exit("No candidate image produced reverse-search matches.")


if __name__ == "__main__":
    main()

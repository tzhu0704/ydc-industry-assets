"""Scenario 6 — Licence-aware asset retrieval (domain-scoped Web Search + Contents, no model)

Creators and tool vendors ask the same question about any asset search: "may I use this?" Search results are
candidates, not licences. The safest pattern is to scope retrieval to sources that publish reuse terms
(`include_domains`: space agencies, museums, Wikimedia Commons), read each page with Contents (HTML, so the
media file URLs are complete), and return the candidate files together with their source page.

Licence status is NOT inferred from page text: wiki pages, for example, carry boilerplate licence wording about the
page text, not about the image, and an agent that sniffs it would report the wrong thing. Every candidate is
reported as "licence: confirm on the source page", and a person (or a licence-field API of the source) decides.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from media_utils import extract_media_urls, host
from you_api import contents, save_sample, web_search, web_search_hits

QUERY = "Hubble Ultra Deep Field image"
OPEN_SOURCES = ["nasa.gov", "science.nasa.gov", "esahubble.org", "commons.wikimedia.org", "si.edu", "loc.gov"]


def main() -> None:
    req = dict(query=QUERY, count=6, include_domains=OPEN_SOURCES)
    res = web_search(extraction_mode="highlights", **req)
    save_sample("06_search", {**req, "extraction": {"extraction_mode": "highlights"}}, res)
    hits = web_search_hits(res)
    print(f"hits: {len(hits)} from {sorted({host(h['url']) for h in hits})}", file=sys.stderr)
    if not hits:
        sys.exit("No results from open-licence sources.")

    urls = [h["url"] for h in hits[:3]]
    pages = contents(urls, formats=("html", "markdown"))
    items = pages if isinstance(pages, list) else pages.get("results") or pages.get("contents") or []
    report = []
    for it in items:
        html = it.get("html") or (it.get("contents") or {}).get("html", "")
        report.append({"page": it.get("url"), "media_files": extract_media_urls(html)[:3],
                       "licence": "not determined: confirm on the source page"})
    save_sample("06_contents", {"urls": urls, "formats": ["html", "markdown"]}, report)

    for r in report:
        print(f"\n{r['page']}")
        print("  media files :", r["media_files"] or "none found")
        print("  licence     :", r["licence"])


if __name__ == "__main__":
    main()

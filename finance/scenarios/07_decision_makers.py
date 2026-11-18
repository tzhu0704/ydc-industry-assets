"""Scenario 7 — Decision-maker discovery for corporate banking (People Search + filing corroboration)

A corporate-banking team prospecting a listed company wants to know who holds the finance roles. People Search
(`POST /v1/people/search`) returns structured profiles by role and place: current title and company, tenure, and trust
signals (`authenticity_score`, `source_count`, `last_updated_at`). Each company is then checked against HKEXnews with
Web Search to see whether it is a listed issuer. The output is a lead list for a human to verify, never a verification.
Names, links and bios are dropped before anything is written to samples/.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from you_api import hit_text, people_search, redact_person, save_sample, web_search, web_search_hits

QUERY = "chief financial officer at Hong Kong listed company"
DOMAINS = ["hkexnews.hk", "www.hkexnews.hk", "www1.hkexnews.hk"]
GENERIC = {"hong", "kong", "hk", "the", "a", "an", "limited", "ltd", "holdings", "group", "company", "co", "listed", "china", "international", "mainboard"}


def distinctive_token(company: str) -> str | None:
    """First word of the company name that is specific enough to look for; None for names like "HK Listed Co"."""
    c = company.lower()
    if "listed" in c or not any(k in c for k in ("limited", "holdings", "group", "corporation", "company", "bank", "securities", "ltd")):
        return None  # a placeholder, or not a company that could be a listed issuer
    return next((w for w in company.lower().replace("(", " ").split() if w not in GENERIC and len(w) >= 4), None)


def main() -> None:
    resp = people_search(QUERY, count=10)
    # profiles whose company name is a placeholder (e.g. "HK Listed Co") cannot be looked up: keep the named ones
    people = [p for p in resp.get("results", []) if distinctive_token((p.get("current_position") or {}).get("company") or "")][:5]
    print(f"people: {len(people)}", file=sys.stderr)
    if not people:
        sys.exit("People Search returned nothing: not guessing.")
    save_sample("07_people", {"query": QUERY, "count": 10}, {"results": [redact_person(p) for p in people]})

    rows = []
    for i, p in enumerate(people, 1):
        pos = p.get("current_position") or {}
        company = pos.get("company") or ""
        listed = None
        token = distinctive_token(company) if company else None
        if token:
            req = dict(query=f"{company} announcement", count=5, include_domains=DOMAINS)
            r = web_search(extraction_mode="highlights", **req)
            save_sample(f"07_filings_{i}", {**req, "query": "<company> announcement", "extraction": {"extraction_mode": "highlights"}},
                        {"results": {"web": [{"url": h["url"], "page_age": h.get("page_age")} for h in web_search_hits(r)]}})
            listed = sum(1 for h in web_search_hits(r) if token in (h.get("title", "") + hit_text(h, 1500)).lower())
        rows.append({"title": pos.get("title"), "company": company, "months_in_role": pos.get("months_in_role"),
                     "authenticity": p.get("authenticity_score"), "sources": p.get("source_count"),
                     "updated": (p.get("last_updated_at") or "")[:10], "filings_found": listed})

    print(f"{'title':28} {'company':34} {'months':>6} {'auth':>5} {'src':>4} {'updated':10} {'HKEX hits':>9}")
    for r in rows:
        print(f"{(r['title'] or '')[:28]:28} {r['company'][:34]:34} {str(r['months_in_role'] or ''):>6} "
              f"{str(r['authenticity'] or ''):>5} {str(r['sources'] or ''):>4} {r['updated']:10} {'n/a' if r['filings_found'] is None else r['filings_found']:>9}")
    print("\nTriage: a profile is a claim. Low authenticity_score or source_count, or no filings found, means ask a person.")
    save_sample("07_table", {"query": QUERY}, {"rows": rows})


if __name__ == "__main__":
    main()

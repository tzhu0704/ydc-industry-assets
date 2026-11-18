"""Scenario 8 — What Knowledge adds: the same finance queries with and without it (measured, no model)

For each query the script makes two Web Search calls, one plain and one with `knowledge=core`, and records what each
returns: whether a structured record came back, who provided it and how old it is, and the latency the API reports.
Ten queries across FX, rates, macro and company data are run; the count of queries that returned a record is reported as is.
Latency is the API's own `metadata.latency` for a single run; repeated identical requests can be served faster.
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from finance_utils import days_old, median
from you_api import knowledge_records, save_sample, web_search, web_search_hits
from urllib.parse import urlparse

QUERIES = [
    ("FX", "USD to HKD exchange rate"), ("FX", "CNY to HKD exchange rate"),
    ("Rates", "US 10-year treasury yield"), ("Rates", "Hong Kong Monetary Authority base rate"),
    ("Macro", "Hong Kong inflation rate"), ("Macro", "Hong Kong GDP growth"),
    ("Company", "HSBC Holdings stock price"), ("Company", "Standard Chartered revenue latest quarter"),
    ("Other", "Hong Kong property price index"), ("Other", "HIBOR rate"),
]


def host(url: str) -> str:
    return urlparse(url).netloc.removeprefix("www.")


def main() -> None:
    today, rows = date.today(), []
    for group, q in QUERIES:
        plain = web_search(q, count=5)
        kn = web_search(q, count=5, knowledge="core")
        save_sample(f"08_{len(rows) + 1:02d}", {"query": q, "knowledge": "core", "count": 5},
                    {"results": {"knowledge": knowledge_records(kn)[:1]}, "metadata": kn.get("metadata", {})})
        recs = knowledge_records(kn)
        top = recs[0] if recs else None
        rows.append({
            "group": group, "query": q,
            "record": bool(top), "provider": top["attribution"][0]["name"] if top else "",
            "age_days": days_old(top.get("as_of"), today) if top else None,
            "lat_plain": plain.get("metadata", {}).get("latency"), "lat_knowledge": kn.get("metadata", {}).get("latency"),
            "web_first_host": host(web_search_hits(plain)[0]["url"]) if web_search_hits(plain) else "",
        })
        r = rows[-1]
        print(f"{q[:40]:40} record={r['record']!s:5} {r['provider'][:26]:26} age={r['age_days']} "
              f"lat {r['lat_plain']:.2f}s -> {r['lat_knowledge']:.2f}s", file=sys.stderr)

    got = [r for r in rows if r["record"]]
    print(f"\nqueries with a structured, attributed record: {len(got)} of {len(rows)}")
    print(f"providers: {sorted({r['provider'] for r in got})}")
    print(f"median record age: {median([r['age_days'] for r in got])} days")
    print(f"median latency  plain: {median([r['lat_plain'] for r in rows]):.2f}s   with knowledge: {median([r['lat_knowledge'] for r in rows]):.2f}s")
    print("no record for:", [r["query"] for r in rows if not r["record"]])
    save_sample("08_table", {"queries": len(rows)}, {"rows": rows})


if __name__ == "__main__":
    main()

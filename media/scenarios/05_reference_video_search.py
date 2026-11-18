"""Scenario 5 — Reference-video search (text -> video, no model in the loop)

The same idea as scenario 4 for footage: three kinds of brief through the video engine, reporting count,
distinct platforms and an on-topic proxy for the top 10, plus a shortlist with title and platform.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from media_utils import host, on_topic
from you_api import custom_search, save_sample

BRIEFS = [
    ("topic explainer", "Banana Wars history", ["banana"]),
    ("named subject", "Neymar skills dribbling compilation", ["neymar"]),
    ("mood footage", "rainy night city street slow motion", ["rain", "night", "street"]),
]
TOP = 10


def platform(r: dict) -> str:
    return (r.get("displayed_link") or host(r.get("link", ""))).split("›")[0].strip().removeprefix("www.")


def main() -> None:
    rows, first = [], None
    for kind, q, terms in BRIEFS:
        resp = custom_search("google_videos", q=q, country="US")
        vids = resp.get("video_results", [])[:TOP]
        save_sample(f"05_{kind.split()[0]}", {"engine": "google_videos", "q": q}, {"video_results": vids[:3]})
        m = {"n": len(vids), "platforms": len({platform(v) for v in vids}),
             "on_topic": sum(on_topic(f"{v.get('title','')} {v.get('snippet','')}", terms) for v in vids)}
        rows.append((kind, q, m))
        first = first or vids
        print(f"{kind:16} {m}", file=sys.stderr)
    print(f"{'brief':16} {'n':>3} {'platforms':>10} {'on-topic':>9}")
    for kind, _, m in rows:
        print(f"{kind:16} {m['n']:>3} {m['platforms']:>10} {m['on_topic']:>9}")
    save_sample("05_table", {"top": TOP}, {"rows": [{"brief": k, "query": q, **m} for k, q, m in rows]})
    print(f"\nShortlist for {BRIEFS[0][1]!r}:")
    for v in first[:5]:
        print(f"- {v.get('title','')[:70]} | {platform(v)}")


if __name__ == "__main__":
    main()

"""Scenario 1 — Regulatory circular watch (official domains + freshness + highlights)

A bank's compliance team needs this month's regulatory changes, in Traditional Chinese, without a law firm's
summary in between. Retrieval is limited to the two regulators' own sites (`include_domains`) and to the last month
(`freshness`); Highlights returns the matching passage of each page. `freshness` is a request, not a guarantee: a run can still
return older or undated pages, so the code splits the results by page_age into "recent" and "older or undated" itself.
The brief is checked in code before it is shown: every date must be one the search supplied, every [n] citation must
exist, every recent source must be covered, and the text must be Traditional Chinese.
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from finance_utils import bad_citations, days_old, outside_window, simplified_chars, ungrounded_dates
from loop import checked_chat
from you_api import hit_text, save_sample, web_search, web_search_hits

QUERY = "new circular to authorized institutions licensed corporations requirements consultation"
DOMAINS = ["hkma.gov.hk", "sfc.hk"]
QUERY_SITE = "(site:hkma.gov.hk OR site:sfc.hk) " + QUERY

PROMPT = """你是香港銀行合規團隊的監管動態助手。只依據下面編號的官方來源，用繁體中文寫「近 30 天監管動態」簡報。
【近期】組的每個來源各寫一行：發布機構（來源標註的 HKMA 或 SFC）、日期（只能用該來源的 page_age，格式 YYYY-MM-DD）、
一句話說明要求或變化、來源編號 [n]。若該來源只是目錄或索引頁而不是具體通函，直接說明。
【較舊或日期未知】組合併成一行，列出編號與日期，說明它們不屬於近 30 天，僅供參考。
資料沒有寫明的（生效日期、適用範圍）寫「資料中未提及」，不要補充；英文專有名詞保留原文。

{context}
"""
RECENT_DAYS = 30


def main() -> None:
    today = date.today()
    # Two ways to ask for "official sources, last month". Measure both before choosing one.
    configs = {"include_domains": dict(query=QUERY, include_domains=DOMAINS),
               "site: operators": dict(query=QUERY_SITE)}
    compare, results = [], {}
    for name, cfg in configs.items():
        req = dict(count=8, freshness="month", **cfg)
        res = web_search(extraction_mode="highlights", **req)
        save_sample("01_" + name.split(":")[0].replace(" ", "_"), {**req, "extraction": {"extraction_mode": "highlights"}}, res)
        hs = web_search_hits(res)
        old, undated = outside_window([days_old(h.get("page_age"), today) for h in hs], 31)
        official = sum(1 for h in hs if any(d in h["url"] for d in DOMAINS))
        compare.append({"config": name, "results": len(hs), "official": official, "outside_30d": old, "undated": undated})
        results[name] = (res, hs)
        print(f"{name:16} {compare[-1]}", file=sys.stderr)
    save_sample("01_compare", {"freshness": "month"}, {"rows": compare})
    print(f"{'configuration':16} {'results':>7} {'official':>8} {'>30 days':>9} {'undated':>8}")
    for c in compare:
        print(f"{c['config']:16} {c['results']:>7} {c['official']:>8} {c['outside_30d']:>9} {c['undated']:>8}\n", end="")
    res, hits = results["site: operators"]
    if not hits:
        sys.exit("No regulator pages in the last month: nothing to report.")

    allowed = {(h.get("page_age") or "")[:10] for h in hits} - {""}

    def entry(i, h):
        issuer = "HKMA" if "hkma.gov.hk" in h["url"] else "SFC"
        return (f"[{i}] 發布機構 {issuer} | {h.get('title', '')} — {h['url']} (page_age {(h.get('page_age') or 'N/A')[:10]}; "
                f"{days_old(h.get('page_age'), today)} 天前)\n{hit_text(h, 380)}")

    recent_ids = [i for i, h in enumerate(hits, 1)
                  if (days_old(h.get("page_age"), today) is not None and days_old(h.get("page_age"), today) <= RECENT_DAYS)]
    older_ids = [i for i in range(1, len(hits) + 1) if i not in recent_ids]
    context = ("【近期（30 天內）】\n" + "\n\n".join(entry(i, hits[i - 1]) for i in recent_ids)
               + "\n\n【較舊或日期未知】\n" + "\n\n".join(entry(i, hits[i - 1]) for i in older_ids))
    print(f"recent: {recent_ids} | older/undated: {older_ids}", file=sys.stderr)
    prompt = PROMPT.format(context=context)

    def check(text: str) -> list[str]:
        p = []
        if ungrounded_dates(text, allowed):
            p.append(f"日期不在來源中：{ungrounded_dates(text, allowed)}")
        if bad_citations(text, len(hits)):
            p.append(f"引用編號超出範圍：{bad_citations(text, len(hits))}")
        if simplified_chars(text):
            p.append(f"出現簡體字：{simplified_chars(text)}")
        missing = [i for i in recent_ids if f"[{i}]" not in text]
        if missing:
            p.append(f"近期來源沒有被涵蓋：{missing}")
        return p

    text, attempts = checked_chat(prompt, check)
    save_sample("01_brief", {"prompt": prompt, "attempts": attempts, "recent": recent_ids, "older": older_ids}, {"brief": text})
    print(f"checks: {attempts}", file=sys.stderr)
    print(text)


if __name__ == "__main__":
    main()

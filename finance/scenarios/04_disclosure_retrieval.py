"""Scenario 4 — Exchange filings: find them, read them in full, extract figures with verbatim evidence

Credit and relationship teams need the issuer's own filing, not an article about it. The search is limited to HKEXnews
with a `site:` operator in the query (which, unlike `include_domains`, keeps `freshness` strict: see scenario 1). Contents then reads the PDFs in full (an annual results announcement is ~100,000 characters), so the
code can tell whose filing each one is from its text, not from a search snippet. For the annual results announcement the
model extracts headline figures, and each figure must come with a quote that appears verbatim in the filing and that
contains the number; anything that fails is rejected. The filing date in the URL is compared with the date the index reports.
"""

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from finance_utils import hkex_url_date, norm, parse_date, quote_supported
from loop import checked_chat
from media_json import extract_json
from you_api import contents, content_text, save_sample, web_search, web_search_hits

ISSUER_TERMS = ["tencent", "騰訊"]
QUERY = "site:hkexnews.hk Tencent Holdings annual results announcement"
WINDOW = 15000  # characters of the filing handed to the model

PROMPT = """下面是一份港交所公告全文的開頭部分。請提取「截至 2025 年 12 月 31 日止年度」的：
Revenues、Operating profit、Profit attributable to equity holders of the Company（本年度數字），以及末期股息（每股）。
只輸出一個 JSON：{{"items": [{{"metric": str, "value": str, "unit": str, "quote": str}}]}}
quote 必須是公告原文中逐字出現的一段（表格的一行即可），且必須包含該數字；unit 照原文（例如 RMB in millions 或 HKD per share）。
找不到的項目不要編造，直接省略。

{text}
"""


def main() -> None:
    req = dict(query=QUERY, count=10, freshness="year")
    res = web_search(extraction_mode="highlights", **req)
    save_sample("04_search", {**req, "extraction": {"extraction_mode": "highlights"}}, res)
    hits = web_search_hits(res)
    print(f"hits: {len(hits)} | latency {res.get('metadata', {}).get('latency')}", file=sys.stderr)

    pages = contents([h["url"] for h in hits], formats=("markdown",))
    items = pages if isinstance(pages, list) else pages.get("results") or pages.get("contents") or []
    text_by_url = {it.get("url"): content_text(it) for it in items}
    save_sample("04_contents", {"urls": [h["url"] for h in hits], "formats": ["markdown"]},
                [{"url": u, "chars": len(t)} for u, t in text_by_url.items()])

    rows = []
    for h in hits:
        t = text_by_url.get(h["url"], "")
        n = sum(t.lower().count(w) for w in ISSUER_TERMS)
        filed, indexed = hkex_url_date(h["url"]), parse_date(h.get("page_age"))
        rows.append({"filed": filed, "indexed": indexed, "chars": len(t), "issuer_mentions": n, "url": h["url"],
                     "gap_days": (indexed - filed).days if filed and indexed else None,
                     "annual": "annual results" in t[:3000].lower() and "31 december 2025" in t[:6000].lower()})
    rows.sort(key=lambda r: (-r["issuer_mentions"], -(r["filed"] or date.min).toordinal()))

    print(f"{'filed (URL)':11} {'indexed':11} {'gap':>4} {'chars':>7} {'issuer mentions':>15}  annual-results")
    for r in rows:
        print(f"{str(r['filed']):11} {str(r['indexed']):11} {'' if r['gap_days'] is None else r['gap_days']:>4} {r['chars']:>7} "
              f"{r['issuer_mentions']:>15}  {'yes' if r['annual'] else ''}")
    mine = [r for r in rows if r["issuer_mentions"] >= 3]
    print(f"\n{len(mine)} of {len(rows)} results are the target issuer's filings (by full text); "
          f"{sum(1 for r in mine if r['gap_days'] not in (None, 0))} have an indexed date that differs from the URL date.")
    save_sample("04_table", {"issuer_terms": ISSUER_TERMS}, {"rows": [
        {k: (str(v) if isinstance(v, date) else v) for k, v in r.items()} for r in rows]})

    target = next((r for r in rows if r["annual"] and r["issuer_mentions"] >= 3), None)
    if not target:
        sys.exit("No annual results announcement among the results: nothing to extract.")
    text = text_by_url[target["url"]]
    prompt = PROMPT.format(text=text[:WINDOW])

    def check(reply: str) -> list[str]:
        data = extract_json(reply)
        if not data or not data.get("items"):
            return ["no items parsed"]
        problems = []
        for it in data["items"]:
            digits = "".join(c for c in str(it.get("value", "")) if c.isdigit() or c == ".")
            if not quote_supported(it.get("quote", ""), [text]):
                problems.append(f"{it.get('metric')}: quote not found verbatim in the filing")
            elif digits and digits not in norm(it["quote"]).replace(",", ""):
                problems.append(f"{it.get('metric')}: value {it.get('value')} not in its own quote")
        return problems

    reply, attempts = checked_chat(prompt, check)
    data = extract_json(reply) or {}
    save_sample("04_extraction", {"filing": target["url"], "window_chars": WINDOW, "attempts": attempts}, data)
    print(f"\nextraction from {target['url'][-34:]} (checks: {attempts}):")
    for it in data.get("items", []):
        print(f"- {it['metric']}: {it['value']} {it['unit']}\n    quote: {it['quote'][:110]}")


if __name__ == "__main__":
    main()

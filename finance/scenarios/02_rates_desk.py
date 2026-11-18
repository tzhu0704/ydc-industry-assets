"""Scenario 2 — Rates and market desk note (Knowledge + a sourced rule, arithmetic in code)

A treasury or economics desk needs today's numbers with their provider and date: HKD exchange rates, the US 10-year
yield, Hong Kong's base rate, inflation and GDP growth. Knowledge returns each as a dated record from a named provider.
The Linked Exchange Rate band is not hard-coded: it is read from HKMA's own page in the same run, and the code reports
where USD/HKD sits inside it. The model writes a short note from the finished table; every number in the note must come
from the table.
"""

import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from finance_utils import band_status, days_old, parse_peg_band, simplified_chars, ungrounded_numbers
from loop import checked_chat
from you_api import hit_text, knowledge_records, save_sample, web_search, web_search_hits

QUERIES = [
    ("USD/HKD", "USD to HKD exchange rate"),
    ("CNY/HKD", "CNY to HKD exchange rate"),
    ("US 10Y yield", "US 10-year treasury yield"),
    ("HK interest rate", "Hong Kong Monetary Authority base rate"),
    ("HK inflation", "Hong Kong inflation rate"),
    ("HK GDP growth", "Hong Kong GDP growth"),
]

PROMPT = """你是香港銀行資金部的市場簡報助手。下面是已經整理好的數據表（比較與差距由程式計算，數字不要改）。
用繁體中文寫 4 句話的晨間簡報：①港元匯率與聯繫匯率區間的位置 ②美國 10 年期收益率 ③香港利率、通脹與經濟增長 ④哪些數據偏舊。
每句話只在句末用一個括號標註該句所有數據的來源與日期（不要在每個數字後重複標註）；只能使用表中出現的數字；不要給出投資建議。

{table}
"""


def first_sentence(s: str, n: int = 150) -> str:
    return re.split(r"(?<=\.)\s", s, maxsplit=1)[0][:n]


def main() -> None:
    # 1) the band, read from the regulator rather than remembered
    bq = dict(query="Linked Exchange Rate System convertibility undertaking 7.75 7.85 HK$ per US$",
              include_domains=["hkma.gov.hk"], count=5)
    b = web_search(extraction_mode="highlights", **bq)
    save_sample("02_band", {**bq, "extraction": {"extraction_mode": "highlights"}}, b)
    band = parse_peg_band(" ".join(hit_text(h, 2000) for h in web_search_hits(b)))
    if not band:
        sys.exit("Could not read the 7.75 / 7.85 band from HKMA pages: not guessing it.")
    band_hit = next(h for h in web_search_hits(b) if "7.85" in hit_text(h, 2000))
    band_src, band_date = band_hit["url"], (band_hit.get("page_age") or "")[:10] or "頁面日期未給出"

    # 2) the records
    today, rows, text_rows, lat = date.today(), [], [], []
    for label, q in QUERIES:
        req = dict(query=q, knowledge="core", count=3)
        r = web_search(**req)
        save_sample(f"02_{label.replace('/', '').replace(' ', '_')}", req, r)
        lat.append(r.get("metadata", {}).get("latency"))
        recs = knowledge_records(r)
        if not recs:
            text_rows.append(f"{label} | 無記錄")
            continue
        rec = recs[0]
        age = days_old(rec.get("as_of"), today)
        text_rows.append(f"{label} | {first_sentence(rec['description'])} | 來源 {rec['attribution'][0]['name']} | 日期 {rec.get('as_of')} | {age} 天前")
        rows.append((label, rec))

    # 3) arithmetic in code
    usdhkd = next((r for lbl, r in rows if lbl == "USD/HKD"), None)
    m = re.search(r"current rate is ([0-9.]+) HKD per USD", usdhkd["description"]) if usdhkd else None
    if m:
        rate = float(m.group(1))
        gap = round(band[1] - rate, 5)
        text_rows.append(f"聯繫匯率區間 | {band[0]} 至 {band[1]} 港元兌 1 美元（來源 HKMA 頁面 {band_src}，頁面日期 {band_date}）| USD/HKD {rate}：{band_status(rate, band)}；距弱方兌換保證 {band[1]} 仍差 {gap}")
    table = "\n".join(text_rows)
    print(table + f"\n[latency per call: {[round(x, 2) for x in lat if x]}]", file=sys.stderr)

    prompt = PROMPT.format(table=table)

    def check(text: str) -> list[str]:
        p = []
        if ungrounded_numbers(text, table):
            p.append(f"這些數字不在數據表中：{ungrounded_numbers(text, table)}")
        if simplified_chars(text):
            p.append(f"出現簡體字：{simplified_chars(text)}")
        return p

    text, attempts = checked_chat(prompt, check)
    save_sample("02_table", {"band": band}, {"table": table, "latency": lat})
    save_sample("02_note", {"prompt": prompt, "attempts": attempts}, {"note": text})
    print(text)


if __name__ == "__main__":
    main()

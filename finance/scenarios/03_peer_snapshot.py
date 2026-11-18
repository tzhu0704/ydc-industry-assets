"""Scenario 3 — Peer bank snapshot (Knowledge: stock + financials, with a currency and period guard)

A strategy or investor-relations team wants a quick, sourced read on peer banks. Knowledge returns each bank's stock
overview and its latest-quarter revenue as dated records (S&P Global). The banks report in different currencies, so the
prompt forbids comparing revenue across currencies or periods and the note is checked in code: every number must be in
the records, and the text must be Traditional Chinese.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from finance_utils import simplified_chars, ungrounded_numbers
from loop import checked_chat
from you_api import knowledge_records, save_sample, web_search

PEERS = ["HSBC Holdings", "Standard Chartered", "DBS Group"]

PROMPT = """你是銀行策略部的同業分析助手。只依據下面的數據記錄，用繁體中文為每家銀行寫兩句話：
①股價：照記錄原樣寫價格（含貨幣符號）、交易所與代號、日期；市值照記錄原樣寫（含幣種）。
②最近一個季度的總收入：寫幣種與截至日期。
記錄裡的 $ 或 £ 符號照原樣寫，不要自行換成別的幣種；各銀行的上市地、報告幣種與季度可能不同，請先說明差異，不要直接比較。
日期一律使用記錄標註的日期（YYYY-MM-DD）。只能使用記錄中出現的數字；資料沒有的寫「資料中未提及」；不要給出投資建議。每個數字附上數據來源。

{context}
"""


def pick(recs: list[dict], key: str) -> dict | None:
    return next((r for r in recs if key.lower() in r["title"].lower()), None)


def main() -> None:
    blocks, source_text = [], ""
    for name in PEERS:
        for kind, q, key in (("stock", f"{name} stock price", "Stock Overview"),
                             ("revenue", f"{name} revenue latest quarter", "Total Revenues")):
            req = dict(query=q, knowledge="core", count=3)
            r = web_search(**req)
            save_sample(f"03_{name.split()[0]}_{kind}", req, r)
            rec = pick(knowledge_records(r), key)
            if not rec:
                print(f"{name} {kind}: no record", file=sys.stderr)
                continue
            line = (f"[{name} / {kind}] {rec['title']}: {rec['description'][:480]} "
                    f"(來源 {rec['attribution'][0]['name']}, 日期 {rec.get('as_of') or 'N/A'})")
            blocks.append(line)
            source_text += " " + line
    if not blocks:
        sys.exit("No records: no snapshot.")

    prompt = PROMPT.format(context="\n\n".join(blocks))

    def check(text: str) -> list[str]:
        p = []
        if ungrounded_numbers(text, source_text):
            p.append(f"這些數字不在記錄中：{ungrounded_numbers(text, source_text)}")
        if simplified_chars(text):
            p.append(f"出現簡體字：{simplified_chars(text)}")
        return p

    text, attempts = checked_chat(prompt, check)
    save_sample("03_note", {"prompt": prompt, "attempts": attempts}, {"note": text})
    print(f"checks: {attempts}", file=sys.stderr)
    print(text)


if __name__ == "__main__":
    main()

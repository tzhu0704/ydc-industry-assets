"""Scenario 6 — Multi-currency trip budget (knowledge FX, arithmetic done in code)

A Japan–Thailand–France trip is priced in three currencies. One Web Search call per currency pair
returns a dated, attributed FX record (`knowledge=core`). The conversion is done here in code, not by
the model, and a currency whose record is missing or in the wrong direction is reported as
"no rate" instead of being converted with a remembered number (that branch is covered by
tests/test_fx.py; every currency returned a rate in the live run). The model only writes the summary
from the finished table.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fx import parse_rate, to_cny
from you_api import chat, knowledge_records, save_sample, web_search

ITEMS = [  # (label, amount, currency)
    ("东京酒店 3 晚", 54000, "JPY"),
    ("东京—京都新干线往返", 28000, "JPY"),
    ("曼谷 SPA 与晚餐", 3500, "THB"),
    ("巴黎博物馆通票", 79, "EUR"),
    ("巴黎地铁与市内交通", 40, "EUR"),
    ("冰岛极光团", 250, "ISK"),
]

PROMPT = """下面是一份已经算好的出境游预算表（换算由程序完成，数字不要改）。
写 3 句话的总结：总额、最大的一项、哪些币种用了哪天的汇率。没有汇率的条目单独说明，不要估算。

{table}
"""


def main() -> None:
    rates: dict[str, dict] = {}
    for cur in sorted({c for _, _, c in ITEMS}):
        req = dict(query=f"{cur} to CNY exchange rate", knowledge="core", count=3)
        resp = web_search(**req)
        save_sample(f"06_{cur}", req, resp)
        rec = next((r for r in knowledge_records(resp) if parse_rate(r["description"], cur, "CNY")), None)
        if rec:
            rates[cur] = {"rate": parse_rate(rec["description"], cur, "CNY"),
                          "as_of": rec.get("as_of"), "source": rec["attribution"][0]["name"]}
        print(f"{cur}: {rates.get(cur, 'NO RATE')}", file=sys.stderr)

    rows, total = [], 0.0
    for label, amount, cur in ITEMS:
        if cur in rates:
            cny = to_cny(amount, rates[cur]["rate"])
            total += cny
            rows.append(f"{label} | {amount:,} {cur} | {rates[cur]['rate']} CNY/{cur} ({rates[cur]['source']}, {rates[cur]['as_of']}) | {cny:,.2f} CNY")
        else:
            rows.append(f"{label} | {amount:,} {cur} | 无汇率 | 未换算")
    table = "\n".join(rows) + f"\n已换算合计 | {total:,.2f} CNY"
    print(table)
    save_sample("06_table", {"items": ITEMS}, {"rates": rates, "table": table})

    out = chat(PROMPT.format(table=table))
    save_sample("06_answer", {"prompt": PROMPT.format(table=table)}, out)
    print("\n" + out["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()

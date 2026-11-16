"""Scenario 7 — Travel-platform market intelligence (knowledge + highlights)

For a platform's strategy team: how are the two big online travel agencies doing right now? Knowledge
returns dated financial and traffic records (Fiscal.ai, S&P Global, Semrush); Highlights returns the
recent news behind them. The model is told to quote each figure with its provider and period, to
not compare figures from different periods as if they were the same, and to say when a record has
no date.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from you_api import chat, hit_text, knowledge_records, save_sample, web_search, web_search_hits

KNOWLEDGE_QUERIES = {
    "ctrip_stock": "Trip.com Group stock price",
    "ctrip_revenue": "Trip.com Group revenue latest quarter",
    "ctrip_traffic": "trip.com monthly visits traffic",
    "booking_stock": "Booking Holdings stock price",
    "booking_revenue": "Booking Holdings revenue latest quarter",
    "booking_traffic": "Booking.com monthly visits traffic",
}
NEWS_QUERY = "Trip.com Group Booking Holdings travel demand outlook results"

PROMPT = """你是在线旅游平台战略团队的分析助手。只使用下面的资料写一份 250 字以内、用完整句子的对比简报：
Trip.com Group 与 Booking Holdings 的近期营收、流量、股价信号，以及新闻里的关键背景。
要求：①每个数字标注数据提供方、币种和所属期间/日期；②两家公司的营收所属季度或币种不同时，不要直接比较大小或增速，
先说明期间和币种；③某条记录没有日期时写“数据日期未给出”；④资料没有的内容写“资料中未提及”；
⑤新闻背景只写资料里明确出现的事件，并标注来源编号和页面日期。

{context}
"""


def main() -> None:
    blocks = []
    for name, q in KNOWLEDGE_QUERIES.items():
        req = dict(query=q, knowledge="core", count=3)
        resp = web_search(**req)
        save_sample(f"07_{name}", req, resp)
        recs = knowledge_records(resp)
        print(f"{name}: {len(recs)} record(s)", file=sys.stderr)
        for r in recs[:1]:
            blocks.append(f"[KNOWLEDGE/{name}] {r['title']}: {r['description'][:420]} "
                          f"(source: {r['attribution'][0]['name']}, as of {r.get('as_of') or 'N/A'})")
    nq = dict(query=NEWS_QUERY, freshness="month", count=5)
    news = web_search(extraction_mode="highlights", **nq)
    save_sample("07_news", {**nq, "extraction": {"extraction_mode": "highlights"}}, news)
    for i, h in enumerate(web_search_hits(news), 1):
        blocks.append(f"[NEWS {i}] {h.get('title','')} — {h['url']} (page_age {h.get('page_age','N/A')})\n{hit_text(h, 350)}")

    prompt = PROMPT.format(context="\n\n".join(blocks))
    out = chat(prompt)
    save_sample("07_answer", {"prompt": prompt}, out)
    print(out["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()

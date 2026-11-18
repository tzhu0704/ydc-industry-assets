"""Scenario 6 — Bilingual policy Q&A (language targeting, official sources, answer in Traditional Chinese)

A Hong Kong bank answers customers and staff in Traditional Chinese, Simplified Chinese and English. The same question
about a cross-boundary programme is run in three languages against the regulators' sites with `language` set, and the
script measures what comes back: how many results are dated, how many are within a year, and how many have text in the
requested language (judged from the passage itself, not the URL). The Traditional Chinese answer is then written
from those pages and checked in code: citations must exist, numbers and dates must come from the sources, no Simplified
characters.
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from finance_utils import bad_citations, content_language, days_old, simplified_chars, ungrounded_numbers
from loop import checked_chat
from you_api import hit_text, save_sample, web_search, web_search_hits

DOMAINS = ["hkma.gov.hk", "sfc.hk"]
QUESTIONS = {
    "ZH-HANT": "財富管理互聯互通 合資格投資者 條件",
    "EN": "Wealth Management Connect eligible investors requirements",
    "ZH-HANS": "财富管理互联互通 合资格投资者 条件",
}

PROMPT = """你是香港銀行的客戶服務知識助手。客戶問：「財富管理互聯互通的合資格投資者有什麼條件？」
只依據下面編號的官方來源，用繁體中文回答。每個結論後標註來源編號 [n] 與該來源的 page_age 日期（YYYY-MM-DD）。
來源沒有寫明的條件（例如具體金額）寫「資料中未提及」，不要補充；來源之間不一致的列在最後的「需人工確認」。

{context}
"""


def main() -> None:
    today, rows, answer_hits = date.today(), [], []
    for lang, q in QUESTIONS.items():
        req = dict(query=q, count=10, include_domains=DOMAINS, language=lang)
        res = web_search(extraction_mode="highlights", **req)
        save_sample(f"06_{lang}", {**req, "extraction": {"extraction_mode": "highlights"}}, res)
        hits = web_search_hits(res)
        dated = [h for h in hits if h.get("page_age")]
        rows.append({"language": lang, "n": len(hits), "dated": len(dated),
                     "within_1y": sum(1 for h in dated if (days_old(h["page_age"], today) or 9999) <= 365),
                     "in_language": sum(1 for h in hits if content_language(hit_text(h, 3000)) == lang),
                     "latency": res.get("metadata", {}).get("latency")})
        print(f"{lang:8} {rows[-1]}", file=sys.stderr)
        if lang == "ZH-HANT":
            answer_hits = hits

    print(f"{'language':8} {'results':>7} {'dated':>6} {'<=1y':>5} {'text in that language':>21}")
    for r in rows:
        print(f"{r['language']:8} {r['n']:>7} {r['dated']:>6} {r['within_1y']:>5} {r['in_language']:>21}")
    save_sample("06_table", {"questions": QUESTIONS}, {"rows": rows})

    top = answer_hits[:5]
    if not top:
        sys.exit("No Traditional Chinese results: no answer.")
    context = "\n\n".join(f"[{i}] {h.get('title', '')} — {h['url']} (page_age {(h.get('page_age') or 'N/A')[:10]})\n{hit_text(h, 700)}"
                          for i, h in enumerate(top, 1))
    source_text = context
    prompt = PROMPT.format(context=context)

    def check(text: str) -> list[str]:
        p = []
        if bad_citations(text, len(top)):
            p.append(f"引用編號超出範圍：{bad_citations(text, len(top))}")
        if ungrounded_numbers(text, source_text):
            p.append(f"這些數字不在來源中：{ungrounded_numbers(text, source_text)}")
        if simplified_chars(text):
            p.append(f"出現簡體字：{simplified_chars(text)}")
        return p

    text, attempts = checked_chat(prompt, check)
    save_sample("06_answer", {"prompt": prompt, "attempts": attempts}, {"answer": text})
    print(f"\nchecks: {attempts}\n")
    print(text)


if __name__ == "__main__":
    main()

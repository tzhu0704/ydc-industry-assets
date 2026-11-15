"""Scenario 4 — Supplier due diligence: who runs it, and is it still true? (People Search + Web Search)

A travel platform onboarding a tour operator or hotel wants to know who is behind it. Two sources,
two jobs:
  - People Search (POST /v1/people/search, standalone): structured profiles by role / place /
    organisation — current title, tenure, and trust signals (`authenticity_score`,
    `consistency_score`, `source_count`, `last_updated_at`).
  - Web Search + highlights (freshness=year): what the web says about that company *now*.

The model must not treat a thin profile as fact: it is told to report the trust signals next to each
claim and to list anything it could not corroborate. Person records are redacted before they are
written to samples/ (names, links and bios are dropped).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from you_api import chat, hit_text, people_search, redact_person, save_sample, web_search, web_search_hits

PEOPLE_QUERY = "founder of a tour operator in Kyoto"

PROMPT = """你是旅游平台的供应商尽调助手。目标：{q}
下面有两类资料：[PEOPLE] 来自 People Search 的结构化人物档案，[WEB] 来自近一年的网页摘录。
请输出：①候选人表（公司、职位、任职月数、地点）；②每位候选人的可信度信号
（authenticity_score、consistency_score、source_count、last_updated_at）；③[WEB] 是否印证了
该公司仍在运营——引用来源编号和页面日期；④“未能确认”：档案过薄、分数偏低、或网页没有印证的结论。
不要补充资料里没有的信息。人物姓名已脱敏，不要尝试还原。

{context}
"""


def person_line(i: int, p: dict) -> str:
    pos = p.get("current_position", {})
    return (f"[PEOPLE {i}] company={pos.get('company')} title={pos.get('title')} "
            f"months_in_role={pos.get('months_in_role','N/A')} location={p.get('location')} "
            f"authenticity_score={p.get('authenticity_score')} consistency_score={p.get('consistency_score','N/A')} "
            f"source_count={p.get('source_count')} last_updated_at={p.get('last_updated_at')}")


def main() -> None:
    people_resp = people_search(PEOPLE_QUERY, count=3)
    people = people_resp.get("results", [])
    print(f"people: {len(people)}", file=sys.stderr)
    if not people:
        sys.exit("People Search returned nothing — not guessing.")
    save_sample("04_people", {"query": PEOPLE_QUERY, "count": 3},
                {"results": [redact_person(p) for p in people]})

    lines, web_blocks = [], []
    for i, p in enumerate(people, 1):
        lines.append(person_line(i, p))
        company = p.get("current_position", {}).get("company")
        if not company:
            continue
        q = f"{company} {p.get('location','')}".strip()
        w = web_search(q, extraction_mode="highlights", freshness="year", count=3)
        save_sample(f"04_web_{i}", {"query": q, "freshness": "year", "extraction": {"extraction_mode": "highlights"}}, w)
        for j, h in enumerate(web_search_hits(w), 1):
            web_blocks.append(f"[WEB {i}.{j}] {h.get('title','')} — {h['url']} (page_age {h.get('page_age','N/A')})\n{hit_text(h, 300)}")

    context = "\n".join(lines) + "\n\n" + "\n\n".join(web_blocks)
    answer = chat(PROMPT.format(q=PEOPLE_QUERY, context=context))
    save_sample("04_answer", {"prompt": PROMPT.format(q=PEOPLE_QUERY, context=context)}, answer)
    print(answer["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()

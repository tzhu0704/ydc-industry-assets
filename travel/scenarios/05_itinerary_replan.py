"""Scenario 5 — Itinerary re-plan around the forecast (knowledge + highlights)

The traveller already has a three-day plan. Knowledge supplies the dated forecast; Highlights
(country + freshness) supplies current indoor alternatives. The model may only move existing
items between days or swap in an alternative that appears in the retrieved passages, and must cite
the forecast line behind every move.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from you_api import chat, hit_text, knowledge_records, save_sample, web_search, web_search_hits

PLAN = [
    ("Day 1", "浅草寺 + 隅田川步行", "outdoor"),
    ("Day 2", "新宿御苑 + 明治神宫", "outdoor"),
    ("Day 3", "teamLab Planets", "indoor"),
]

PROMPT = """你是行程助手。用户未来三天在东京，原计划如下：
{plan}

只使用下面的资料重新安排：①天气只能引用 [WEATHER] 里的预报，每次调整都要写出依据的那一行（日期、天气）；
②可以在三天之间调换原有项目（原有项目不需要引用来源）；要新增室内项目时，只能用 [INDOOR] 资料中明确出现的，并标注来源编号和页面日期，票价、闭馆日只引用该来源原文；
③资料没有覆盖的（票价、预约、开放时间）写“资料中未提及”。输出：新行程表 + 每次调整的理由。

[WEATHER]
{weather}

[INDOOR]
{indoor}
"""


def main() -> None:
    wq = dict(query="Tokyo weather forecast this week", knowledge="core", count=3)
    w = web_search(**wq)
    save_sample("05_weather", wq, w)
    recs = knowledge_records(w)
    if not recs:
        sys.exit("No forecast record — refusing to re-plan without one.")
    weather = f"{recs[0]['description']} (source: {recs[0]['attribution'][0]['name']}, as of {recs[0].get('as_of')})"

    iq = dict(query="Tokyo indoor attractions for a rainy day museum exhibition", country="JP",
              freshness="month", count=5)
    mode = "highlights"
    h = web_search(extraction_mode=mode, **iq)
    save_sample("05_indoor", {**iq, "extraction": {"extraction_mode": mode}}, h)
    hits = web_search_hits(h)
    indoor = "\n\n".join(f"[{i}] {x.get('title','')} — {x['url']} (page_age {x.get('page_age','N/A')})\n{hit_text(x, 350)}"
                         for i, x in enumerate(hits, 1))

    plan = "\n".join(f"{d}: {item}（{kind}）" for d, item, kind in PLAN)
    prompt = PROMPT.format(plan=plan, weather=weather, indoor=indoor)
    out = chat(prompt)
    save_sample("05_answer", {"prompt": prompt}, out)
    print(out["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()

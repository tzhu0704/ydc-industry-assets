"""Scenario 1 — Pre-trip briefing (knowledge + highlights, client-side harness mode)

A mainland-China traveller is about to leave for Tokyo. A good travel agent answers
three different kinds of question, and each wants a different kind of evidence:
  - "What will the weather be?"      -> a number with a date, not a page   (knowledge)
  - "How much is 10,000 CNY in JPY?" -> a live rate with its source        (knowledge)
  - "Anything new I should know?"    -> the specific passages, recent only (highlights)

Three Web Search calls on the same endpoint, one prompt, one briefing. Every figure in
the briefing carries the provider and `as_of` date it came from.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from you_api import chat, hit_text, knowledge_records, save_sample, web_search, web_search_hits

DESTINATION = "Tokyo"
BUDGET_CNY = 10000

CALLS = {
    "weather": dict(query=f"{DESTINATION} weather forecast this week", knowledge="core", count=3),
    "fx": dict(query="CNY to JPY exchange rate", knowledge="core", count=3),
    "news": dict(
        query=f"{DESTINATION} tourist attractions closures events travel notice",
        extraction_mode="highlights", freshness="month", country="JP", count=5,
    ),
}

PROMPT = """你是一位出境游行程助手。用户是中国大陆游客，下周去{dest}，预算 {budget} 元人民币。
只使用下面的资料写一份简短的行前简报：①天气与穿衣 ②预算折合日元 ③近期需要注意的事。
每个数字后标注来源和日期。资料里没有的内容写“资料中未提及”，不要补充猜测。

{context}
"""


def build_context(results: dict[str, dict]) -> str:
    blocks = []
    for name in ("weather", "fx"):
        for rec in knowledge_records(results[name])[:1]:
            src = rec.get("attribution", [{}])[0].get("name", "")
            blocks.append(f"[KNOWLEDGE/{name}] {rec.get('title','')}: {rec.get('description','')} "
                          f"(as of {rec.get('as_of','N/A')}, source: {src})")
    for i, hit in enumerate(web_search_hits(results["news"]), 1):
        blocks.append(f"[NEWS {i}] {hit.get('title','')} — {hit.get('url','')} "
                      f"(page_age {hit.get('page_age','N/A')})\n{hit_text(hit)}")
    return "\n\n".join(blocks)


def main() -> None:
    results = {}
    for name, call in CALLS.items():
        call = dict(call)
        query = call.pop("query")
        mode = call.pop("extraction_mode", None)
        print(f"[{name}] {query!r}", file=sys.stderr)
        results[name] = web_search(query, extraction_mode=mode, **call)
        body = {"query": query, **{k: v for k, v in call.items()},
                **({"extraction": {"extraction_mode": mode}} if mode else {})}
        save_sample(f"01_{name}", body, results[name])
        print(f"  knowledge={len(knowledge_records(results[name]))} web={len(web_search_hits(results[name]))}",
              file=sys.stderr)

    prompt = PROMPT.format(dest=DESTINATION, budget=BUDGET_CNY, context=build_context(results))
    briefing = chat(prompt)
    save_sample("01_briefing", {"prompt": prompt}, briefing)
    print(briefing["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()

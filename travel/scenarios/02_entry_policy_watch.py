"""Scenario 2 — Entry-policy watch (official domains + freshness + language, client-side mode)

"Do I need a visa?" is the question where a stale or SEO-farm answer costs the traveller
a missed flight. Scope retrieval to the destination's own government / tourism-board sites
(`include_domains`), ask for the last year only (`freshness`), and return the Chinese-language
page where one exists (`language`). The model is told to quote the rule, give the page's own
date, and say so when the official sources do not settle the question.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from you_api import chat, hit_text, save_sample, web_search, web_search_hits

QUERY = "中国大陆护照 赴日本 签证 入境 要求 电子签 Visit Japan Web"
OFFICIAL = ["mofa.go.jp", "jnto.go.jp", "japan.travel", "immi.moj.go.jp", "vjw-lp.digital.go.jp",
            "cn.emb-japan.go.jp"]

PROMPT = """你是出境游合规助手。用户持中国大陆护照，计划赴日本旅游。
只依据下面的官方来源回答：是否需要签证、办理方式、入境时需要准备什么。
要求：①每条结论引用来源编号和该页面的日期（page_age）；②来源之间不一致或没有明确说明的，
单独列在“未能确认”里，不要用常识补全；③最后一行给出建议用户出发前再核对的官方页面。

{context}
"""


def main() -> None:
    body = dict(count=8, include_domains=OFFICIAL, freshness="year", language="ZH-HANS")
    print(f"Query: {QUERY!r}\nDomains: {OFFICIAL}", file=sys.stderr)
    result = web_search(QUERY, extraction_mode="highlights", **body)
    save_sample("02_entry_policy", {"query": QUERY, "extraction": {"extraction_mode": "highlights"}, **body}, result)

    hits = web_search_hits(result)
    print(f"official hits: {len(hits)}", file=sys.stderr)
    for h in hits:
        print(f"  {h.get('page_age','?')[:10]}  {h['url']}", file=sys.stderr)
    if not hits:
        sys.exit("No official-domain results — refusing to answer from nothing.")

    context = "\n\n".join(
        f"[{i}] {h.get('title','')} — {h['url']} (page_age {h.get('page_age','N/A')})\n{hit_text(h, 600)}"
        for i, h in enumerate(hits, 1)
    )
    answer = chat(PROMPT.format(context=context))
    save_sample("02_entry_answer", {"prompt": PROMPT.format(context=context)}, answer)
    print(answer["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()

"""Scenario 2 — Trend radar for a creator (freshness + highlights, then Contents)

"What is trending this week?" is a script-ideation question and a sound-selection question. Web Search with
`freshness=week` returns this week's roundup pages; Contents then reads the top pages in full so the code can
pull concrete, checkable items out of them (here: Instagram Reels audio ids) instead of asking the model to
recall them. The model writes a short brief from the highlights and is given the counts the code found.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from media_utils import extract_audio_ids
from you_api import chat, contents, content_text, hit_text, save_sample, web_search, web_search_hits

QUERY = "trending Instagram audio reels this week"

PROMPT = """你是短视频创作者的趋势分析助手。只依据下面的资料，写一份 200 字以内的“本周趋势简报”：
①资料里明确点名的热门音频/玩法（逐条写，标注来源编号和页面日期）；
②代码从各页面全文里抽取到的音频 ID 数量只作参考，说明它是第三方页面列出的，未经平台核实；
③资料没有给出排名依据的，不要自己排名；资料没有的写“资料中未提及”。

{context}
"""


def main() -> None:
    req = dict(query=QUERY, count=5, freshness="week")
    res = web_search(extraction_mode="highlights", **req)
    save_sample("02_trends", {**req, "extraction": {"extraction_mode": "highlights"}}, res)
    hits = web_search_hits(res)
    print(f"hits: {len(hits)}", file=sys.stderr)
    if not hits:
        sys.exit("No results from the last week — nothing to report.")

    top = [h["url"] for h in hits[:3]]
    pages = contents(top)
    items = pages if isinstance(pages, list) else pages.get("results") or pages.get("contents") or []
    save_sample("02_contents", {"urls": top, "formats": ["markdown"]},
                [{"url": it.get("url"), "markdown_chars": len(content_text(it))} for it in items])
    counts = {it.get("url"): len(extract_audio_ids(content_text(it))) for it in items}
    print(f"audio ids per page: {counts}", file=sys.stderr)

    lines = [f"[{i}] {h.get('title','')} — {h['url']} (page_age {h.get('page_age','N/A')})\n{hit_text(h, 350)}"
             for i, h in enumerate(hits, 1)]
    lines.append("[CODE] 全文抽取到的 Instagram Reels 音频 ID 数量：" + "; ".join(f"{u} = {n}" for u, n in counts.items()))
    prompt = PROMPT.format(context="\n\n".join(lines))
    out = chat(prompt)
    save_sample("02_brief", {"prompt": prompt}, out)
    print(out["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()

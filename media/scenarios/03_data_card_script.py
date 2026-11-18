"""Scenario 3 — Data-card voice-over with every number grounded (knowledge, validated in code)

Automatic "today's numbers" videos (price, air quality, rate) fail when a model rounds, mixes up or
invents a figure. Knowledge supplies each figure as a dated record; the model writes the voice-over and
on-screen text; code then checks that every number it wrote appears in the records. A failing script is sent
back once with the offending numbers listed.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from media_utils import extract_json, numbers_in, ungrounded_numbers
from you_api import chat, knowledge_records, save_sample, web_search

QUERIES = {"bitcoin": "Bitcoin price today", "air": "Beijing air quality today", "fx": "USD to CNY exchange rate"}

PROMPT = """你是财经/生活类短视频的文案助手。用下面三条带日期的数据，写一条约 20 秒的口播和屏幕字幕。
规则：①只能使用资料里出现的数字，原样引用，不要四舍五入、不要换算、不要新增数字；
②口播要口语化、用中文说法（例如“11月18日”“华氏”“每个比特币”），不要出现英文时间戳或英文单位；但数字一律写阿拉伯数字，口播和屏幕字幕里都一样，不要写成汉字数字；
③每条数据后用口语说明来源和日期；④不要给出投资或健康建议。
只输出一个 JSON：{{"voice_over": str, "on_screen": [str]}}

{context}
"""


def check(script: dict, source_text: str) -> list[str]:
    """Numbers not found in the records, plus numbers shown on screen but missing from the voice-over
    (a figure spelled out in words would otherwise escape the check)."""
    voice, screen = script.get("voice_over", ""), " ".join(script.get("on_screen", []))
    bad = ungrounded_numbers(voice + " " + screen, source_text)
    bad += [f"{n} (on screen, not in voice-over as a digit)" for n in sorted(numbers_in(screen) - numbers_in(voice))]
    return bad


def main() -> None:
    blocks, source_text = [], ""
    for key, q in QUERIES.items():
        req = dict(query=q, knowledge="core", count=3)
        r = web_search(**req)
        save_sample(f"03_{key}", req, r)
        recs = knowledge_records(r)
        if not recs:
            print(f"{key}: no knowledge record — leaving it out", file=sys.stderr)
            continue
        rec = recs[0]
        text = f"{rec['title']}: {rec['description'][:500]} (source: {rec['attribution'][0]['name']}, as of {rec.get('as_of') or 'N/A'})"
        blocks.append(f"[{key}] {text}")
        source_text += " " + text
    if not blocks:
        sys.exit("No data records — no script.")

    prompt = PROMPT.format(context="\n\n".join(blocks))
    attempts, script = [], None
    for attempt in (1, 2):
        p = prompt if attempt == 1 else prompt + f"\n\n上一版未通过校验：{bad}。请改用资料中的数字（阿拉伯数字，口播与字幕一致），重新输出完整 JSON。"
        reply = chat(p)["choices"][0]["message"]["content"]
        script = extract_json(reply)
        bad = check(script, source_text) if script else ["(invalid JSON)"]
        attempts.append({"attempt": attempt, "ungrounded_numbers": bad})
        print(f"attempt {attempt}: ungrounded numbers = {bad}", file=sys.stderr)
        if not bad:
            break
    save_sample("03_result", {"prompt": prompt, "attempts": attempts}, {"script": script})
    if bad:
        sys.exit(f"Numbers still not grounded after repair: {bad}")
    print(json.dumps(script, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

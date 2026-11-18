"""Scenario 1 — Shot script (camera-movement script) planned from live facts (knowledge + highlights)

A creator asks for a 30-second teaser of a landmark. A good shot script depends on facts a model
does not hold: when the light is good *today*, what the weather will do, what is closed or
restricted right now, and whether a drone may fly there. This script collects those facts with
Web Search and then asks the model for a structured shot list.

The shot list is checked in code before anyone sees it: durations must sum to the target, every
camera move must come from a fixed vocabulary, every cited source id must exist, a drone shot must cite
a drone-rules source, and the shoot window must equal the golden-hour window computed here from the
sourced sunset time. Failures are fed back to the model once.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from media_utils import (CAMERA_MOVES, extract_json, golden_hour_window, parse_sunset,
                         validate_shot_script)
from you_api import chat, hit_text, knowledge_records, save_sample, web_search, web_search_hits

TOPIC = "Senso-ji Temple, Tokyo"
TOTAL_SECONDS = 30
DRONE_DOMAINS = ["mlit.go.jp", "japan.travel", "jnto.go.jp", "city.taito.tokyo.jp"]

PROMPT = """你是短视频的分镜/运镜脚本助手。为“{topic}”写一条 {total} 秒的旅行预告片分镜脚本。

只能使用下面编号的资料里的事实；每个镜头的 facts 字段列出用到的资料编号（没有用到就留空数组）。
资料没有覆盖的内容（例如某处是否允许拍摄）不要假设，写进 unverified。
拍摄时间窗必须原样使用：{window}（已由程序根据 [W] 里的日落时间算出）。
camera_move 只能取：{moves}。
如果要用无人机镜头，必须引用无人机规则资料的编号，且 voice_over 不得暗示“可以随意飞”。
只输出一个 JSON 对象，格式：
{{"title": str, "total_seconds": {total}, "shoot_window": "{window}",
 "shots": [{{"n": int, "seconds": int, "camera_move": str, "framing": str, "subject": str,
            "voice_over": str, "facts": [资料编号]}}], "unverified": [str]}}
所有镜头的 seconds 之和必须等于 {total}。

{context}
"""


def collect() -> tuple[str, set[str], set[str], tuple[int, int]]:
    blocks, ids, drone_ids = [], set(), set()

    wq = dict(query="Tokyo weather forecast today sunset", knowledge="core", count=3)
    w = web_search(**wq)
    save_sample("01_weather", wq, w)
    recs = knowledge_records(w)
    if not recs:
        sys.exit("No forecast record — cannot plan light. Stopping.")
    sunset = parse_sunset(recs[0]["description"])
    if not sunset:
        sys.exit("Forecast record has no sunset time — refusing to guess the golden hour.")
    blocks.append(f"[W] {recs[0]['description'][:700]} (source: {recs[0]['attribution'][0]['name']}, as of {recs[0].get('as_of')})")
    ids.add("W")

    venue = dict(query=f"{TOPIC} opening hours closures notice photography", country="JP", freshness="month", count=4)
    drone = dict(query="drone flight rules tourists Japan permission populated areas Tokyo", include_domains=DRONE_DOMAINS,
                 freshness="year", count=4)
    for tag, req, prefix in (("venue", venue, "V"), ("drone", drone, "D")):
        r = web_search(extraction_mode="highlights", **req)
        save_sample(f"01_{tag}", {**req, "extraction": {"extraction_mode": "highlights"}}, r)
        for i, h in enumerate(web_search_hits(r), 1):
            sid = f"{prefix}{i}"
            ids.add(sid)
            if prefix == "D":
                drone_ids.add(sid)
            blocks.append(f"[{sid}] {h.get('title','')} — {h['url']} (page_age {h.get('page_age','N/A')})\n{hit_text(h, 380)}")
    return "\n\n".join(blocks), ids, drone_ids, sunset


def main() -> None:
    context, ids, drone_ids, sunset = collect()
    window = golden_hour_window(sunset)
    print(f"sources: {sorted(ids)} | drone-rules sources: {sorted(drone_ids)} | window: {window}", file=sys.stderr)

    prompt = PROMPT.format(topic=TOPIC, total=TOTAL_SECONDS, window=window,
                           moves=" / ".join(CAMERA_MOVES), context=context)
    script, problems, attempts = None, [], []
    for attempt in (1, 2):
        reply = chat(prompt if attempt == 1 else prompt + "\n\n上一版未通过程序校验，问题如下，请修正后重新输出完整 JSON：\n- "
                     + "\n- ".join(problems))
        text = reply["choices"][0]["message"]["content"]
        script = extract_json(text)
        problems = validate_shot_script(script, ids, drone_ids, TOTAL_SECONDS, window) if script else ["reply was not valid JSON"]
        attempts.append({"attempt": attempt, "problems": problems})
        print(f"attempt {attempt}: {'PASS' if not problems else problems}", file=sys.stderr)
        save_sample(f"01_script_attempt{attempt}", {"prompt": prompt if attempt == 1 else "(repair prompt)"},
                    {"reply": text, "problems": problems})
        if not problems:
            break

    save_sample("01_result", {"topic": TOPIC, "window": window, "attempts": attempts}, {"script": script})
    if problems:
        sys.exit(f"Script still failing validation after repair: {problems}")
    print(json.dumps(script, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

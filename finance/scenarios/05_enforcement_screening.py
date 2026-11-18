"""Scenario 5 — Enforcement and adverse-media screening, grounded in regulator text

Screening teams refresh watch-lists from regulator enforcement notices. Retrieval is limited to the regulators' own sites with `site:` operators (which keep `freshness` strict) and the code drops anything outside the window again;
the model extracts who was sanctioned, what the action was and when, and every item must carry a quote that appears
verbatim in the cited source. Items whose quote cannot be found are rejected and sent back once. The prompt states two
rules the output is held to: it does not conclude anything about anyone not named in a source, and "nothing found" is
never presented as "cleared".
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from finance_utils import dates_in, quote_supported, simplified_chars
from loop import checked_chat
from media_json import extract_json
from you_api import hit_text, save_sample, web_search, web_search_hits

QUERY = "(site:sfc.hk OR site:hkma.gov.hk) SFC disciplinary action reprimands fines licensed corporation representative"
WINDOW_DAYS = 365

PROMPT = """你是銀行合規的制裁／負面新聞篩查助手。只依據下面編號的監管機構來源，提取其中明確記載的執法行動。
只輸出一個 JSON：{{"actions": [{{"subject": str, "action": str, "amount": str, "date": str, "source": int, "quote": str}}]}}
規則：
①quote 必須是該來源（source 編號對應的那一條）原文中逐字出現的一句話（至少 12 個字元），且能支持 subject 與 action；
②date 只能用該來源裡寫明的日期，或該來源的 page_age（YYYY-MM-DD）；來源沒寫的 amount 填「未提及」；
③不要對來源中沒有出現的任何人或機構下結論；沒有執法行動的來源直接略過；
④最多列 6 項。

{context}
"""


def main() -> None:
    req = dict(query=QUERY, count=8, freshness="year")
    res = web_search(extraction_mode="highlights", **req)
    save_sample("05_search", {**req, "extraction": {"extraction_mode": "highlights"}}, res)
    hits = web_search_hits(res)
    from datetime import date
    from finance_utils import days_old
    stale = [h for h in hits if (days_old(h.get("page_age"), date.today()) or 99999) > WINDOW_DAYS]  # undated counts as stale
    hits = [h for h in hits if h not in stale]
    print(f"kept {len(hits)} sources inside {WINDOW_DAYS} days, dropped {len(stale)} older/undated", file=sys.stderr)
    texts = [hit_text(h, 4000) for h in hits]
    ages = [(h.get("page_age") or "")[:10] for h in hits]
    print(f"sources: {len(hits)} | latency {res.get('metadata', {}).get('latency')}", file=sys.stderr)
    if not hits:
        sys.exit("No regulator sources: absence of results is not a clearance. Stopping.")

    context = "\n\n".join(f"[{i}] {h.get('title', '')} — {h['url']} (page_age {ages[i - 1] or 'N/A'})\n{texts[i - 1][:1800]}"
                          for i, h in enumerate(hits, 1))
    prompt = PROMPT.format(context=context)

    def check(reply: str) -> list[str]:
        data = extract_json(reply)
        if data is None or "actions" not in data:
            return ["reply was not the requested JSON"]
        problems = []
        for k, a in enumerate(data["actions"], 1):
            src = a.get("source")
            if not isinstance(src, int) or not 1 <= src <= len(hits):
                problems.append(f"action {k}: bad source {src!r}")
                continue
            if not quote_supported(a.get("quote", ""), [texts[src - 1]]):
                problems.append(f"action {k}: quote is not verbatim in source [{src}]")
            allowed = dates_in(texts[src - 1]) | ({ages[src - 1]} if ages[src - 1] else set())
            if a.get("date") and not (dates_in(a["date"]) <= allowed or a["date"] in texts[src - 1]):
                problems.append(f"action {k}: date {a['date']!r} is not in source [{src}]")
        return problems

    reply, attempts = checked_chat(prompt, check)
    data = extract_json(reply) or {"actions": []}
    save_sample("05_extraction", {"prompt": prompt, "attempts": attempts}, data)
    print(f"checks: {attempts}", file=sys.stderr)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"\n{len(data['actions'])} action(s) extracted from {len(hits)} sources. "
          "Zero results for a name would NOT mean the name is clear: coverage is limited to these sources.")


if __name__ == "__main__":
    main()

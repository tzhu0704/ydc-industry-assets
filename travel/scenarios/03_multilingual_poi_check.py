"""Scenario 3 — Same question, three languages (no model in the loop)

An international-travel app gets the same question in Chinese, English and Japanese, and
the user is standing in the destination. This script runs one question per language
and reports measurable properties of what comes back — result count, share with a
page date, share dated within 30 days, and how many distinct sites — with and without
`country` + `freshness`. No judge model: the numbers are the evidence, so a reader can rerun
the script and compare.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from you_api import save_sample, web_search, web_search_hits

QUESTIONS = {
    "ZH-HANS": ["东京 浅草寺 开放时间 最近 人多吗", "京都 清水寺 红叶 最佳观赏时间 今年", "大阪 环球影城 近期 闭园 维护 通知"],
    "EN": ["Senso-ji Tokyo opening hours and crowds right now", "Kiyomizu-dera Kyoto autumn leaves best time this year",
           "Universal Studios Japan Osaka maintenance closure notice"],
    "JA": ["浅草寺 拝観時間 混雑 最新", "清水寺 紅葉 見頃 今年", "ユニバーサル・スタジオ・ジャパン 休止 メンテナンス お知らせ"],
}


def parse_age(s: str | None):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "")).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def measure(hits: list[dict]) -> dict:
    now = datetime.now(timezone.utc)
    ages = [parse_age(h.get("page_age")) for h in hits]
    dated = [a for a in ages if a]
    return {
        "results": len(hits),
        "dated": len(dated),
        "within_30d": sum(1 for a in dated if now - a <= timedelta(days=30)),
        "sites": len({urlparse(h["url"]).netloc for h in hits}),
        "with_highlights": sum(1 for h in hits if h.get("contents", {}).get("highlights")),
    }


def main() -> None:
    rows, samples = [], {}
    for lang, qs in QUESTIONS.items():
        for mode, extra in (("default", {}), ("country+freshness", {"country": "JP", "freshness": "month"})):
            agg = {"results": 0, "dated": 0, "within_30d": 0, "sites": 0, "with_highlights": 0}
            for q in qs:
                res = web_search(q, extraction_mode="highlights", count=10, language=lang, **extra)
                samples[f"{lang}|{mode}|{q}"] = [
                    {"url": h["url"], "page_age": h.get("page_age")} for h in web_search_hits(res)
                ]
                for k, v in measure(web_search_hits(res)).items():
                    agg[k] += v
            rows.append((lang, mode, agg))
            print(f"{lang:8} {mode:18} {agg}", file=sys.stderr)

    save_sample("03_multilingual", {"questions": QUESTIONS}, {"summary": [
        {"language": l, "mode": m, **a} for l, m, a in rows], "hits": samples})

    print(f"{'lang':8} {'mode':18} {'results':>7} {'dated%':>7} {'<=30d%':>7} {'sites':>6} {'highlights%':>11}")
    for lang, mode, a in rows:
        n = max(a["results"], 1)
        print(f"{lang:8} {mode:18} {a['results']:>7} {100*a['dated']/n:>6.0f}% "
              f"{100*a['within_30d']/n:>6.0f}% {a['sites']:>6} {100*a['with_highlights']/n:>10.0f}%")


if __name__ == "__main__":
    main()

"""Pure helpers for the financial-services scenarios (no network; unit-tested in tests/test_finance.py)."""

import re
from datetime import date, datetime

# Characters that exist only in Simplified Chinese (their Traditional forms differ). A small, curated list:
# enough to flag a "Traditional Chinese" answer that slipped into Simplified, not a full converter.
SIMPLIFIED_ONLY = set("这国银费务来对时发资产条规则会员实现关门问题经济开设让过达进选单据项户议网级统储币种额总应办贷约证监险转账个为与业动备")
_NUM = re.compile(r"\d[\d,]*\.?\d*")
_HKEX_DATE = re.compile(r"/(\d{4})/(\d{2})(\d{2})/")


def parse_date(s: str | None) -> date | None:
    """'2026-11-18T..' or '2026-11-18' -> date; None when absent/unparseable."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "")[:19]).date()
    except ValueError:
        try:
            return date.fromisoformat(s[:10])
        except ValueError:
            return None


def days_old(as_of: str | None, today: date) -> int | None:
    d = parse_date(as_of)
    return (today - d).days if d else None


def hkex_url_date(url: str) -> date | None:
    """HKEXnews paths look like /listedco/listconews/sehk/2026/0318/<file>.pdf -> 2026-03-18."""
    m = _HKEX_DATE.search(url or "")
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def numbers_in(text: str) -> set[str]:
    out = set()
    for n in _NUM.findall(text or ""):
        n = n.replace(",", "").rstrip(".")
        if "." in n:
            n = n.rstrip("0").rstrip(".")
        if n:
            out.add(n)
    return out


def ungrounded_numbers(answer: str, source_text: str) -> list[str]:
    src = numbers_in(source_text)
    return sorted(n for n in numbers_in(answer) if n not in src)


def parse_peg_band(text: str) -> tuple[float, float] | None:
    """Find the Linked Exchange Rate band (e.g. 7.75 and 7.85 HK$ per US$) in official text; None if not both present."""
    vals = {float(v) for v in re.findall(r"\b7\.[0-9]{2}\b", text or "")}
    return (min(vals), max(vals)) if {7.75, 7.85} <= vals else None


def band_status(rate: float, band: tuple[float, float]) -> str:
    lo, hi = band
    if rate < lo:
        return "below the band (strong side)"
    if rate > hi:
        return "above the band (weak side)"
    pos = (rate - lo) / (hi - lo)
    return f"inside the band ({pos:.0%} of the way from the strong side to the weak side)"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def quote_supported(quote: str, source_texts: list[str]) -> bool:
    """True when `quote` appears verbatim (whitespace/case-insensitive) in at least one source text."""
    q = norm(quote)
    return len(q) >= 12 and any(q in norm(t) for t in source_texts)


def simplified_chars(text: str) -> list[str]:
    return sorted({c for c in text or "" if c in SIMPLIFIED_ONLY})


_ISO = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
_CITE = re.compile(r"\[(\d+)\]")


def dates_in(text: str) -> set[str]:
    return set(_ISO.findall(text or ""))


def ungrounded_dates(answer: str, allowed: set[str]) -> list[str]:
    """ISO dates written in `answer` that are not among the dates supplied as evidence."""
    return sorted(d for d in dates_in(answer) if d not in allowed)


def bad_citations(answer: str, n_sources: int) -> list[str]:
    """Cited source numbers [k] that are outside 1..n_sources."""
    return sorted({m for m in _CITE.findall(answer or "") if not 1 <= int(m) <= n_sources}, key=int)


def content_language(text: str) -> str:
    """Rough language of a passage: 'EN' (little CJK), 'ZH-HANS' (several Simplified-only characters) or 'ZH-HANT'."""
    cjk = sum("\u4e00" <= c <= "\u9fff" for c in text or "")
    if cjk < 40:
        return "EN"
    return "ZH-HANS" if len(simplified_chars(text)) >= 3 else "ZH-HANT"


def outside_window(ages: list[int | None], limit_days: int) -> tuple[int, int]:
    """(older than the window, undated) among page ages in days."""
    return (sum(1 for a in ages if a is not None and a > limit_days), sum(1 for a in ages if a is None))


def median(xs: list[float]) -> float | None:
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    mid = len(xs) // 2
    return xs[mid] if len(xs) % 2 else (xs[mid - 1] + xs[mid]) / 2

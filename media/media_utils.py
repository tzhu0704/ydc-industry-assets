"""Pure helpers for the media scenarios (no network; unit-tested in tests/test_media.py)."""

import re
from urllib.parse import urlparse

STOCK_DOMAINS = (
    "shutterstock.com", "istockphoto.com", "gettyimages.com", "alamy.com", "adobe.com",
    "stock.adobe.com", "depositphotos.com", "123rf.com", "dreamstime.com", "freepik.com",
    "vecteezy.com", "pond5.com", "storyblocks.com",
)
_IMG_EXT = re.compile(r"\.(jpe?g|png|webp|gif|avif)(\?|#|$)", re.I)
_MEDIA_EXT = re.compile(r"https?://[^\s\"')>\]]+\.(?:jpe?g|png|webp|mp4|mov|webm|mp3|wav)(?:\?[^\s\"')>\]]*)?", re.I)
_AUDIO_ID = re.compile(r"instagram\.com/reels/audio/(\d+)")
_NUM = re.compile(r"\d[\d,]*\.?\d*")


def host(url: str) -> str:
    return urlparse(url or "").netloc.lower().removeprefix("www.")


def is_stock(url_or_source: str) -> bool:
    h = host(url_or_source) or (url_or_source or "").lower()
    return any(h == d or h.endswith("." + d) or d.split(".")[0] in h for d in STOCK_DOMAINS)


def is_direct_image(url: str) -> bool:
    """True when the URL itself points at an image file (not a page or a proxy endpoint)."""
    return bool(url) and bool(_IMG_EXT.search(urlparse(url).path))


def on_topic(text: str, key_terms: list[str]) -> bool:
    """Keyword match (any key term, case-insensitive). Not human judgment: a cheap, repeatable proxy."""
    t = (text or "").lower()
    return any(k.lower() in t for k in key_terms)


def extract_audio_ids(markdown: str) -> list[str]:
    """Distinct Instagram Reels audio ids found in page text, in order of first appearance."""
    seen: dict[str, None] = {}
    for m in _AUDIO_ID.findall(markdown or ""):
        seen.setdefault(m, None)
    return list(seen)


def extract_media_urls(text: str, min_thumb: int = 400) -> list[str]:
    """Distinct image/video/audio file URLs in page text or HTML, in order of first appearance.

    Skips wiki file *pages*, SVG/icon/favicon/logo assets and small thumbnails (a '/NNNpx-' path segment below `min_thumb`).
    """
    seen: dict[str, None] = {}
    for m in _MEDIA_EXT.finditer((text or "").replace("\\/", "/")):
        url = m.group(0)
        if "/wiki/File:" in url or "/wiki/Image:" in url or re.search(r"\.svg|favicon|/plugins/|/themes/|logo|sprite|icon", url, re.I):
            continue
        t = re.search(r"/(\d+)px-", url)
        if t and int(t.group(1)) < min_thumb:
            continue
        seen.setdefault(url, None)
    return list(seen)


def numbers_in(text: str) -> set[str]:
    """Numbers as normalised strings (commas removed, trailing '.' stripped, '0.50' -> '0.5')."""
    out = set()
    for n in _NUM.findall(text or ""):
        n = n.replace(",", "").rstrip(".")
        if "." in n:
            n = n.rstrip("0").rstrip(".")
        if n:
            out.add(n)
    return out


def ungrounded_numbers(script: str, source_text: str) -> list[str]:
    """Numbers in `script` that do not appear in `source_text` (sorted). Empty list = every number is grounded."""
    src = numbers_in(source_text)
    return sorted(n for n in numbers_in(script) if n not in src)


CAMERA_MOVES = ("static", "push-in", "pull-out", "pan", "tilt", "tracking", "handheld", "crane", "drone-orbit", "drone-rise")


def parse_sunset(text: str):
    """(hour, minute) 24h from 'sunset is at 4:34 PM' style text; None if absent."""
    m = re.search(r"sunset is at (\d{1,2}):(\d{2}) ?([AP]M)", text or "", re.I)
    if not m:
        return None
    h, mi, ap = int(m.group(1)) % 12, int(m.group(2)), m.group(3).upper()
    return (h + (12 if ap == "PM" else 0), mi)


def golden_hour_window(sunset: tuple[int, int]) -> str:
    """Rule of thumb used by the script, not a sourced fact: the hour before sunset, 'HH:MM-HH:MM'."""
    total = sunset[0] * 60 + sunset[1]
    start = total - 60
    return f"{start // 60:02d}:{start % 60:02d}-{sunset[0]:02d}:{sunset[1]:02d}"


def extract_json(text: str):
    """First top-level JSON object in a model reply (tolerates ```json fences and prose around it)."""
    import json
    s = text or ""
    start = s.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(s)):
            c = s[i]
            if in_str:
                esc = (c == "\\" and not esc)
                if c == '"' and not esc:
                    in_str = False
                continue
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(s[start:i + 1])
                    except ValueError:
                        break
        start = s.find("{", start + 1)
    return None


def validate_shot_script(script: dict, source_ids: set[str], drone_source_ids: set[str],
                         total_seconds: int, window: str) -> list[str]:
    """Deterministic checks on a shot script; returns a list of problems (empty = passes)."""
    problems = []
    shots = script.get("shots") if isinstance(script, dict) else None
    if not shots:
        return ["no shots"]
    total = 0
    for s in shots:
        n = s.get("n")
        if s.get("camera_move") not in CAMERA_MOVES:
            problems.append(f"shot {n}: camera_move {s.get('camera_move')!r} not in vocabulary")
        sec = s.get("seconds")
        if not isinstance(sec, (int, float)) or sec <= 0:
            problems.append(f"shot {n}: bad seconds {sec!r}")
        else:
            total += sec
        facts = s.get("facts") or []
        bad = [f for f in facts if f not in source_ids]
        if bad:
            problems.append(f"shot {n}: cites unknown sources {bad}")
        if str(s.get("camera_move", "")).startswith("drone") and not (set(facts) & drone_source_ids):
            problems.append(f"shot {n}: drone shot without a cited drone-rules source")
    if total != total_seconds:
        problems.append(f"durations sum to {total}, expected {total_seconds}")
    if script.get("shoot_window") != window:
        problems.append(f"shoot_window {script.get('shoot_window')!r} != computed {window!r}")
    return problems

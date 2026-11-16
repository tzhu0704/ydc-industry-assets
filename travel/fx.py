"""Deterministic helpers for the multi-currency budget scenario (no network, unit-tested)."""

import re

_RATE = re.compile(r"current rate is ([0-9][0-9,]*\.?[0-9]*) ([A-Z]{3}) per ([A-Z]{3})")


def parse_rate(description: str, base: str, quote: str) -> float | None:
    """Rate as `quote per base` from a knowledge FX record; None if the text is not that pair."""
    m = _RATE.search(description or "")
    if not m:
        return None
    value, q, b = float(m.group(1).replace(",", "")), m.group(2), m.group(3)
    return value if (b, q) == (base, quote) else None


def to_cny(amount: float, rate_cny_per_unit: float) -> float:
    return round(amount * rate_cny_per_unit, 2)

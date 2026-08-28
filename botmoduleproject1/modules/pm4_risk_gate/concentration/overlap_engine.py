"""FX currency overlap: base/quote, USD block, European basket."""

from __future__ import annotations

from botmoduleproject1.modules.pm4_risk_gate.domain.policies import EUROPEAN_MAJORS


def split_pair(symbol: str) -> tuple[str, str]:
    text = symbol.strip().upper().replace("/", "")
    if len(text) >= 6:
        return text[:3], text[3:6]
    return text, ""


def currencies(symbol: str) -> frozenset[str]:
    base, quote = split_pair(symbol)
    return frozenset(c for c in (base, quote) if c)


def cluster_id(symbol: str) -> str:
    text = symbol.strip().upper().replace("/", "")
    base, quote = split_pair(text)
    if text in EUROPEAN_MAJORS:
        return "european_majors"
    pair = {base, quote}
    if "USD" in pair:
        other = next(iter(pair - {"USD"}), "USD")
        return f"usd_block:{other}"
    return f"{base}|{quote}"


def usd_weight(symbol: str) -> float:
    return 1.0 if "USD" in currencies(symbol) else 0.0


def european_weight(symbol: str) -> float:
    text = symbol.strip().upper().replace("/", "")
    return 1.0 if text in EUROPEAN_MAJORS else 0.0

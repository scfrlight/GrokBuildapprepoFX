"""Base/quote overlap clusters. Pair-agnostic."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from botmoduleproject1.modules.pm2_market_context.domain.ids import cluster_id


class CorrelationView(BaseModel):
    model_config = ConfigDict(frozen=True)
    symbol: str
    base: str
    quote: str
    cluster: str


def split_symbol(symbol: str) -> tuple[str, str]:
    text = symbol.upper().replace("/", "")
    if len(text) >= 6:
        return text[:3], text[3:6]
    return text, "USD"


def view_for(symbol: str) -> CorrelationView:
    base, quote = split_symbol(symbol)
    return CorrelationView(symbol=symbol, base=base, quote=quote, cluster=cluster_id(base, quote))


def shared_currency(a: str, b: str) -> bool:
    va, vb = view_for(a), view_for(b)
    return va.base in {vb.base, vb.quote} or va.quote in {vb.base, vb.quote}

"""Typed handoff from public PM2 artifacts into SymbolPipe."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.pm2 import PublicationBundle, RankedCandidate


class PM2HandoffService:
    def candidates(self, bundle: PublicationBundle) -> tuple[RankedCandidate, ...]:
        seen: dict[str, RankedCandidate] = {}
        for item in bundle.shortlist + bundle.watchlist:
            seen[item.symbol] = item
        return tuple(seen.values())

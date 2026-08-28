"""Feature provenance metadata attached to every snapshot."""

from __future__ import annotations

from botmoduleproject1.modules.pm2_market_context.features.builder import FeatureSnapshot


def provenance_of(snapshot: FeatureSnapshot) -> dict[str, str]:
    return dict(snapshot.provenance)

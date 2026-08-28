"""Optional GMM adapter. Disabled in Sequence 03 — not a QRF/ML layer."""

from __future__ import annotations

from botmoduleproject1.modules.pm2_market_context.features.builder import FeatureSnapshot


class GmmAdapter:
    enabled = False

    def infer(self, snapshot: FeatureSnapshot) -> None:
        return None

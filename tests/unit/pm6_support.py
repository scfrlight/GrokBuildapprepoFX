"""Shared fixtures for PM6 post-trade tests."""

from __future__ import annotations

from datetime import datetime

from botmoduleproject1.modules.pm6_post_trade.config.schema import Pm6PostTradeConfig
from botmoduleproject1.modules.pm6_post_trade.module import PM6PostTradeModule
from tests.unit.pm4_support import AS_OF
from tests.unit.pm5_support import Clock, ingest_allow, pm5_module


def pm6_module(*, clock: Clock | None = None, config: Pm6PostTradeConfig | None = None, **kwargs) -> PM6PostTradeModule:
    return PM6PostTradeModule(
        config or Pm6PostTradeConfig(),
        clock or Clock(),
        feature_enabled=kwargs.get("feature_enabled", True),
        surveillance_enabled=kwargs.get("surveillance_enabled", True),
        incident_enabled=kwargs.get("incident_enabled", True),
        governance_enabled=kwargs.get("governance_enabled", True),
        withdrawal_enabled=kwargs.get("withdrawal_enabled", True),
    )


def observe_allow(module: PM6PostTradeModule | None = None, key: str = "pm6-ok"):
    pm6 = module or pm6_module()
    _exe, bundle, pub = ingest_allow(key=key)
    truth = pm6.observe(pub, bundle)
    return pm6, bundle, pub, truth

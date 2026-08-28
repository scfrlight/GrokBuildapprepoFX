"""Safety invariants: no orders, no side mutation, no forbidden imports."""

from __future__ import annotations

from pathlib import Path

from botmoduleproject1.contracts.v1.strategy import Direction
from tests.unit.pm3fx_support import confirmed_bars, forecasting_module, make_intent

ROOT = Path(__file__).resolve().parents[2]
MODULE_ROOT = ROOT / "botmoduleproject1" / "modules" / "pm3_forecasting"


def test_forecast_does_not_mutate_intent_or_volume() -> None:
    intent = make_intent(direction=Direction.BUY, key="safe")
    before = intent.model_dump()
    mod = forecasting_module()
    out = mod.forecast_with_bars(intent, confirmed_bars())
    assert out is not None
    assert intent.model_dump() == before
    assert intent.requested_volume is None
    assert intent.direction is Direction.BUY


def test_forecast_is_not_an_order() -> None:
    mod = forecasting_module()
    out = mod.forecast_with_bars(make_intent(key="not-order"), confirmed_bars())
    assert out is not None
    dumped = out.model_dump()
    blob = str(dumped)
    assert "OrderRequest" not in blob
    assert "lot" not in blob.lower()
    assert out.producer == "pm3_forecasting"
    assert "direction" not in dumped


def test_no_forbidden_imports() -> None:
    blob = "\n".join(p.read_text(encoding="utf-8") for p in MODULE_ROOT.rglob("*.py"))
    assert "from botmoduleproject1.adapters.mt5" not in blob
    assert "from botmoduleproject1.modules.pm5_execution" not in blob
    assert "from botmoduleproject1.adapters.telegram" not in blob
    assert "from botmoduleproject1.modules.pm4_risk" not in blob
    assert "from botmoduleproject1.modules.pm3_strategy_engine" not in blob
    assert "import sklearn" not in blob
    assert "from sklearn" not in blob
    assert "import numpy" not in blob
    assert "from numpy" not in blob
    assert "import pandas" not in blob
    assert "from pandas" not in blob
    assert "import MetaTrader5" not in blob
    assert "from MetaTrader5" not in blob
    assert "import aiogram" not in blob
    assert "from aiogram" not in blob

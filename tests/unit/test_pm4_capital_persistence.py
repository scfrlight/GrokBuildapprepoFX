"""Capital-gate persistence: SQLite plus live PostgreSQL when a DSN is present."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from botmoduleproject1.contracts.v1.pm4_capital import CapitalDecisionState, QuantileBand, RiskEvaluationRequest
from botmoduleproject1.contracts.v1.time import UTC
from botmoduleproject1.modules.pm4_risk_gate.capital.evaluation import CapitalEvaluationService
from botmoduleproject1.modules.pm4_risk_gate.config.schema import Pm4RiskGateConfig
from botmoduleproject1.modules.pm8_persistence.api.v1 import PersistenceApiV1
from botmoduleproject1.modules.pm8_persistence.migrations import MigrationService
from botmoduleproject1.modules.pm8_persistence.money import canonical
from botmoduleproject1.modules.pm8_persistence.postgres.embedded import discover_dsn, start_embedded_postgres
from botmoduleproject1.modules.pm8_persistence.postgres.store import PostgresStore
from botmoduleproject1.modules.pm8_persistence.store import SqliteStore
from tests.unit.pm4_support import _Clock

AS_OF = datetime(2026, 1, 15, 14, 0, tzinfo=UTC)


def _band() -> QuantileBand:
    return QuantileBand(
        q05=Decimal("1.09600"),
        q25=Decimal("1.09800"),
        q50=Decimal("1.10000"),
        q75=Decimal("1.10200"),
        q95=Decimal("1.10400"),
    )


def make_request(**overrides) -> RiskEvaluationRequest:
    payload = dict(
        request_id=str(uuid4()),
        idempotency_key=overrides.pop("idempotency_key", f"p-{uuid4().hex[:10]}"),
        correlation_id=str(uuid4()),
        causation_id=str(uuid4()),
        trade_intent_id=str(uuid4()),
        strategy_id="trend_pullback",
        strategy_version="v1",
        profile_id="trend_pullback",
        profile_version="v1",
        symbol="EURUSD",
        side="buy",
        requested_quantity=Decimal("1.00"),
        entry_price=Decimal("1.10000"),
        stop_loss_price=Decimal("1.09500"),
        take_profit_price=Decimal("1.11000"),
        signal_timestamp=AS_OF,
        intent_created_at=AS_OF,
        market_snapshot_id="mkt",
        regime_snapshot_id="reg",
        model_snapshot_id="model-1",
        model_version="0.1.0",
        model_quality_status="ok",
        predicted_quantiles=_band(),
        spread=Decimal("0.00010"),
        estimated_slippage=Decimal("0.00010"),
        estimated_commission=Decimal("2"),
        account_snapshot_id="acct",
        portfolio_snapshot_id="port",
        current_positions_snapshot_id="pos",
        current_orders_snapshot_id="ord",
        risk_policy_version="1.0.0",
        execution_policy_version="sim-1",
        account_equity=Decimal("100000"),
        peak_equity=Decimal("100000"),
        free_margin=Decimal("100000"),
        conversion_rate=Decimal("1"),
        contract_size=Decimal("100000"),
        volume_step=Decimal("0.01"),
        session="london",
        regime="trending",
        market_age_seconds=1,
        account_age_seconds=1,
        portfolio_age_seconds=1,
        model_age_seconds=1,
        reconciliation_status="ok",
        control_state="active",
        persistence_available=True,
    )
    payload.update(overrides)
    return RiskEvaluationRequest(**payload)


def _svc(api, config=None) -> CapitalEvaluationService:
    return CapitalEvaluationService(
        config or Pm4RiskGateConfig(),
        clock=_Clock(AS_OF),
        persistence=api,
        require_persistence=True,
    )


def test_sqlite_money_canonical_and_idempotent_restart(tmp_path: Path) -> None:
    store = SqliteStore(tmp_path / "cap.sqlite")
    api = PersistenceApiV1(store)
    svc = _svc(api)
    req = make_request(idempotency_key="sql-1")
    first = svc.evaluate(req)
    assert first.decision.final_decision in {
        CapitalDecisionState.APPROVED,
        CapitalDecisionState.APPROVED_REDUCED_SIZE,
    }
    events = [ev for ev in api.store.list_events(limit=1000) if ev["event_type"] == "risk.decision.committed"]
    assert events
    payload = events[-1]["payload_json"]
    if isinstance(payload, str):
        import json

        payload = json.loads(payload)
    assert payload["qty"] == canonical(first.decision.approved_quantity)
    assert payload["price"] == canonical(req.entry_price)
    assert payload["risk_amount"] == canonical(first.decision.monetary_risk)
    reopened = PersistenceApiV1(SqliteStore(tmp_path / "cap.sqlite"))
    again = _svc(reopened).evaluate(req)
    assert again.decision.decision_id == first.decision.decision_id


def _pg_dsn() -> str:
    found = discover_dsn()
    if found:
        return found
    return start_embedded_postgres()


@pytest.fixture
def pg_api():
    dsn = _pg_dsn()
    schema = "c_" + uuid4().hex[:12]
    store = PostgresStore(dsn, schema_name=schema, connect_timeout=5)
    MigrationService(store).upgrade_to(2)
    yield PersistenceApiV1(store)
    ident = schema.replace('"', "")
    try:
        store.conn.execute(f'DROP SCHEMA IF EXISTS "{ident}" CASCADE')
    except Exception:
        pass
    store.close()


@pytest.mark.postgres
def test_postgres_numeric_capital_decision(pg_api):
    svc = _svc(pg_api)
    req = make_request(idempotency_key="pg-cap-1")
    result = svc.evaluate(req)
    assert result.decision.final_decision in {
        CapitalDecisionState.APPROVED,
        CapitalDecisionState.APPROVED_REDUCED_SIZE,
    }
    assert result.decision.execution_permitted is False
    events = [ev for ev in pg_api.store.list_events(limit=1000) if ev.get("event_type") == "risk.decision.committed"]
    assert events
    raw = events[-1].get("payload_json")
    if isinstance(raw, str):
        import json

        raw = json.loads(raw)
    assert raw["qty"] == canonical(result.decision.approved_quantity)
    assert raw["price"] == canonical(req.entry_price)
    assert raw["risk_amount"] == canonical(result.decision.monetary_risk)
    cur = pg_api.store.conn.execute(
        "SELECT amount_canonical, data_type FROM money_records "
        "JOIN information_schema.columns ON 1=0"
    ) if False else pg_api.store.conn.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema=current_schema() AND table_name='money_records' AND column_name='amount_canonical'"
    )
    col = cur.fetchone()
    assert col is not None
    assert "numeric" in str(col["data_type"]).lower()
    amount = pg_api.store.conn.execute(
        "SELECT amount_canonical FROM money_records WHERE field='qty' ORDER BY committed_at DESC LIMIT 1"
    ).fetchone()
    assert amount is not None
    assert Decimal(str(amount["amount_canonical"])) == Decimal(raw["qty"])
    again = _svc(pg_api).evaluate(req)
    assert again.decision.output_hash == result.decision.output_hash


@pytest.mark.postgres
def test_postgres_drawdown_restart(pg_api):
    first = _svc(pg_api)
    first.evaluate(make_request(idempotency_key="pg-dd-1", account_equity=Decimal("100000"), peak_equity=Decimal("100000")))
    restarted = _svc(pg_api)
    blocked = restarted.evaluate(
        make_request(
            idempotency_key="pg-dd-2",
            account_equity=Decimal("91000"),
            peak_equity=Decimal("91000"),
        )
    )
    assert blocked.decision.final_decision is CapitalDecisionState.BLOCKED_DRAWDOWN
    assert restarted.ledger.peak_equity == Decimal("100000")

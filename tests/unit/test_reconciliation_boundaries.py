"""Architectural reconciliation invariants (post-Sequence 14). Not Sequence 15."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from uuid import uuid4

import pytest

from botmoduleproject1.app.container import build_container
from botmoduleproject1.app.exceptions import ExecutionDisabledError, LiveTradingDisabledError
from botmoduleproject1.app.feature_flags import FEATURE_FLAG_CATALOG
from botmoduleproject1.app.lifecycle import LifecycleState
from botmoduleproject1.app.sequence_gate import CANONICAL_SEQUENCES
from botmoduleproject1.app.settings import load_settings
from botmoduleproject1.app.stubs import DisabledExecution, NullLedger, NullMonitoring, NullOperator, NullStorage
from botmoduleproject1.cli.entrypoint import main
from botmoduleproject1.contracts.v1.persistence import IngestDisposition, IntegrityState, JournalCategory, ReplayScope
from botmoduleproject1.contracts.v1.pm8_persistence import ApiDisposition, PersistenceApiVersion, TableFamily
from botmoduleproject1.modules.observability.health_model import evaluate
from botmoduleproject1.modules.observability.module import OBSERVABILITY_METADATA, ObservabilityModule
from botmoduleproject1.modules.pm6_post_trade.module import PM6PostTradeModule
from botmoduleproject1.modules.pm8_persistence.api.v1 import PersistenceApiV1
from botmoduleproject1.modules.pm8_persistence.store import SqliteStore

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "botmoduleproject1"
TEST_YAML = ROOT / "configs" / "test.example.yaml"
BASE_YAML = ROOT / "configs" / "base.example.yaml"

FORBIDDEN_EXECUTION_IMPORTS = (
    "botmoduleproject1.modules.pm5_execution.oms",
    "botmoduleproject1.modules.pm5_execution.ems",
    "botmoduleproject1.adapters.mt5",
    "botmoduleproject1.modules.mt5_execution_engine",
    "MetaTrader5",
)
PM4_SIZING_IMPORT = "botmoduleproject1.modules.pm4_risk_gate.sizing"
ORDER_VERBS = ("submit", "send_order", "place_order", "broker_send")


def _py_files(relative: str) -> list[Path]:
    return sorted((PKG / relative).rglob("*.py"))


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
    return found


def test_numbering_map_consistency_00_to_14():
    text = (ROOT / "docs" / "MODULE_NUMBERING_MAP.md").read_text(encoding="utf-8")
    for n in range(15):
        assert f"| {n:02d} |" in text
    assert "pm6_post_trade" in text
    assert "mt5_execution_engine" in text
    assert "modules/observability" in text
    assert "modules/pm6_execution" in text
    assert CANONICAL_SEQUENCES[8] == "pm6_post_trade_controls"
    assert CANONICAL_SEQUENCES[9] == "pm8_database_consolidation"
    assert CANONICAL_SEQUENCES[11] == "mt5_execution_engine"
    assert not CANONICAL_SEQUENCES[11].startswith("pm6")
    assert CANONICAL_SEQUENCES[14] == "observability_operations_documentation"
    assert 15 not in CANONICAL_SEQUENCES


def test_observability_is_not_pm6():
    assert OBSERVABILITY_METADATA.name == "observability"
    assert OBSERVABILITY_METADATA.name != "pm6_monitoring"
    readme = (PKG / "modules" / "observability" / "README.md").read_text(encoding="utf-8")
    assert "Not PM6" in readme
    settings = load_settings(config_path=TEST_YAML, environ={}, cli_mode="observe")
    container = build_container(settings)
    obs = container.registry.get("observability").instance
    mon = container.registry.get("pm6_monitoring").instance
    assert isinstance(obs, ObservabilityModule)
    assert isinstance(mon, NullMonitoring)
    assert not isinstance(obs, PM6PostTradeModule)


def test_all_catalog_flags_default_false():
    settings = load_settings(config_path=BASE_YAML, environ={}, cli_mode="doctor")
    enabled = settings.feature_flags.enabled_map()
    assert enabled
    assert all(value is False for value in enabled.values())
    assert all(spec.default is False for spec in FEATURE_FLAG_CATALOG)


def test_default_binds_are_null_or_disabled():
    settings = load_settings(config_path=TEST_YAML, environ={}, cli_mode="doctor")
    container = build_container(settings)
    assert container.registry.get("pm4_risk").instance.__class__.__name__ == "NullRiskGate"
    assert isinstance(container.registry.get("pm5_execution").instance, DisabledExecution)
    assert isinstance(container.registry.get("pm6_monitoring").instance, NullMonitoring)
    assert isinstance(container.registry.get("pm7_ledger").instance, NullLedger)
    assert isinstance(container.registry.get("pm8_persistence").instance, NullStorage)
    assert isinstance(container.registry.get("pm8_operator").instance, NullOperator)


def test_pm6_module_cannot_submit_orders_or_size_risk():
    from tests.unit.pm6_support import pm6_module

    pm6 = pm6_module()
    for verb in ORDER_VERBS:
        assert not hasattr(pm6, verb), f"PM6 must not expose {verb}"
    assert not hasattr(pm6, "sizer")
    assert not hasattr(pm6, "oms")
    for path in _py_files("modules/pm6_post_trade"):
        imported = _imports(path)
        assert PM4_SIZING_IMPORT not in imported
        for banned in FORBIDDEN_EXECUTION_IMPORTS:
            assert banned not in imported, f"{path} imports {banned}"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in ORDER_VERBS:
                raise AssertionError(f"{path} defines {node.name}")


def test_observability_cannot_submit_orders():
    settings = load_settings(config_path=TEST_YAML, environ={}, cli_mode="observe")
    obs = ObservabilityModule.from_settings(settings, clock=None)
    for verb in ORDER_VERBS:
        assert not hasattr(obs, verb)
    for path in _py_files("modules/observability"):
        imported = _imports(path)
        for banned in FORBIDDEN_EXECUTION_IMPORTS:
            assert banned not in imported
        assert PM4_SIZING_IMPORT not in imported


def test_sequence_14_cannot_set_trading_readiness_true():
    settings = load_settings(config_path=TEST_YAML, environ={}, cli_mode="observe")
    health, ready = evaluate(
        settings,
        lifecycle=LifecycleState.RUNNING,
        persistence_ok=True,
        persistence_enabled=True,
        integrity_ok=True,
        stale_data=False,
        operator_bound=True,
    )
    assert health.trading_readiness is False
    assert ready.accept_trade is False
    source = (PKG / "modules" / "observability" / "health_model.py").read_text(encoding="utf-8")
    assert "trading_readiness=True" not in source
    assert "accept_trade=True" not in source


def test_pm7_pm8_not_broker_adapters():
    for rel in ("modules/pm7_persistence", "modules/pm8_persistence"):
        for path in _py_files(rel):
            imported = _imports(path)
            assert "botmoduleproject1.adapters.mt5" not in imported
            assert "MetaTrader5" not in imported
            text = path.read_text(encoding="utf-8")
            assert "def submit(" not in text


def test_pm8_checkpoint_monotonic(tmp_path: Path):
    api = PersistenceApiV1(SqliteStore(tmp_path / "mono.sqlite"))
    api.ingest_event(
        event_type="t",
        producer="recon",
        family=TableFamily.EVENT,
        payload={"n": 1},
    )
    first = api.checkpoint()
    second = api.checkpoint()
    assert int(second["cursor_seq"]) >= int(first["cursor_seq"])
    with pytest.raises(ValueError, match="monotonic"):
        api.store.save_checkpoint(
            {
                "checkpoint_id": "backwards",
                "cursor_seq": int(first["cursor_seq"]) - 1,
                "payload_json": "{}",
                "created_at": "2020-01-01T00:00:00+00:00",
            }
        )
    latest = api.latest_checkpoint()
    assert latest is not None
    assert int(latest["cursor_seq"]) == int(second["cursor_seq"])


def test_pm8_named_projections_are_not_claimed_complete():
    """Operator dashboard / performance projections are PARTIAL/absent — do not invent them."""
    matrix = (ROOT / "docs" / "PM8_PM8A_GAP_MATRIX.md").read_text(encoding="utf-8")
    for name in (
        "open orders",
        "closed trades",
        "symbol performance",
        "profile performance",
        "daily summary",
        "operator dashboard",
    ):
        assert name in matrix.lower()
    assert "ABSENT" in matrix or "PARTIAL" in matrix


def test_pm7_status_is_partial_evidence_journal():
    inventory = (ROOT / "docs" / "ARCHITECTURE_INVENTORY.md").read_text(encoding="utf-8")
    assert "PARTIAL" in inventory
    assert "evidence-journal" in inventory.lower() or "evidence journal" in inventory.lower()
    assert "production_durable" in inventory.lower() or "not production durable" in inventory.lower()
    readme = (PKG / "modules" / "pm7_persistence" / "README.md").read_text(encoding="utf-8")
    assert "PARTIAL" in readme


def test_pm7_append_only_correction_lineage():
    from tests.unit.pm7_support import make_event, pm7_module

    mod = pm7_module()
    first = mod.ingest(make_event())
    assert first.disposition is IngestDisposition.COMMITTED
    with pytest.raises(Exception):
        mod.mutate(first.event_id, event_payload={"x": 1})
    corr = mod.correct(first.event_id, payload={"note": "fix"}, actor="ops", reason="typo")
    assert corr.disposition is IngestDisposition.COMMITTED
    rec = mod.get_journal_entry(corr.event_id)
    assert rec.event.category is JournalCategory.CORRECTION
    assert rec.event.causation_id == first.event_id
    assert str(first.event_id) in rec.event.lineage_refs
    assert mod.get_journal_entry(first.event_id) is not None
    assert len(mod.journal.records()) == 2


def test_pm7_replay_and_integrity_status():
    from tests.unit.pm7_support import make_event, pm7_module

    mod = pm7_module()
    mod.ingest(make_event(idempotency_key="r1"))
    mod.ingest(make_event(idempotency_key="r2", ticket="SIM-2"))
    replay = mod.replay(scope=ReplayScope.SESSION)
    assert replay.event_count == 2
    source_len = len(mod.journal.records())
    mod.replay(scope=ReplayScope.SESSION)
    assert len(mod.journal.records()) == source_len
    report = mod.verify_integrity()
    assert report.chain_valid is True
    assert report.state is IntegrityState.VALID
    assert report.claim == "tamper_detection_only"


def test_pm8_versioned_api():
    api = PersistenceApiV1(SqliteStore(":memory:"))
    assert api.version is PersistenceApiVersion.V1
    assert PersistenceApiV1.__module__.endswith("pm8_persistence.api.v1")


def test_pm8_idempotency_and_dedupe_edges(tmp_path: Path):
    api = PersistenceApiV1(SqliteStore(tmp_path / "edges.sqlite"))
    eid = str(uuid4())
    a = api.ingest_event(
        event_type="signal.recorded",
        producer="recon",
        family=TableFamily.SIGNAL,
        payload={"symbol": "EURUSD"},
        event_id=eid,
        idempotency_key="recon-k1",
    )
    b = api.ingest_event(
        event_type="signal.recorded",
        producer="recon",
        family=TableFamily.SIGNAL,
        payload={"symbol": "EURUSD"},
        event_id=eid,
        idempotency_key="recon-k1",
    )
    assert a.disposition is ApiDisposition.COMMITTED
    assert b.disposition is ApiDisposition.DUPLICATE_IGNORED
    api.persist_order("co-recon", {"state": "accepted"})
    dup_order = api.persist_order("co-recon", {"state": "accepted"})
    assert dup_order.disposition is ApiDisposition.DUPLICATE_IGNORED
    api.persist_execution("co-recon", "mt5_demo_sim", {"fill": 1}, venue_callback_id="cb-recon")
    dup_cb = api.persist_execution("co-recon", "mt5_demo_sim", {"fill": 1}, venue_callback_id="cb-recon")
    assert dup_cb.disposition is ApiDisposition.DUPLICATE_IGNORED
    first = api.apply_projection_event("pos", 1, {"EURUSD": "1"})
    second = api.apply_projection_event("pos", 1, {"EURUSD": "9"})
    assert first.disposition is ApiDisposition.COMMITTED
    assert second.disposition is ApiDisposition.DUPLICATE_IGNORED


def test_pm8_outbox_atomicity(tmp_path: Path):
    api = PersistenceApiV1(SqliteStore(tmp_path / "outbox.sqlite"))
    result = api.ingest_event(
        event_type="order.recorded",
        producer="recon",
        family=TableFamily.ORDER,
        payload={"client_order_id": "c-recon"},
        idempotency_key="order-c-recon",
    )
    assert result.disposition is ApiDisposition.COMMITTED
    pending = api.store.pending()
    assert len(pending) == 1
    assert pending[0]["event_id"] == str(result.record_id)


def test_live_cli_fail_closed():
    assert main(["live", "--config", str(TEST_YAML)]) == 2
    with pytest.raises(LiveTradingDisabledError):
        load_settings(config_path=TEST_YAML, cli_mode="live", environ={})


def test_telegram_transport_refused():
    from botmoduleproject1.adapters.telegram.transport import RealTelegramTransport
    from botmoduleproject1.app.exceptions import FeatureFlagError

    with pytest.raises(FeatureFlagError, match="Telegram"):
        RealTelegramTransport()


def test_operator_cannot_bypass_pm4():
    from botmoduleproject1.contracts.v1.operator import CommandDisposition
    from tests.unit.pm8_support import actor, pm8_module

    mod = pm8_module()
    receipt = mod.handle_text("/buy EURUSD", actor(), idempotency_key="recon-buy")
    assert receipt.disposition is CommandDisposition.REFUSED
    assert receipt.creates_order is False
    doctor = mod.handle_text("/doctor", actor(), idempotency_key="recon-doc")
    assert "execution_permitted=false" in doctor.message


def test_disabled_execution_still_raises():
    with pytest.raises(ExecutionDisabledError):
        DisabledExecution().submit(object())  # type: ignore[arg-type]


def test_recovery_before_trading_still_halts():
    from botmoduleproject1.runtime.orchestrator import UnifiedRuntime

    settings = load_settings(config_path=TEST_YAML, environ={}, cli_mode="test", profile="test")
    container = build_container(settings)
    orch = UnifiedRuntime(container, persistence_api=None)
    orch.state.running = True
    orch.state.recovery_complete = False
    out = orch.tick()
    assert out["ok"] is False
    assert out["reason"] == "recovery_before_trading"


def test_recon_no_silent_pass(tmp_path: Path):
    api = PersistenceApiV1(SqliteStore(tmp_path / "recon.sqlite"))
    rejected = api.persist_reconciliation("local-1", None, "pass", {})
    assert rejected.disposition.value == "rejected"


def test_no_sequence_15_artifacts():
    assert not (ROOT / "docs" / "architecture" / "sequence_15_report.md").exists()
    assert not (ROOT / "docs" / "sequence_15_report.md").exists()
    flags = (PKG / "app" / "feature_flags.py").read_text(encoding="utf-8")
    assert "enable_sequence_15" not in flags
    assert "enable_seq15" not in flags


def test_traceability_and_inventory_exist():
    for rel in (
        "docs/ARCHITECTURE_INVENTORY.md",
        "docs/PM8_PM8A_GAP_MATRIX.md",
        "docs/TRACEABILITY_MATRIX.md",
        "docs/MODULE_NUMBERING_MAP.md",
        "docs/known_limitations.md",
    ):
        assert (ROOT / rel).is_file(), rel
    matrix = (ROOT / "docs" / "TRACEABILITY_MATRIX.md").read_text(encoding="utf-8")
    for row_id in ("R-01", "R-12", "R-17", "R-25"):
        assert f"| {row_id} |" in matrix
    inventory = (ROOT / "docs" / "ARCHITECTURE_INVENTORY.md").read_text(encoding="utf-8")
    assert "PM7 PARTIAL" in inventory or "PARTIAL / evidence-journal" in inventory


def test_ci_hygiene_still_bans_piped_gates():
    workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
    assert "pytest" in workflow
    assert not re.search(r"pytest[^\n]*\|\s*tee", workflow)
    assert not re.search(r"\|\s*grep\b", workflow)

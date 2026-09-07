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
    for n in range(16):
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
    assert CANONICAL_SEQUENCES[15] == "demo_only_trading_readiness_allowlist"

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
        settings, lifecycle=LifecycleState.RUNNING, persistence_ok=True,
        persistence_enabled=True, integrity_ok=True, stale_data=False, operator_bound=True,
    )
    assert health.trading_readiness is False
    assert ready.accept_trade is False
    source = (PKG / "modules" / "observability" / "health_model.py").read_text(encoding="utf-8")
    assert "trading_readiness=True" not in source
    assert "accept_trade=True" not in source

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

def test_no_full_sequence_15_trading_enablement_artifacts():
    """Full Seq15 trading enablement stays blocked; Phase 1 allowlist is separate."""
    assert not (ROOT / "docs" / "architecture" / "sequence_15_report.md").exists()
    assert not (ROOT / "docs" / "sequence_15_report.md").exists()
    flags = (PKG / "app" / "feature_flags.py").read_text(encoding="utf-8")
    assert "enable_sequence_15" not in flags
    assert "enable_seq15" not in flags
    assert "enable_demo_trading_readiness" in flags
    assert (ROOT / "docs" / "architecture" / "sequence_15_demo_readiness_report.md").is_file()

def test_no_sequence_15_artifacts():
    test_no_full_sequence_15_trading_enablement_artifacts()

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

"""PM1 wiring, PM4 handoff, registry, health, no MT5 side effect."""

from __future__ import annotations

from pathlib import Path

from botmoduleproject1.app.container import build_container
from botmoduleproject1.app.health import CheckKind
from botmoduleproject1.app.settings import load_settings
from botmoduleproject1.app.stubs import DisabledExecution
from botmoduleproject1.contracts.v1.execution import ExecutionLifecycleState, ReconciliationOutcome
from botmoduleproject1.contracts.v1.risk import HandoffEligibility, RiskVerdictStatus
from botmoduleproject1.contracts.v1.strategy import Direction
from botmoduleproject1.modules.pm5_execution.module import PM5ExecutionModule
from tests.unit.pm4_support import AS_OF, admitted_bundle
from tests.unit.pm5_support import Clock, ingest_allow, pm5_module

ROOT = Path(__file__).resolve().parents[2]
TEST_YAML = ROOT / "configs" / "test.example.yaml"


def test_metadata_and_manifest() -> None:
    mod = pm5_module()
    meta = mod.metadata()
    assert meta.name == "pm5_execution"
    assert "pm4_risk" in meta.dependencies
    man = mod.manifest()
    assert "orders_to_mt5" in man["does_not"]
    assert man["mt5"] == "placeholder_blocked"
    assert man["durable"] is False


def test_health_startup() -> None:
    mod = pm5_module()
    names = {c.name for c in mod.health_checks(CheckKind.STARTUP)}
    assert "execution.startup" in names
    assert "execution.mt5" in names
    live = {c.name for c in mod.health_checks(CheckKind.LIVENESS)}
    assert "execution.liveness" in live


def test_pm4_allow_does_not_open_broker() -> None:
    _mod, bundle, pub = ingest_allow(key="int-allow")
    assert bundle.handoff_eligibility is HandoffEligibility.ELIGIBLE_PENDING_PM5
    assert bundle.verdict.status is RiskVerdictStatus.ALLOW
    assert bundle.execution_permitted is False
    assert pub.mt5_used is False
    assert pub.broker_side_effect is False
    assert pub.order.broker_ticket.startswith("SIM-")
    assert pub.reconciliation.outcome is ReconciliationOutcome.DEGRADED


def test_pm4_quantity_not_exceeded() -> None:
    from botmoduleproject1.modules.pm5_execution.intake.validators import approved_quantity

    _mod, bundle, pub = ingest_allow(key="int-qty")
    cap = approved_quantity(bundle)
    assert pub.order.original_quantity <= cap
    assert pub.command is not None
    assert pub.command.requested_quantity <= pub.command.approved_quantity


def test_flag_off_keeps_disabled_even_with_pm4() -> None:
    settings = load_settings(
        config_path=TEST_YAML,
        environ={"BOTMODULEPROJECT1_FEATURE__ENABLE_PM4_RISK_GATE": "true"},
        profile="test",
        cli_mode="test",
    )
    container = build_container(settings)
    assert isinstance(container.registry.get("pm4_risk").instance, object)
    assert isinstance(container.registry.get("pm5_execution").instance, DisabledExecution)


def test_both_flags_bind_real_modules() -> None:
    settings = load_settings(
        config_path=TEST_YAML,
        environ={
            "BOTMODULEPROJECT1_FEATURE__ENABLE_PM4_RISK_GATE": "true",
            "BOTMODULEPROJECT1_FEATURE__ENABLE_PM5_SIMULATION": "true",
        },
        profile="test",
        cli_mode="test",
    )
    container = build_container(settings, overrides={"clock": Clock(AS_OF)})
    exe = container.registry.get("pm5_execution").instance
    assert isinstance(exe, PM5ExecutionModule)
    bundle = admitted_bundle(key="wired")
    pub = exe.ingest(bundle, direction=Direction.BUY)
    assert pub.receipt.accepted is True
    assert pub.order.state in {
        ExecutionLifecycleState.FILLED,
        ExecutionLifecycleState.RECONCILIATION_PENDING,
        ExecutionLifecycleState.ACKNOWLEDGED,
    }

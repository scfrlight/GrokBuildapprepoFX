"""Canonical sequence map and freeze gates.

Master Orchestration Prompt is the source of truth for sequence *order*.
The original Drive/GitHub file was not recovered; the architect's 2026-08-30
correction prompt is the authorized mapping. See docs/SEQUENCE_CORRECTION.md.
"""

from __future__ import annotations

# Lifted after Sequences 09–12 build gates in this correction wave.
OPERATOR_PLANE_FROZEN: bool = False

CANONICAL_SEQUENCES: dict[int, str] = {
    0: "repository_reconnaissance",
    1: "pm1_platform_kernel",
    2: "configuration_governance",
    3: "pm2_market_context",
    4: "pm3_strategy_engine",
    5: "pm3_forecasting_qrf",
    6: "pm4_risk_gate",
    7: "pm5_oms_ems_simulation",
    8: "pm6_post_trade_controls",
    9: "pm8_database_consolidation",
    10: "pm8a_migration_backup_recovery",
    11: "pm6_mt5_execution_exit_engine",
    12: "unified_runtime_orchestrator",
    13: "pm9_operator_ux_telegram_control",
}

MISLABELED_OPERATOR_SEQUENCE = 10
CANONICAL_OPERATOR_SEQUENCE = 13

OPERATOR_FREEZE_FIELDS = frozenset({"pm8_operator", "pm8_hitl", "pm8_command_audit"})


def operator_freeze_message(flag_name: str) -> str:
    return (
        f"feature flag {flag_name} is FROZEN. The operator/Telegram plane was an "
        f"early build mislabeled as Sequence {MISLABELED_OPERATOR_SEQUENCE}; "
        f"canonical home is Sequence {CANONICAL_OPERATOR_SEQUENCE}. "
        "No further operator work and no flag bind until Sequences 09–12 complete. "
        "See docs/SEQUENCE_CORRECTION.md."
    )


def assert_operator_not_frozen(field: str, flag_name: str) -> None:
    from botmoduleproject1.app.exceptions import FeatureFlagError

    if OPERATOR_PLANE_FROZEN and field in OPERATOR_FREEZE_FIELDS:
        raise FeatureFlagError(operator_freeze_message(flag_name))

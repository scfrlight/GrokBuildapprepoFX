"""Public PM4 contract tests: enums, RiskVerdict, publication, no-order invariant."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from botmoduleproject1.contracts.v1.risk import (
    ConcentrationState,
    DrawdownStage,
    HandoffEligibility,
    HeatRegime,
    KillSwitchScope,
    KillSwitchStatus,
    RecoveryStage,
    RiskAdmissionCard,
    RiskAdmissionDecision,
    RiskBudgetCard,
    RiskControlState,
    RiskDecisionTier,
    RiskEventType,
    RiskMode,
    RiskPublicationBundle,
    RiskRejectionReason,
    RiskSeverity,
    RiskVerdict,
    RiskVerdictStatus,
)
from botmoduleproject1.contracts.v1.time import utc_now
from tests.unit.pm4_support import admitted_bundle


def test_required_enums_exist() -> None:
    assert RiskDecisionTier.HARD_VETO
    assert RiskAdmissionDecision.APPROVE
    assert RiskControlState.ACTIVE
    assert DrawdownStage.MILD_THROTTLE
    assert HeatRegime.HOT
    assert ConcentrationState.CROWDED
    assert KillSwitchScope.ACCOUNT
    assert KillSwitchStatus.LATCHED
    assert RecoveryStage.MANUAL_REVIEW
    assert RiskMode.KILL_PROTECTED
    assert RiskSeverity.CRITICAL
    assert HandoffEligibility.ELIGIBLE_PENDING_PM5
    assert RiskEventType.KILL_SWITCH
    assert RiskRejectionReason.MISSING_FORECAST


def test_risk_verdict_allow_is_explicit() -> None:
    denied = RiskVerdict(
        intent_id=uuid4(),
        occurred_at=utc_now(),
        status=RiskVerdictStatus.DENY,
        reasons=(RiskRejectionReason.POLICY,),
    )
    assert denied.allows_execution is False
    allowed = denied.model_copy(update={"status": RiskVerdictStatus.ALLOW, "reasons": ()})
    assert allowed.allows_execution is True


def test_bundle_cards_are_typed() -> None:
    bundle = admitted_bundle(key="cards")
    assert isinstance(bundle, RiskPublicationBundle)
    assert isinstance(bundle.admission, RiskAdmissionCard)
    assert isinstance(bundle.budget, RiskBudgetCard)
    assert bundle.sizing.recommended_size >= 0
    assert bundle.execution_permitted is False


def test_bundle_forbids_execution_permitted() -> None:
    bundle = admitted_bundle(key="forbid-exec")
    with pytest.raises(ValidationError, match="execution_permitted"):
        RiskPublicationBundle(
            **{**bundle.model_dump(), "execution_permitted": True}
        )


def test_budget_card_hierarchy_fields() -> None:
    card = RiskBudgetCard(
        account_budget=Decimal("2000"),
        sleeve_budget=Decimal("1000"),
        regime_budget=Decimal("800"),
        cluster_budget=Decimal("1000"),
        symbol_budget=Decimal("500"),
        candidate_budget=Decimal("500"),
        residual_headroom=Decimal("400"),
        consumed_headroom=Decimal("100"),
    )
    assert card.account_budget > card.symbol_budget

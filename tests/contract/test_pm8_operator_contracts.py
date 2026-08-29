from datetime import datetime, timezone

import pytest

from botmoduleproject1.contracts.v1.operator import (
    CommandDisposition,
    CommandReceipt,
    OperatorCommand,
    OperatorIdentity,
    OperatorVerb,
    REFUSED_VERBS,
    TransportMode,
)
from botmoduleproject1.contracts.v1.roles import OperatorRole
from botmoduleproject1.contracts.v1.tuning import TuningChangeRequest, ParameterSchema, TuningChangeStatus
from botmoduleproject1.modules.pm8_operator.authz.rbac import allowed_verbs, has_permission


def _now():
    return datetime(2026, 8, 29, 6, 0, tzinfo=timezone.utc)


def test_command_requires_idempotency_and_utc():
    actor = OperatorIdentity(actor_id="a", display_name="a", role=OperatorRole.ADMIN)
    with pytest.raises(Exception):
        OperatorCommand(
            occurred_at=_now(),
            idempotency_key="  ",
            verb=OperatorVerb.STATUS,
            actor=actor,
        )
    cmd = OperatorCommand(
        occurred_at=_now(),
        idempotency_key="k1",
        verb=OperatorVerb.STATUS,
        actor=actor,
    )
    assert cmd.channel == "simulated"


def test_receipt_cannot_claim_order():
    actor = OperatorIdentity(actor_id="a", display_name="a", role=OperatorRole.ADMIN)
    receipt = CommandReceipt(
        correlation_id=actor.event_id if hasattr(actor, "event_id") else __import__("uuid").uuid4(),
        idempotency_key="k",
        occurred_at=_now(),
        verb=OperatorVerb.HALT,
        disposition=CommandDisposition.ACCEPTED,
        actor_id="a",
        role=OperatorRole.ADMIN,
        message="halted",
        reason_code="halted",
    )
    assert receipt.creates_order is False
    assert receipt.skips_pm4 is False
    assert receipt.broker_side_effect is False
    assert receipt.mt5_used is False


def test_refused_verbs_are_never_allowed():
    for role in OperatorRole:
        for verb in REFUSED_VERBS:
            assert has_permission(role, verb) is False
            assert verb not in allowed_verbs(role)


def test_tuning_cannot_auto_promote():
    req = TuningChangeRequest(
        occurred_at=_now(),
        idempotency_key="t1",
        parameter=ParameterSchema(name="x", display_name="x", group="g", type="float"),
        new_value=1,
        requested_by="op",
    )
    assert req.auto_promote_to_live is False
    assert req.status is TuningChangeStatus.DRAFT


def test_secret_payload_rejected():
    actor = OperatorIdentity(actor_id="a", display_name="a", role=OperatorRole.ADMIN)
    with pytest.raises(Exception):
        OperatorCommand(
            occurred_at=_now(),
            idempotency_key="k",
            verb=OperatorVerb.STATUS,
            actor=actor,
            payload={"token": "secret"},
        )

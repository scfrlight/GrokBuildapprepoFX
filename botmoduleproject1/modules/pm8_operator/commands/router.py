"""Dispatch allowed verbs. Refused verbs never become side effects."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from botmoduleproject1.contracts.v1.alerts import ApprovalStatus
from botmoduleproject1.contracts.v1.operator import (
    REFUSED_VERBS,
    CommandDisposition,
    CommandReceipt,
    HaltState,
    OperatorCommand,
    OperatorVerb,
)
from botmoduleproject1.modules.pm8_operator.authz.rbac import has_permission, scopes_for
from botmoduleproject1.modules.pm8_operator.intake.parser import parse_text

if TYPE_CHECKING:
    from botmoduleproject1.modules.pm8_operator.module import PM8OperatorModule


def _receipt(
    command: OperatorCommand,
    *,
    disposition: CommandDisposition,
    message: str,
    reason_code: str,
    now,
    details: dict[str, Any] | None = None,
) -> CommandReceipt:
    return CommandReceipt(
        correlation_id=command.correlation_id,
        causation_id=command.event_id,
        idempotency_key=command.idempotency_key,
        occurred_at=now,
        verb=command.verb,
        disposition=disposition,
        actor_id=command.actor.actor_id,
        role=command.actor.role,
        message=message,
        reason_code=reason_code,
        details=details or {},
    )


def dispatch(module: "PM8OperatorModule", command: OperatorCommand) -> CommandReceipt:
    now = module.clock.now()
    module.hitl.expire_due(now)

    if command.verb in REFUSED_VERBS:
        return _receipt(
            command,
            disposition=CommandDisposition.REFUSED,
            message="Command is forbidden on the operator plane. It is not an order path.",
            reason_code="verb_refused",
            now=now,
            details={"execution_permitted": False},
        )

    if not has_permission(command.actor.role, command.verb):
        return _receipt(
            command,
            disposition=CommandDisposition.UNAUTHORIZED,
            message=f"role {command.actor.role.value} cannot {command.verb.value}",
            reason_code="rbac_denied",
            now=now,
            details={"scopes": [s.value for s in scopes_for(command.actor.role)]},
        )

    if command.verb is OperatorVerb.HELP:
        return _receipt(
            command,
            disposition=CommandDisposition.ACCEPTED,
            message="Allowed: /status /health /doctor /pending /alerts /journal /ack /halt /approve /reject /propose. Refused: /buy /sell /order /resume /rearm /live /mt5.",
            reason_code="help",
            now=now,
        )

    if command.verb is OperatorVerb.STATUS:
        bundle = module.publish()
        return _receipt(
            command,
            disposition=CommandDisposition.ACCEPTED,
            message=f"halt={bundle.halt_state.value} transport={bundle.transport_mode.value} hitl={bundle.hitl_pending} live=false",
            reason_code="status",
            now=now,
            details=bundle.model_dump(mode="json"),
        )

    if command.verb is OperatorVerb.HEALTH:
        checks = module.health_checks(module._health_kind())
        failed = [c.name for c in checks if not c.passed]
        return _receipt(
            command,
            disposition=CommandDisposition.ACCEPTED,
            message="health ok" if not failed else f"failed:{','.join(failed)}",
            reason_code="health",
            now=now,
            details={"failed": failed, "count": len(checks)},
        )

    if command.verb is OperatorVerb.DOCTOR:
        return _receipt(
            command,
            disposition=CommandDisposition.ACCEPTED,
            message="doctor: live disabled, mt5 unbound, telegram api unbound, pm4 exclusive, execution_permitted=false",
            reason_code="doctor",
            now=now,
        )

    if command.verb is OperatorVerb.PENDING:
        pending = module.hitl.pending()
        return _receipt(
            command,
            disposition=CommandDisposition.ACCEPTED,
            message=f"{len(pending)} pending HITL requests",
            reason_code="pending",
            now=now,
            details={"ids": [str(i.request_id) for i in pending]},
        )

    if command.verb is OperatorVerb.LIST_ALERTS:
        open_alerts = [a for a in module.alerts if not a.acked]
        return _receipt(
            command,
            disposition=CommandDisposition.ACCEPTED,
            message=f"{len(open_alerts)} unacked alerts",
            reason_code="alerts",
            now=now,
            details={"ids": [str(a.alert_id) for a in open_alerts]},
        )

    if command.verb is OperatorVerb.QUERY_JOURNAL:
        if module.ledger is None:
            return _receipt(
                command,
                disposition=CommandDisposition.ACCEPTED,
                message="ledger_unavailable",
                reason_code="ledger_unavailable",
                now=now,
            )
        return _receipt(
            command,
            disposition=CommandDisposition.ACCEPTED,
            message="journal query accepted (headless)",
            reason_code="journal_query",
            now=now,
        )

    if command.verb is OperatorVerb.ACK:
        target = command.target_id or command.payload.get("target_id")
        if not target:
            return _receipt(
                command,
                disposition=CommandDisposition.REJECTED,
                message="ack requires a target id",
                reason_code="missing_target",
                now=now,
            )
        found = False
        for alert in module.alerts:
            if str(alert.alert_id) == str(target):
                alert.acked = True
                alert.acked_by = command.actor.actor_id
                found = True
                break
        if not found:
            return _receipt(
                command,
                disposition=CommandDisposition.REJECTED,
                message="alert not found",
                reason_code="not_found",
                now=now,
            )
        return _receipt(
            command,
            disposition=CommandDisposition.ACCEPTED,
            message=f"acked {target}",
            reason_code="acked",
            now=now,
        )

    if command.verb is OperatorVerb.HALT:
        if module.config.halt_requires_dual_control and module.halt_state is HaltState.RUNNING:
            first = module.dual_halt_actor
            if first is None:
                module.dual_halt_actor = command.actor.actor_id
                return _receipt(
                    command,
                    disposition=CommandDisposition.PENDING_DUAL_CONTROL,
                    message="halt waiting for a second distinct actor",
                    reason_code="dual_control",
                    now=now,
                )
            if first == command.actor.actor_id:
                return _receipt(
                    command,
                    disposition=CommandDisposition.PENDING_DUAL_CONTROL,
                    message="same actor cannot complete dual control",
                    reason_code="dual_control_same_actor",
                    now=now,
                )
        module.halt_state = HaltState.HALTED
        module.dual_halt_actor = None
        return _receipt(
            command,
            disposition=CommandDisposition.ACCEPTED,
            message="halt requested and recorded. auto-rearm is forbidden. this is not a broker flatten.",
            reason_code="halted",
            now=now,
            details={"halt_state": module.halt_state.value, "broker_flatten": False},
        )

    if command.verb in {OperatorVerb.APPROVE, OperatorVerb.REJECT}:
        if not module.config.hitl_enabled:
            return _receipt(
                command,
                disposition=CommandDisposition.REFUSED,
                message="HITL flag is off",
                reason_code="hitl_disabled",
                now=now,
            )
        target = command.target_id or command.payload.get("target_id")
        if not target:
            req = module.hitl.open_intent_request(actor=command.actor.actor_id, now=now)
            return _receipt(
                command,
                disposition=CommandDisposition.PENDING_HITL,
                message=f"opened HITL request {req.request_id}",
                reason_code="hitl_opened",
                now=now,
                details={"request_id": str(req.request_id), "skips_pm4": False},
            )
        decided = module.hitl.decide(
            str(target),
            approved=command.verb is OperatorVerb.APPROVE,
            actor=command.actor.actor_id,
            now=now,
        )
        if decided is None:
            return _receipt(
                command,
                disposition=CommandDisposition.REJECTED,
                message="HITL request not found",
                reason_code="not_found",
                now=now,
            )
        if decided.status is ApprovalStatus.EXPIRED:
            return _receipt(
                command,
                disposition=CommandDisposition.EXPIRED,
                message="HITL request expired",
                reason_code="expired",
                now=now,
            )
        if decided.status is ApprovalStatus.APPROVED:
            return _receipt(
                command,
                disposition=CommandDisposition.ACCEPTED,
                message="HITL approved. Consent recorded. PM4 is still the only gate. No OrderRequest emitted.",
                reason_code="hitl_approved_not_an_order",
                now=now,
                details={"request_id": str(decided.request_id), "order_emitted": False},
            )
        return _receipt(
            command,
            disposition=CommandDisposition.ACCEPTED,
            message="HITL rejected",
            reason_code="hitl_rejected",
            now=now,
            details={"request_id": str(decided.request_id)},
        )

    if command.verb is OperatorVerb.PROPOSE_TUNING:
        if not module.config.studio_enabled:
            return _receipt(
                command,
                disposition=CommandDisposition.REFUSED,
                message="studio flag is off",
                reason_code="studio_disabled",
                now=now,
            )
        name = command.payload.get("parameter") or command.target_id or "unnamed"
        value = command.payload.get("new_value", "")
        proposal = module.studio.propose(
            actor=command.actor.actor_id,
            now=now,
            name=str(name),
            new_value=value,
            key=command.idempotency_key,
        )
        return _receipt(
            command,
            disposition=CommandDisposition.ACCEPTED,
            message=f"research proposal {proposal.request_id} recorded; auto_promote_to_live=false",
            reason_code="studio_proposed",
            now=now,
            details={
                "request_id": str(proposal.request_id),
                "auto_promote_to_live": False,
                "status": proposal.status.value,
            },
        )

    return _receipt(
        command,
        disposition=CommandDisposition.REJECTED,
        message="unhandled verb",
        reason_code="unhandled",
        now=now,
    )


def command_from_text(module: "PM8OperatorModule", command: OperatorCommand) -> OperatorCommand:
    """If verb is HELP but text parses to another verb, keep structured verb as source of truth."""
    if command.text and command.verb is OperatorVerb.HELP:
        verb, target, payload = parse_text(command.text)
        return command.model_copy(update={"verb": verb, "target_id": target or command.target_id, "payload": {**command.payload, **payload}})
    return command

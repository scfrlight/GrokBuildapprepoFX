"""PM8 operator orchestrator. Commands are not orders. No MT5. No Telegram API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from botmoduleproject1.app.capabilities import ModuleMetadata
from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.contracts.v1.operator import (
    CommandDisposition,
    CommandReceipt,
    HaltState,
    OperatorAlert,
    OperatorCommand,
    OperatorIdentity,
    OperatorPublicationBundle,
    OperatorVerb,
    TransportMode,
)
from botmoduleproject1.contracts.v1.roles import OperatorRole
from botmoduleproject1.modules.pm8_operator.audit.emitter import CommandAudit
from botmoduleproject1.modules.pm8_operator.capabilities import PM8_OPERATOR_METADATA
from botmoduleproject1.modules.pm8_operator.commands.router import command_from_text, dispatch
from botmoduleproject1.modules.pm8_operator.config.schema import Pm8OperatorConfig, config_from_settings
from botmoduleproject1.modules.pm8_operator.health import health_checks as pm8_health
from botmoduleproject1.modules.pm8_operator.hitl.queue import HitlQueue
from botmoduleproject1.modules.pm8_operator.intake.parser import parse_text
from botmoduleproject1.modules.pm8_operator.manifest import module_manifest
from botmoduleproject1.modules.pm8_operator.publication.publisher import PublicationService
from botmoduleproject1.modules.pm8_operator.studio.proposals import Studio
from botmoduleproject1.modules.pm8_operator.transport.simulated import SimulatedTransport


@dataclass
class RuntimeAlert:
    alert_id: UUID
    occurred_at: Any
    code: str
    message: str
    severity: str = "info"
    acked: bool = False
    acked_by: str | None = None


class PM8OperatorModule:
    """Registered as pm8_operator when enable_pm8_operator is on."""

    def __init__(
        self,
        config: Pm8OperatorConfig,
        clock: Any,
        *,
        feature_enabled: bool = True,
        ledger: Any = None,
        persistence_api: Any = None,
    ) -> None:
        self.config = config
        self.clock = clock
        self.feature_enabled = feature_enabled
        self.ledger = ledger
        self.persistence_api = persistence_api
        self.transport_mode = (
            TransportMode.SIMULATED if feature_enabled and config.operating_mode == "simulated" else TransportMode.DISABLED
        )
        self.halt_state = HaltState.RUNNING
        self.dual_halt_actor: str | None = None
        self.hitl = HitlQueue(ttl_seconds=config.approval_ttl_seconds)
        self.studio = Studio()
        self.audit = CommandAudit()
        self.transport = SimulatedTransport()
        self.publisher = PublicationService()
        self.alerts: list[RuntimeAlert] = []
        self._idempotency: dict[str, CommandReceipt] = {}
        self._last_bundle: OperatorPublicationBundle | None = None
        self._last_disposition: CommandDisposition | None = None

    def bind_persistence(self, storage: Any) -> None:
        api = getattr(storage, "api", storage)
        self.persistence_api = api
        self.ledger = storage

    @classmethod
    def from_settings(cls, settings: object, clock: Any, ledger: Any = None) -> "PM8OperatorModule":
        flags = getattr(settings, "feature_flags")
        cfg = config_from_settings(settings)
        return cls(
            cfg,
            clock,
            feature_enabled=bool(getattr(flags, "pm8_operator", False)),
            ledger=ledger,
        )

    def metadata(self) -> ModuleMetadata:
        return PM8_OPERATOR_METADATA

    def manifest(self) -> dict:
        return module_manifest()

    def is_ready(self) -> bool:
        return self.feature_enabled and self.transport_mode is TransportMode.SIMULATED

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        return pm8_health(
            kind=kind,
            enabled=self.feature_enabled,
            transport=self.transport_mode,
            halt_state=self.halt_state,
            telegram_api_bound=False,
            mt5=False,
        )

    def _health_kind(self) -> CheckKind:
        return CheckKind.LIVENESS

    def raise_alert(self, *, code: str, message: str, severity: str = "warning") -> RuntimeAlert:
        alert = RuntimeAlert(
            alert_id=uuid4(),
            occurred_at=self.clock.now(),
            code=code,
            message=message,
            severity=severity,
        )
        self.alerts.append(alert)
        return alert

    def handle_text(
        self,
        text: str,
        actor: OperatorIdentity,
        *,
        idempotency_key: str | None = None,
    ) -> CommandReceipt:
        verb, target, payload = parse_text(text)
        command = OperatorCommand(
            occurred_at=self.clock.now(),
            idempotency_key=idempotency_key or f"{actor.actor_id}:{text}",
            verb=verb,
            actor=actor,
            text=text,
            target_id=target,
            payload=payload,
            channel="simulated",
        )
        return self.handle(command)

    def handle(self, command: OperatorCommand) -> CommandReceipt:
        command = command_from_text(self, command)
        existing = self._idempotency.get(command.idempotency_key)
        if existing is not None:
            return existing.model_copy(update={"disposition": CommandDisposition.DUPLICATE, "reason_code": "duplicate"})
        receipt = dispatch(self, command)
        self._idempotency[command.idempotency_key] = receipt
        self._last_disposition = receipt.disposition
        if self.config.audit_enabled:
            self.audit.record(command, receipt)
        self.transport.deliver_in(command)
        self.transport.deliver_out(receipt, chat_id=command.actor.telegram_user_id or "console")
        return receipt

    def publish(self) -> OperatorPublicationBundle:
        bundle = self.publisher.publish(
            as_of=self.clock.now(),
            halt_state=self.halt_state,
            hitl_pending=len(self.hitl.pending()),
            studio_open=len(self.studio.open()),
            last_disposition=self._last_disposition,
            diagnostics={
                "enabled": self.feature_enabled,
                "transport": self.transport_mode.value,
                "telegram_api_bound": False,
                "mt5_used": False,
                "execution_permitted": False,
                "live_trading": False,
                "auto_rearm": False,
                "audit_records": len(self.audit.records),
            },
        )
        self._last_bundle = bundle
        return bundle


def demo_actor(role: OperatorRole = OperatorRole.ADMIN, actor_id: str = "op-admin") -> OperatorIdentity:
    return OperatorIdentity(
        actor_id=actor_id,
        display_name=actor_id,
        role=role,
        transport=TransportMode.SIMULATED,
    )

from __future__ import annotations

from pydantic import ValidationError

from botmoduleproject1.contracts.v1.execution import ExecutionPublicationBundle
from botmoduleproject1.contracts.v1.persistence import IngestDisposition, IngestResult, LedgerEvent
from botmoduleproject1.contracts.v1.post_trade import OperationalTruthBundle
from botmoduleproject1.contracts.v1.risk import RiskPublicationBundle
from botmoduleproject1.modules.pm7_persistence.intake.normalizer import classify_truth, from_mapping
from botmoduleproject1.modules.pm7_persistence.intake.pm4_adapter import from_risk
from botmoduleproject1.modules.pm7_persistence.intake.pm5_adapter import from_execution
from botmoduleproject1.modules.pm7_persistence.intake.pm6_adapter import from_monitoring
from botmoduleproject1.modules.pm7_persistence.intake.validators import validate_event


class IntakeError(ValueError):
    def __init__(self, reasons: tuple[str, ...]) -> None:
        super().__init__(",".join(reasons))
        self.reasons = reasons


class IntakeGateway:
    def normalize(self, source, *, now) -> LedgerEvent:
        try:
            if isinstance(source, LedgerEvent):
                event = source
            elif isinstance(source, RiskPublicationBundle):
                event = from_risk(source, now=now)
            elif isinstance(source, ExecutionPublicationBundle):
                event = from_execution(source, now=now)
            elif isinstance(source, OperationalTruthBundle):
                event = from_monitoring(source, now=now)
            elif isinstance(source, dict):
                event = from_mapping(source, now=now)
            else:
                raise TypeError(f"unsupported ingest source {type(source)!r}")
            return classify_truth(event)
        except ValidationError as exc:
            raise IntakeError(("schema_invalid",) + tuple(str(e["msg"]) for e in exc.errors()[:3])) from exc

    def validate(self, event: LedgerEvent, *, now, feature_enabled: bool):
        return validate_event(event, now=now, feature_enabled=feature_enabled)

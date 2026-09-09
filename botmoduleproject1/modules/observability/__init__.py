"""Sequence 14 observability + Sequence 15 demo readiness allowlist.

Observability remains observe-only by default. Sequence 15 Phase 1 may open
trading_readiness only via the explicit DEMO allowlist (env opt-in).
"""

from botmoduleproject1.modules.observability.demo_readiness import (
    DemoReadinessDecision,
    evaluate_demo_readiness_allowlist,
)
from botmoduleproject1.modules.observability.errors import ERROR_CATALOG, public_message
from botmoduleproject1.modules.observability.health_model import TRANSITION_TABLE, evaluate
from botmoduleproject1.modules.observability.logging_events import emit_event
from botmoduleproject1.modules.observability.metrics import METRIC_CATALOG, MetricRegistry
from botmoduleproject1.modules.observability.module import ObservabilityModule
from botmoduleproject1.modules.observability.redaction import redact_mapping
from botmoduleproject1.modules.observability.runbooks import RUNBOOKS

__all__ = [
    "DemoReadinessDecision",
    "ERROR_CATALOG",
    "METRIC_CATALOG",
    "MetricRegistry",
    "ObservabilityModule",
    "RUNBOOKS",
    "TRANSITION_TABLE",
    "emit_event",
    "evaluate",
    "evaluate_demo_readiness_allowlist",
    "public_message",
    "redact_mapping",
]

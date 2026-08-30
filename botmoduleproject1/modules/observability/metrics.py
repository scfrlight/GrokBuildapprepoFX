"""Typed metric catalog. Bounded labels. Safe defaults."""

from __future__ import annotations

from typing import Any

from botmoduleproject1.contracts.v1.observability import (
    ALLOWED_METRIC_LABELS,
    FORBIDDEN_LABEL_FRAGMENTS,
    MetricSample,
    MetricSpec,
    MetricType,
    MetricUnit,
)
from botmoduleproject1.contracts.v1.time import utc_now


def _spec(
    name: str,
    metric_type: MetricType,
    unit: MetricUnit,
    *,
    labels: tuple[str, ...] = ("module",),
    source: str,
    update_point: str,
    default: float = 0.0,
    description: str,
) -> MetricSpec:
    return MetricSpec(
        name=name,
        metric_type=metric_type,
        unit=unit,
        labels=labels,
        cardinality="bounded: allowlisted label keys only; no IDs, payloads, or secrets",
        source_module=source,
        update_point=update_point,
        safe_default=default,
        description=description,
    )


METRIC_CATALOG: tuple[MetricSpec, ...] = (
    _spec("botmodule.persistence.latency_ms", MetricType.HISTOGRAM, MetricUnit.MILLISECONDS, source="pm8_persistence", update_point="PersistenceApiV1.ingest_event", description="Persistence write latency"),
    _spec("botmodule.persistence.errors", MetricType.COUNTER, MetricUnit.COUNT, labels=("module", "error_code"), source="pm8_persistence", update_point="PersistenceApiV1 error path", description="Persistence errors"),
    _spec("botmodule.outbox.backlog", MetricType.GAUGE, MetricUnit.COUNT, source="pm8_persistence", update_point="outbox poll", description="Outbox backlog size"),
    _spec("botmodule.outbox.relay_lag_ms", MetricType.GAUGE, MetricUnit.MILLISECONDS, source="pm8_persistence", update_point="outbox dispatch", description="Outbox relay lag"),
    _spec("botmodule.inbox.dedupe_hits", MetricType.COUNTER, MetricUnit.COUNT, source="pm8_persistence", update_point="inbox consume", description="Inbox dedupe hits"),
    _spec("botmodule.dead_letter.count", MetricType.GAUGE, MetricUnit.COUNT, source="pm8_persistence", update_point="outbox dead-letter", description="Dead-letter count"),
    _spec("botmodule.projection.lag", MetricType.GAUGE, MetricUnit.COUNT, source="pm8_persistence", update_point="projection cursor", description="Projection lag in events"),
    _spec("botmodule.projection.rebuild_duration_ms", MetricType.HISTOGRAM, MetricUnit.MILLISECONDS, source="pm8_persistence", update_point="projection rebuild", description="Projection rebuild duration"),
    _spec("botmodule.replay.duration_ms", MetricType.HISTOGRAM, MetricUnit.MILLISECONDS, source="pm7_persistence", update_point="journal replay", description="Replay duration"),
    _spec("botmodule.snapshot.age_seconds", MetricType.GAUGE, MetricUnit.SECONDS, source="pm8_persistence", update_point="snapshot capture", description="Snapshot age"),
    _spec("botmodule.checkpoint.age_seconds", MetricType.GAUGE, MetricUnit.SECONDS, source="pm8_persistence", update_point="checkpoint", description="Checkpoint age"),
    _spec("botmodule.reconciliation.mismatch_count", MetricType.GAUGE, MetricUnit.COUNT, source="pm6_post_trade", update_point="reconciliation", description="Reconciliation mismatches"),
    _spec("botmodule.reconciliation.degraded_count", MetricType.COUNTER, MetricUnit.COUNT, source="pm6_post_trade", update_point="reconciliation degraded", description="Reconciliation degraded transitions"),
    _spec("botmodule.risk.denials", MetricType.COUNTER, MetricUnit.COUNT, labels=("module", "outcome"), source="pm4_risk_gate", update_point="risk verdict", description="Risk denials"),
    _spec("botmodule.execution.simulation_attempts", MetricType.COUNTER, MetricUnit.COUNT, labels=("module", "outcome"), source="pm5_execution", update_point="SIM ticket", description="Execution simulation attempts"),
    _spec("botmodule.execution.duplicate_attempts", MetricType.COUNTER, MetricUnit.COUNT, source="pm5_execution", update_point="idempotent submit", description="Duplicate execution attempts"),
    _spec("botmodule.retry.count", MetricType.COUNTER, MetricUnit.COUNT, labels=("module", "family"), source="pm8_persistence", update_point="outbox retry", description="Retry count"),
    _spec("botmodule.market.stale_events", MetricType.COUNTER, MetricUnit.COUNT, source="pm2_market_context", update_point="stale detector", description="Stale market-data events"),
    _spec("botmodule.incidents.active", MetricType.GAUGE, MetricUnit.COUNT, source="pm6_post_trade", update_point="incident registry", description="Active incidents"),
    _spec("botmodule.incidents.unresolved", MetricType.GAUGE, MetricUnit.COUNT, source="pm6_post_trade", update_point="incident registry", description="Unresolved incidents"),
    _spec("botmodule.operator.actions", MetricType.COUNTER, MetricUnit.COUNT, labels=("module", "outcome"), source="pm8_operator", update_point="command dispatch", description="Operator actions"),
    _spec("botmodule.operator.denied_actions", MetricType.COUNTER, MetricUnit.COUNT, labels=("module", "outcome"), source="pm8_operator", update_point="permission check", description="Denied operator actions"),
    _spec("botmodule.health.transitions", MetricType.COUNTER, MetricUnit.COUNT, labels=("module", "dimension", "outcome"), source="observability", update_point="health evaluate", description="Health transitions"),
    _spec("botmodule.shutdown.duration_ms", MetricType.HISTOGRAM, MetricUnit.MILLISECONDS, source="pm1_platform", update_point="runtime.stop", description="Shutdown duration"),
    _spec("botmodule.recovery.duration_ms", MetricType.HISTOGRAM, MetricUnit.MILLISECONDS, source="runtime", update_point="orchestrator recovery", description="Recovery duration"),
)

CATALOG_BY_NAME: dict[str, MetricSpec] = {spec.name: spec for spec in METRIC_CATALOG}


class CardinalityError(ValueError):
    pass


class UnknownMetricError(ValueError):
    pass


class MetricRegistry:
    """In-process samples. High-cardinality labels are refused."""

    def __init__(self) -> None:
        self._values: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}

    def _check_labels(self, name: str, labels: dict[str, str]) -> dict[str, str]:
        spec = CATALOG_BY_NAME.get(name)
        if spec is None:
            raise UnknownMetricError(name)
        allowed = set(spec.labels)
        for key, value in labels.items():
            lowered = key.lower()
            if key not in ALLOWED_METRIC_LABELS or key not in allowed:
                raise CardinalityError(f"label {key!r} not allowed on {name}")
            if any(frag in lowered for frag in FORBIDDEN_LABEL_FRAGMENTS):
                raise CardinalityError(f"forbidden label key {key!r}")
            if any(frag in value.lower() for frag in FORBIDDEN_LABEL_FRAGMENTS):
                raise CardinalityError(f"forbidden label value on {key}")
            if len(value) > 32:
                raise CardinalityError(f"label value too long on {key}")
        return {k: labels[k] for k in spec.labels if k in labels}

    def set(self, name: str, value: float, **labels: str) -> MetricSample:
        checked = self._check_labels(name, labels)
        key = (name, tuple(sorted(checked.items())))
        self._values[key] = float(value)
        return MetricSample(name=name, value=float(value), labels=checked, captured_at=utc_now())

    def inc(self, name: str, amount: float = 1.0, **labels: str) -> MetricSample:
        checked = self._check_labels(name, labels)
        key = (name, tuple(sorted(checked.items())))
        current = self._values.get(key, CATALOG_BY_NAME[name].safe_default)
        return self.set(name, current + amount, **checked)

    def snapshot(self) -> tuple[MetricSample, ...]:
        now = utc_now()
        samples: list[MetricSample] = []
        seen = {name for name, _ in self._values}
        for (name, pairs), value in sorted(self._values.items()):
            samples.append(
                MetricSample(name=name, value=value, labels=dict(pairs), captured_at=now)
            )
        for spec in METRIC_CATALOG:
            if spec.name not in seen:
                samples.append(
                    MetricSample(name=spec.name, value=spec.safe_default, labels={}, captured_at=now)
                )
        return tuple(samples)

    def as_dict(self) -> list[dict[str, Any]]:
        return [s.model_dump(mode="json") for s in self.snapshot()]

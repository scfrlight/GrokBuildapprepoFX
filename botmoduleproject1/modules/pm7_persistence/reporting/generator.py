from botmoduleproject1.contracts.v1.persistence import AuditReport, DataQualityStatus, ReportKind
from botmoduleproject1.modules.pm7_persistence.reporting.templates import TITLES
from botmoduleproject1.modules.pm7_persistence.warehouse.datasets import build_dataset


class ReportingService:
    def generate(self, *, now, kind: ReportKind, records, recon=None, enabled: bool = True) -> AuditReport:
        dataset = build_dataset(now=now, records=records, scope=kind.value)
        extra = ""
        if kind is ReportKind.RECONCILIATION_HEALTH:
            states = [r.state.value for r in (recon or [])]
            degraded = states.count("degraded") + states.count("unavailable")
            extra = f" recon_degraded_or_unavailable={degraded}"
            if not states:
                dataset = dataset.model_copy(update={"quality": DataQualityStatus.INSUFFICIENT_DATA})
        summary = f"{TITLES.get(kind.value, kind.value)}. events={len(records)}.{extra}"
        if dataset.quality is DataQualityStatus.INSUFFICIENT_DATA:
            summary = "insufficient_data"
        if not enabled:
            summary = "reporting_disabled"
            dataset = dataset.model_copy(update={"quality": DataQualityStatus.NOT_AVAILABLE})
        return AuditReport(
            occurred_at=now,
            kind=kind,
            summary=summary,
            dataset=dataset,
            lineage_refs=dataset.source_event_ids,
            quality=dataset.quality,
        )

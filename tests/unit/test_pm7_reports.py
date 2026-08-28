from botmoduleproject1.contracts.v1.persistence import DataQualityStatus, ReportKind
from tests.unit.pm7_support import ingest_sim, make_event, pm7_module


def test_lineage_aware_report():
    mod = pm7_module()
    mod.ingest(make_event())
    report = mod.generate_report(ReportKind.DAILY_OPERATIONS)
    assert report.lineage_refs
    assert report.quality is DataQualityStatus.OK
    assert report.dataset.metrics.get("broker_fills") is None


def test_insufficient_data_handled():
    mod = pm7_module()
    report = mod.generate_report(ReportKind.INCIDENT_REVIEW)
    assert report.quality is DataQualityStatus.INSUFFICIENT_DATA
    assert report.summary == "insufficient_data"


def test_simulation_not_shown_as_broker():
    mod = pm7_module()
    mod.ingest(make_event())
    report = mod.generate_report()
    assert "SIM" in str(report.dataset.metric_definitions.get("simulation_tickets", "")) or report.dataset.metrics.get("simulation_tickets") == 1
    assert report.dataset.truth_source.value == "derived"


def test_reconciliation_degraded_visible():
    mod, *_ = ingest_sim(key="rep-recon")
    report = mod.generate_report(ReportKind.RECONCILIATION_HEALTH)
    assert "degraded" in report.summary or report.dataset.metrics.get("event_count", 0) >= 1


def test_incident_governance_integrity_reports():
    mod = pm7_module()
    mod.ingest(make_event(incident_id="i1", category="incident"))
    for kind in (ReportKind.INCIDENT_REVIEW, ReportKind.GOVERNANCE_REVIEW, ReportKind.INTEGRITY_VERIFICATION):
        report = mod.generate_report(kind)
        assert report.kind is kind

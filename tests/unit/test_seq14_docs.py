"""Sequence 14 documentation and numbering consistency."""

from __future__ import annotations

from pathlib import Path

from botmoduleproject1.app.sequence_gate import CANONICAL_SEQUENCES
from botmoduleproject1.modules.observability.runbooks import RUNBOOKS, write_markdown

ROOT = Path(__file__).resolve().parents[2]
MAP = (ROOT / "docs" / "MODULE_NUMBERING_MAP.md").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


REQUIRED_DOCS = (
    "docs/MODULE_NUMBERING_MAP.md",
    "docs/TRACEABILITY_MATRIX.md",
    "docs/observability/guide.md",
    "docs/observability/health_readiness.md",
    "docs/observability/metrics.md",
    "docs/observability/error_taxonomy.md",
    "docs/architecture/sequence_14_report.md",
    "docs/guides/configuration.md",
    "docs/guides/environment.md",
    "docs/guides/local_test.md",
    "docs/guides/ci.md",
    "docs/guides/mt5_demo_boundary.md",
    "docs/guides/operator_safety.md",
    "docs/guides/incident_response.md",
    "docs/guides/known_limitations.md",
    "docs/guides/persistence_recovery.md",
    "docs/guides/backup_restore.md",
    "docs/adr/ADR-016-observability.md",
)


def test_numbering_map_covers_seq_00_to_14():
    for n in range(15):
        assert f"| {n:02d} |" in MAP, f"missing Sequence {n:02d}"
    assert "observability" in MAP.lower()
    assert "pm6_post_trade" in MAP
    assert "mt5_execution_engine" in MAP
    assert "modules/pm6_execution" in MAP
    assert CANONICAL_SEQUENCES[14].startswith("observability")


def test_readme_does_not_claim_ready():
    lowered = README.lower()
    assert "is **not**" in README.lower() or "not ready" in lowered
    assert "live trading is disabled" in lowered
    # Hyphenated marketing claims are forbidden even as a negation pair.
    assert "demo-ready" not in lowered
    assert "live-ready" not in lowered
    assert "production-ready" not in lowered
    assert "Sequence 14" in README or "observability" in lowered


def test_distinctions_preserved():
    assert "PM6 = `pm6_post_trade`" in MAP or "pm6_post_trade" in MAP
    assert "mt5_execution_engine" in MAP
    assert "Sequence 09" in MAP and "PM8" in MAP
    assert "Sequence 13" in MAP


def test_required_docs_exist():
    missing = [rel for rel in REQUIRED_DOCS if not (ROOT / rel).is_file()]
    assert missing == [], f"missing docs: {missing}"


def test_runbook_markdown_matches_catalog():
    directory = ROOT / "docs" / "runbooks"
    write_markdown(directory)
    for rb in RUNBOOKS:
        path = directory / f"{rb.runbook_id.lower()}.md"
        assert path.is_file(), path
        text = path.read_text(encoding="utf-8")
        assert rb.runbook_id in text
        assert rb.trigger in text
        assert "1. **Trigger.**" in text
        assert "12. **Escalation criteria.**" in text


def test_traceability_has_no_bare_complete():
    text = (ROOT / "docs" / "TRACEABILITY_MATRIX.md").read_text(encoding="utf-8")
    assert "COMPLETE" in text
    assert "implementation" in text.lower()
    assert "| S14-" in text

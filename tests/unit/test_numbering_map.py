"""docs/MODULE_NUMBERING_MAP.md is the name SoT. No bare pm6 for Seq 11."""

from __future__ import annotations

from pathlib import Path

from botmoduleproject1.app.sequence_gate import CANONICAL_SEQUENCES

ROOT = Path(__file__).resolve().parents[2]
MAP = (ROOT / "docs" / "MODULE_NUMBERING_MAP.md").read_text(encoding="utf-8")


def test_numbering_map_file_exists_and_states_rules():
    assert "mt5_execution_engine" in MAP
    assert "pm6_post_trade" in MAP
    assert "Sequence 09 = PM7 journal" in MAP or "Sequence 09 = PM7" in MAP
    assert "previous-session numbering error" in MAP or "error of a previous session" in MAP
    assert "modules/pm6_execution" in MAP
    assert "not mixed" in MAP.lower() or "not mixed into PM8" in MAP


def test_canonical_sequence_11_is_not_pm6():
    assert CANONICAL_SEQUENCES[8] == "pm6_post_trade_controls"
    assert CANONICAL_SEQUENCES[11] == "mt5_execution_engine"
    assert not CANONICAL_SEQUENCES[11].startswith("pm6")
    assert CANONICAL_SEQUENCES[9] == "pm8_database_consolidation"

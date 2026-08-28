"""CLI smoke tests. Live mode is recognized and refused."""

from __future__ import annotations

from pathlib import Path

from botmoduleproject1.cli.entrypoint import main

ROOT = Path(__file__).resolve().parents[2]
TEST_YAML = str(ROOT / "configs" / "test.example.yaml")


def test_doctor_cli_ok(capsys) -> None:
    code = main(["doctor", "--config", TEST_YAML])
    captured = capsys.readouterr()
    assert code == 0
    assert "LIVE TRADING" not in captured.err
    assert "fingerprint=" in captured.out
    assert "NOT TRADE READY" in captured.out


def test_doctor_cli_json(capsys) -> None:
    code = main(["doctor", "--config", TEST_YAML, "--json"])
    captured = capsys.readouterr()
    assert code == 0
    assert "config_fingerprint" in captured.out


def test_live_cli_safe_error(capsys) -> None:
    code = main(["live", "--config", TEST_YAML])
    captured = capsys.readouterr()
    assert code == 2
    assert "LIVE TRADING IS DISABLED" in captured.err


def test_paper_cli_ok(capsys) -> None:
    code = main(["paper", "--config", TEST_YAML])
    assert code == 0
    assert "paper" in capsys.readouterr().out

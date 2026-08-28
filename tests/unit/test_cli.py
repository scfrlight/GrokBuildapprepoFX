"""CLI smoke tests. Live mode is recognized and refused."""

from __future__ import annotations

from pathlib import Path

from botmoduleproject1.cli.entrypoint import main

ROOT = Path(__file__).resolve().parents[2]
TEST_YAML = str(ROOT / "configs" / "test.example.yaml")
DEMO_YAML = str(ROOT / "configs" / "demo.example.yaml")


def test_doctor_cli_ok(capsys) -> None:
    code = main(["doctor", "--config", TEST_YAML])
    captured = capsys.readouterr()
    assert code == 0
    assert "LIVE TRADING" not in captured.err
    assert "fingerprint=" in captured.out
    assert "NOT TRADE READY" in captured.out
    assert "profile=test" in captured.out
    assert "allowed_capabilities=" in captured.out


def test_doctor_cli_json(capsys) -> None:
    code = main(["doctor", "--config", TEST_YAML, "--json"])
    captured = capsys.readouterr()
    assert code == 0
    assert "config_fingerprint" in captured.out
    assert '"profile": "test"' in captured.out


def test_profile_flag_overrides_yaml(capsys) -> None:
    code = main(["doctor", "--config", TEST_YAML, "--profile", "demo"])
    captured = capsys.readouterr()
    assert code == 0
    assert "profile=demo" in captured.out
    assert "allowed_capabilities=" in captured.out


def test_profile_flag_before_mode(capsys) -> None:
    code = main(["--profile", "research", "doctor", "--config", DEMO_YAML])
    captured = capsys.readouterr()
    assert code == 0
    assert "profile=research" in captured.out


def test_live_cli_safe_error(capsys) -> None:
    code = main(["live", "--config", TEST_YAML])
    captured = capsys.readouterr()
    assert code == 2
    assert "LIVE TRADING IS DISABLED" in captured.err


def test_live_profile_cli_safe_error(capsys) -> None:
    code = main(["doctor", "--config", TEST_YAML, "--profile", "live"])
    captured = capsys.readouterr()
    assert code == 2
    assert "LIVE TRADING IS DISABLED" in captured.err


def test_paper_cli_ok(capsys) -> None:
    code = main(["paper", "--config", TEST_YAML])
    assert code == 0
    out = capsys.readouterr().out
    assert "paper" in out
    assert "profile=test" in out

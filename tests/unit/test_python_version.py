"""Python 3.11+ guard. ADR-008. Fail-fast is not optional."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from botmoduleproject1.app.exceptions import PythonVersionError
from botmoduleproject1.app.python_version import (
    MIN_PYTHON,
    assert_python_version,
    is_supported,
)
from botmoduleproject1.app.preflight import check_python_version
from botmoduleproject1.cli.entrypoint import main

ROOT = Path(__file__).resolve().parents[2]
TEST_YAML = str(ROOT / "configs" / "test.example.yaml")


def test_guard_fails_below_311() -> None:
    with pytest.raises(PythonVersionError, match="3.11"):
        assert_python_version(version=(3, 10, 21))
    with pytest.raises(PythonVersionError, match="3.11"):
        assert_python_version(version=(3, 9, 0))


def test_guard_accepts_311_and_newer() -> None:
    assert assert_python_version(version=(3, 11, 0)) == (3, 11, 0)
    assert assert_python_version(version=(3, 12, 1))[:2] == (3, 12)
    assert is_supported((3, 11))
    assert not is_supported((3, 10, 21))
    assert MIN_PYTHON == (3, 11)


def test_preflight_python_check_fails_on_310() -> None:
    result = check_python_version(version=(3, 10, 21))
    assert result.passed is False
    assert result.critical is True
    assert "3.11" in result.message


def test_preflight_python_check_passes_on_311() -> None:
    result = check_python_version(version=(3, 11, 2))
    assert result.passed is True


def test_python_version_fail_fast(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    """doctor --profile test must abort with PythonVersionError on <3.11."""
    monkeypatch.setattr(
        "botmoduleproject1.app.python_version.interpreter_version",
        lambda: (3, 10, 21),
    )
    code = main(["doctor", "--profile", "test", "--config", TEST_YAML])
    captured = capsys.readouterr()
    assert code == 1
    assert "STARTUP FAILED" in captured.err
    assert "3.11" in captured.err
    assert "Python 3.10.21 is not supported" in captured.err


@pytest.mark.real_interpreter
def test_document_actual_pytest_interpreter() -> None:
    """Records the interpreter that collected this suite. Not a skip of the guard."""
    actual = sys.version_info[:3]
    assert actual >= (3, 10)
    if actual < (3, 11):
        assert actual[:2] == (3, 10), "unexpected interpreter below 3.11"


@pytest.mark.real_interpreter
def test_subprocess_doctor_obeys_real_interpreter() -> None:
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "botmoduleproject1",
            "doctor",
            "--profile",
            "test",
            "--config",
            TEST_YAML,
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if sys.version_info[:2] < (3, 11):
        assert proc.returncode == 1
        assert "STARTUP FAILED" in proc.stderr
        assert "3.11" in proc.stderr
    else:
        assert proc.returncode == 0, proc.stderr
        assert "fingerprint=" in proc.stdout

"""Python 3.11+ guard. ADR-008 documents the sandbox 3.10 deviation."""

from __future__ import annotations

import sys

import pytest

from botmoduleproject1.app.exceptions import PythonVersionError
from botmoduleproject1.app.python_version import (
    MIN_PYTHON,
    assert_python_version,
    is_supported,
)
from botmoduleproject1.app.preflight import check_python_version


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


@pytest.mark.real_interpreter
def test_document_actual_pytest_interpreter() -> None:
    """Records the interpreter that collected this suite. Not a skip of the guard."""
    actual = sys.version_info[:2]
    assert actual >= (3, 10)
    if actual < (3, 11):
        assert actual == (3, 10), "unexpected interpreter below 3.11"

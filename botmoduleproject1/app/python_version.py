"""Python version guard. Production floor is 3.11+ (ADR-001, ADR-008)."""

from __future__ import annotations

import sys

from botmoduleproject1.app.exceptions import PythonVersionError

MIN_PYTHON = (3, 11)
MIN_PYTHON_DISPLAY = "3.11"


def interpreter_version() -> tuple[int, int, int]:
    """Indirection so tests can inject a version without rewriting sys."""
    info = sys.version_info
    return (int(info.major), int(info.minor), int(info.micro))


def is_supported(version: tuple[int, ...] | None = None) -> bool:
    ver = version or interpreter_version()
    return tuple(ver[:2]) >= MIN_PYTHON


def assert_python_version(version: tuple[int, ...] | None = None) -> tuple[int, int, int]:
    """Fail-fast if the interpreter is older than 3.11.

    Pass ``version`` to check a hypothetical interpreter (unit tests).
    """
    ver = tuple(version or interpreter_version())
    if ver[:2] < MIN_PYTHON:
        raise PythonVersionError(
            "Python {major}.{minor}.{micro} is not supported. "
            "BotModuleProject1 requires Python {floor}+. "
            "See docs/adr/ADR-008-python-version-constraint.md.".format(
                major=ver[0],
                minor=ver[1] if len(ver) > 1 else 0,
                micro=ver[2] if len(ver) > 2 else 0,
                floor=MIN_PYTHON_DISPLAY,
            )
        )
    if len(ver) >= 3:
        return (int(ver[0]), int(ver[1]), int(ver[2]))
    return (int(ver[0]), int(ver[1]), 0)

"""Shared fixtures.

ADR-008: this App Builder sandbox runs pytest on CPython 3.10.21 because
CPython 3.11 is present but has no pip/ensurepip. Production and CLI still
require 3.11+. Tests patch interpreter_version() so the guard is exercised
without blocking the suite. See tests/unit/test_python_version.py.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _sandbox_python_floor(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest):
    if request.node.get_closest_marker("real_interpreter"):
        yield
        return
    monkeypatch.setattr(
        "botmoduleproject1.app.python_version.interpreter_version",
        lambda: (3, 11, 2),
    )
    yield

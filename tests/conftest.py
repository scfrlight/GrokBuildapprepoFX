"""Shared fixtures.

ADR-008 production floor is Python 3.11+. Official suite runs on 3.11+
(venv / CI). If a collector is still 3.10 (App Builder system python),
unit tests patch interpreter_version() so the rest of the kernel can be
exercised; CLI and unpatched preflight still see the real interpreter.
The patch is not a production escape hatch.
"""

from __future__ import annotations

import sys

import pytest


@pytest.fixture(autouse=True)
def _sandbox_python_floor(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest):
    if request.node.get_closest_marker("real_interpreter"):
        yield
        return
    if sys.version_info[:2] >= (3, 11):
        yield
        return
    monkeypatch.setattr(
        "botmoduleproject1.app.python_version.interpreter_version",
        lambda: (3, 11, 2),
    )
    yield

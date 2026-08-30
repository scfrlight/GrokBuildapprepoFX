# ADR-008: Python version constraint and sandbox deviation

- Status: Accepted
- Date: 2026-08-28
- Sequence: 02

## Context

ADR-001 and `pyproject.toml` require **Python 3.11+**. Sequence 01 tests in the
Grok App Builder sandbox ran on **CPython 3.10.21**. CPython 3.11.2 is installed
in that sandbox but has **no pip, no ensurepip, and no project dependencies**,
so the suite cannot be executed on 3.11 there.

Silently ignoring the floor would hide a portability defect. Pretending the
suite ran on 3.11 would be a lie.

## Decision

1. `requires-python = ">=3.11"` remains the published constraint.
2. Runtime and CLI call `assert_python_version()` and **fail-fast** with
   `PythonVersionError` when the interpreter is older than 3.11.
3. Preflight includes a `python.version` check.
4. Unit tests cover the guard by passing explicit version tuples (including
   `(3, 10, 21)`). They do not rewrite the floor.
5. The App Builder pytest interpreter is documented here as **CPython 3.10.21**.
   `tests/conftest.py` patches `interpreter_version()` to `(3, 11, 2)` so the
   rest of the suite can exercise the kernel. The patch is **not** a production
   escape hatch. CLI and unpatched preflight still see the real interpreter.
6. Operators and CI on a real machine MUST use Python 3.11+.
7. GitHub Actions (`.github/workflows/tests.yml`) runs the suite on CPython 3.11 and 3.12, plus a 3.10 job that proves `doctor --profile test` fail-fast without installing pydantic.

## Consequences

- `python -m botmoduleproject1 doctor` on this sandbox exits 1 with a Python
  version error. That is correct fail-fast, not a regression of live-disable.
- Live mode still exits 2 when the interpreter is 3.11+ (proven by CLI tests).
- Tech debt remains until the sandbox provides a 3.11 environment with
  `pydantic` / `pydantic-settings` installed.

## Alternatives considered

1. Lower `requires-python` to 3.10 — rejected (UTC/`tomllib`/typing target).
2. Skip the guard when `pytest` is running — rejected (silent ignore).
3. Vendor wheels into the repo for 3.11 — rejected (supply-chain / size).

## Validation implications

- `tests/unit/test_python_version.py` fails the build if the guard accepts 3.10.
- `tests/unit/test_python_version.py::test_document_actual_pytest_interpreter`
  records the real collector version without disabling the guard.

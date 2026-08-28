# Tests

- `unit/` — isolated (settings, profiles, flags, preflight, lifecycle, CLI, …)
- `contract/` — schema and layer rules (Sequence 01)
- `integration/` — fakes, never live broker by default
- `e2e/` — future doctor/demo-observe paths

Sequence 02 asserts Python 3.11+ guard, pydantic-settings prefix isolation,
secret redaction, profile hard-block for `live`, dangerous-flag env-only, and
preflight pass/fail. Suite: 67 tests.

ADR-008: this sandbox collects pytest on CPython 3.10.21; `conftest.py` patches
`interpreter_version` so the kernel can be exercised. The guard itself is tested
with explicit `(3, 10, 21)` tuples.

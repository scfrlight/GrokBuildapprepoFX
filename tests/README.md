# Tests

- `unit/` — isolated (settings, profiles, flags, preflight, lifecycle, CLI, PM2 engines, …)
- `contract/` — schema and layer rules (Sequence 01 + PM2 outputs)
- `integration/` — fakes, never live broker by default
- `e2e/` — future doctor/demo-observe paths

Sequence 03 asserts PM2 ranking/context behind `enable_pm2_market_data` (YAML
false; test/research env opt-in), no execution leakage, UTC identity,
determinism, and fail-closed freshness. Suite: 110 tests.

ADR-008: this sandbox collects pytest on CPython 3.10.21; `conftest.py` patches
`interpreter_version` so the kernel can be exercised. The guard itself is tested
with explicit `(3, 10, 21)` tuples.

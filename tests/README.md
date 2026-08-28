# Tests

- `unit/` — isolated kernel tests (settings, registry, lifecycle, health, CLI)
- `contract/` — v1 domain schemas and layer rules
- `integration/` — fakes, never live broker by default
- `e2e/` — future doctor/demo-observe paths

Sequence 01 covers PM1 kernel + v1 contracts. No broker, no orders.

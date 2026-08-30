# PostgreSQL durability evidence

Captured 2026-08-30 against PostgreSQL 16.2.

- `pytest-3.11.log` — 589 passed (includes live PG tests)
- `doctor-3.11.*` — NOT TRADE READY
- `live.*` — exit 2, LIVE TRADING IS DISABLED
- `doctor-3.10.*` — ADR-008 fail-fast
- `postgresql_durability.json` — backend identity, no SQLite fallback, trading_readiness false
- Python 3.12: NOT-RUN-HERE; CI matrix still 3.11/3.12 with `postgres:16` service

`production_durable` remains refused. Sequence 11+ remains blocked.

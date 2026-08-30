# PM8 PostgreSQL durability

Not Sequence 11+. Not Sequence 15. PostgreSQL is a backend of `pm8_persistence`.

`production_durable` remains **refused**. Trading readiness remains **false**. This stage does not claim production-ready, live-ready, or demo-ready.

## Backend identity

| Mode | Store | Fallback |
|---|---|---|
| `memory` / `disabled` | `SqliteStore(":memory:")` | n/a (test only) |
| `sqlite_local` | file-backed SQLite WAL | none (missing path raises) |
| `postgresql` | `PostgresStore` | **none**. Missing DSN or down server → `StorageUnavailable` |

DSN: **only** `BOTMODULEPROJECT1_DATABASE_URL`. Unprefixed `DATABASE_URL` is ignored.

## Schema

PostgreSQL 16 dialect of Seq 09 v1 + Seq 10 v2 + remediation overlay:

- `NUMERIC(28,8)` for money (`money_records.amount_canonical`, `positions_proj.qty/avg_px`)
- `TIMESTAMPTZ` for all timestamps
- `JSONB` for variable payloads
- append-only triggers on `events`, `audit_log`, `executions`, `integrity_log`, `mismatch_actions`, `money_records`, `repair_log`
- unique `(edge, scope, key)` on `idempotency_keys`
- outbox claim: `SELECT ... FOR UPDATE SKIP LOCKED`

Partitioning guidance (not enabled by default): `RANGE(occurred_at)` on `events` / `audit_log` once volume warrants. Tests stay unpartitioned so `TRUNCATE` remains legal (DELETE is blocked).

Table catalog: `botmoduleproject1/modules/pm8_persistence/postgres/ddl.py` `TABLE_FAMILIES`.

## Transactions

`PersistenceApiV1.in_transaction` is re-entrant. Signal / order / execution / recon writes keep event + outbox + idempotency + family row + audit in one transaction.

## Outbox

PostgreSQL relay uses `CLAIM_BATCH_SQL` (`FOR UPDATE SKIP LOCKED`). SQLite still claims sequentially and is local/test-only.

## Restore

Isolated only. Live DSN refused. Isolated SQLite file or isolated PostgreSQL database.

## Safety

- `trading_readiness=false`
- `accept_trade=false`
- no MT5 / Telegram / broker submission
- venue absence cannot PASS reconciliation

## Evidence

`docs/evidence/postgresql/`

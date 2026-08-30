# Durable storage

File-backed SQLite survives process restart. `:memory:` is unit-test only.

- PM8: `SqliteStore(path)` uses WAL. Missing parent directory raises `StorageUnavailable`. Silent memory fallback is forbidden for `sqlite_local`.
- PM7: `SqliteJournal` / `FileJournal` reload committed records on open.
- Schema overlay `SCHEMA_V3` is applied on every open (`CREATE TABLE IF NOT EXISTS`) and does not bump the Seq 10 v1/v2 migration catalog.
- Backend identity is in `PersistenceApiV1.health()` / `pm8.backend` check.

PostgreSQL is **BLOCKED** in this environment.

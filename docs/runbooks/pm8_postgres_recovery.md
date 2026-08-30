# Runbook — PM8 PostgreSQL recovery

id: pm8-postgres-recovery
owner: persistence
trading_must_halt: true

## Symptoms

- `pm8.postgres` health check failed
- `StorageUnavailable: postgresql configured but unavailable`
- checkpoint lag / projection lag
- integrity `compromised`

## Immediate action

1. Leave trading flags false. Do not enable MT5.
2. Confirm DSN is `BOTMODULEPROJECT1_DATABASE_URL` (not `DATABASE_URL`).
3. `SELECT 1` against the DSN. If down, do not fall back to SQLite.
4. If integrity compromised: stop writers, snapshot the cluster, do not UPDATE/DELETE `events`.
5. Restore-apply only onto an **isolated** database. Live DSN is refused.

## Restart

Load latest snapshot + checkpoint, replay tail events, rebuild named projections, resume outbox workers. If consistency is uncertain, remain observe-only.

## Unblock next stage

Not unblocked here. Sequence 11+ / trading enablement still requires explicit architect approval.

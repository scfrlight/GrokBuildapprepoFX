# Migration policy (PM8 PostgreSQL)

| Version | Origin | Tables | Rollback |
|---|---|---|---|
| 1 | Sequence 09 | events, signals, orders, executions, idempotency, outbox, inbox, checkpoints, projections, recon, audit, integrity, repair, snapshots, backup, export | refused if journal non-empty |
| 2 | Sequence 10 | backup_schedules, restore_verifications, restart_drills | v2→v1 allowed (drops those three) |
| overlay | remediation + PG | named projections, recon runs, money_records, append-only triggers, SKIP LOCKED indexes | forward-fix; overlay is `CREATE IF NOT EXISTS` |

Checksums are stored in `schema_migrations`. Repeat `upgrade_to(2)` is a no-op.

No destructive drop of v1 while events exist. No automatic SQLite→PostgreSQL data rewrite in this stage.

PostgreSQL DDL lives in `modules/pm8_persistence/postgres/ddl.py`. SQLite DDL stays in `schema/ddl.py`.

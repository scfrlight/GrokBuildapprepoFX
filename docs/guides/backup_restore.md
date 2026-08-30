# Backup / restore

See `docs/runbooks/pm8a_backup_restore.md` and Sequence 14 runbooks `RB-BACKUP-VERIFICATION` / `RB-RESTORE-VERIFICATION`.

Dump checksum = sha256(full events JSON) including event_id / correlation_id / occurred_at / row_hash. It is **run-specific**. Restore verifies a file against **its own** checksum. `payload_canonical_sha256` hashes only `payload_json` and is comparable across runs.

## Isolated restore-apply (this remediation)

Flows: `verify_backup` → `prepare_restore_target` → `dry_run_restore` → `apply_restore` → `post_restore_verify` / `restore_abort`.

- Dry-run does not mutate the source store.
- Apply writes only to a new isolated SQLite file.
- Applying onto the live store is refused.
- Trading readiness stays false. No MT5 send.
- Pre-apply copy is kept for abort.
- Backward sequence in a backup is rejected.
- Isolated restore-apply: SQLite file target or isolated PostgreSQL DSN. Live store/DSN refused. `trading_blocked` always.

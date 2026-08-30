# Backup / restore guide

See `docs/runbooks/pm8a_backup_restore.md` and Sequence 14 runbooks `RB-BACKUP-VERIFICATION` / `RB-RESTORE-VERIFICATION`.

Dump checksum = sha256(full events JSON) including event_id / correlation_id / occurred_at / row_hash. It is **run-specific**. Restore verifies a file against **its own** checksum. `payload_canonical_sha256` hashes only `payload_json` and is comparable across runs.

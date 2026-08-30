# Runbook — PM8a backup, restore, restart (Sequence 10)

Scope: test/research only. Never against a live trading runtime.

## Backup

1. Enable `enable_pm8_persistence` in test profile.
2. Call `PersistenceApiV1.backup(directory)`.
3. Confirm `verified=true` and checksum match.

Cadence default 86400s, retain 7. Cadence below 60s is refused so backup cannot starve the runtime.

## Restore verification

1. `RestoreService.verify_file(path, expected_checksum)`.
2. Mismatch raises; API must not accept writes from the corrupt file.
3. Verification is isolated from the trading tick (Sequence 12 recovery-before-trading still applies).

## Restart drill

`RestartDrill().run(sqlite_path)` must log seed → close → reopen → integrity valid.

## Rollback

`MigrationService.rollback(1)` from v2 is allowed. Rolling back v1 with a non-empty journal is refused.

# Sequence 10 Report — PM8a Migration, Backup & Recovery Hardening

Date (UTC): 2026-08-30  
Git home: `scfrlight/GrokBuildapprepoFX`  
Display name: **PM8a migrations / backup / restore / restart drills**  
Canonical sequence: **10** (historical `sequence_10_report.md` is the mislabeled operator early build)

## 1. Git commit hash

Workspace has no `.git`. Prior main: `a2a1890`. Kernel push follows this wave.

## 2. Created / updated files

### Created

- `botmoduleproject1/modules/pm8_persistence/migrations.py` (`MigrationService`, `RestoreService`, `RestartDrill`, `BackupSchedule`)
- `botmoduleproject1/modules/pm8_persistence/schema/ddl.py` (`SCHEMA_V2_UP` / `SCHEMA_V2_DOWN`)
- `docs/runbooks/pm8a_backup_restore.md`
- `tests/unit/test_pm8a_seq10.py`

### Updated

- Sequence 09 store (`current_version` is last applied migration, down ⇒ version-1)

## 3. Component status

| Component | Status | Notes |
|---|---|---|
| Versioned migrations | COMPLETE | v1 (Seq 09) → v2 hardening tables |
| Rollback policy | COMPLETE | v2→v1 allowed; v1 drop with journal refused |
| Backup schedules | COMPLETE | retain_count prune; cadence < 60s refused in runbook |
| Restore verification | COMPLETE | checksum mismatch raises; does not mutate live seq |
| Corruption / drift | COMPLETE | Seq 09 integrity tests + corrupt backup refused |
| Restart drills | COMPLETE | seed → close → reopen → integrity valid |
| Runbook | COMPLETE | `docs/runbooks/pm8a_backup_restore.md` |
| Runtime isolation | COMPLETE | backup/restore do not tick the orchestrator |

## 4. Restore verification + restart drill logs (reproduced 2026-08-30 09:38 UTC)

```
RESTART_DRILL {
  'passed': True,
  'log': [
    'seed disposition=committed seq=1',
    'closed',
    'reopen seq=1 integrity=valid passed=True'
  ],
  'sequence': 1
}
BACKUP checksum=8d616114a1e72cbd0da2a45c846c20fb13b3b71c7f6e87bdcb4f3ed41bfa6420
       verified=True event_count=1
RESTORE_VERIFY ok
```

Backup/restore did not change `last_sequence` on the live store (asserted by `test_backup_restore_verification_does_not_touch_runtime`).

## 5. Test results (build gate)

- Sequence 10 gate file: **5 passed** (`tests/unit/test_pm8a_seq10.py`)
- Full suite: **480 passed**
- Python: CPython 3.10.21 (ADR-008 deviation)

## 6. Build gate

**PASS** (hardening of persistence only; not a trading path)

## 7. Residual risks

- File-backed SQLite is still not production durable.
- Restore applies only after isolated verification; operators must not restore onto a running tick (runbook).

## 8. Trading readiness

The system is NOT ready for live trading, demo trading, paper trading, or production.

## 9. Exact next step

Sequence 11 — PM6 MT5 Execution & Exit Engine (Demo-only; existing `pm6_post_trade` is not renamed).

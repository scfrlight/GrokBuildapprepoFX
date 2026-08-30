# PM7 / PM8 durability remediation plan

Status: **REMEDIATION PASSED WITH PARTIALS** — 2026-08-30.  
Not Sequence 15. PostgreSQL production durability remains **BLOCKED**.

Source confidence: in-repo Seq 09 PM7 prompt + reconstructed PM8a (`RECONSTRUCTED-SOURCE`).  
`PM7_Master_Prompt.md` / original Drive `PM8a_Build_Spec.md` = **SOURCE-MISSING**.

## Priority order (this wave)

| # | Capability | Status | Code | Tests | Evidence |
|---|---|---|---|---|---|
| 1 | Durable storage reload | COMPLETE (SQLite local/test) | `pm8_persistence/store.py` `pm7_persistence/infrastructure/repositories/sqlite_journal.py` | `test_file_backed_sqlite_survives_process_restart` `test_pm7_journal_and_snapshot_survive_restart` | `docs/evidence/remediation/durable_restart.log` |
| 2 | Decimal money | COMPLETE for PM8 persist_* money keys | `pm8_persistence/money.py` | `test_decimal_round_trip_and_reject_float` | `decimal_roundtrip.log` |
| 3 | Unit of Work | COMPLETE (nested tx + fault injection) | `PersistenceApiV1.in_transaction` | `test_uow_failure_injection_rolls_back` | `uow_failure_injection.log` |
| 4–5 | Outbox + relay | COMPLETE local/test SQLite | `outbox.py` `relay_outbox` | `test_outbox_relay_retry_dead_letter_and_restart` | `outbox_relay.log` |
| 6 | Inbox / idempotency | COMPLETE with retry/DLQ | `consume_inbox` | `test_inbox_retry_dead_letter_and_duplicate` `test_request_idempotency_hash_conflict` | `inbox_dedupe.log` |
| 7 | Named projections | COMPLETE as rebuildable read models | `projections.py` `rebuild_named_projections` | `test_named_projections_rebuild_and_duplicate` | `projection_rebuild.log` |
| 8 | Reconciliation run aggregate | COMPLETE | `reconciliation.py` | `test_reconciliation_run_lifecycle_and_no_silent_pass` | `reconciliation_lifecycle.log` |
| 9 | Isolated restore-apply | COMPLETE SQLite isolated target | `restore_apply.py` | `test_isolated_restore_apply` | `restore_apply.log` |
| 10 | PM7 durable journal | PARTIAL→hardened reload; warehouse still not production | sqlite/file journals | `test_pm7_*survive_restart` | `pm7_capability.log` |
| 11 | Safety | COMPLETE (unchanged locks) | flags / observability | `test_reconciliation_boundaries.py` | `safety_invariants.log` |

## Explicit limitations

- `:memory:` remains valid for unit tests only.
- SQLite outbox relay is **local/test-only**; PostgreSQL `FOR UPDATE SKIP LOCKED` is **BLOCKED**.
- Restore-apply refuses the live store; trading stays blocked.
- Named projections are not canonical truth.
- Existing JSON payload bags remain; money keys are canonical decimal strings. Residual non-money floats in unrelated modules are **PARTIAL**.
- PM7 evidence/snapshot sidecars persist with sqlite/file backends; in-memory mode does not.

## Unblock PostgreSQL

Requires a provisioned server, NUMERIC mappings, SKIP LOCKED relay tests, and a separate authorization. Not this wave.

# PM7 / PM8a gap matrix after durability remediation

Statuses: COMPLETE | PARTIAL | BLOCKED | SOURCE-MISSING | RECONSTRUCTED-SOURCE | NEEDS-HARDENING | NOT-IN-SCOPE.

COMPLETE requires implementation + test + evidence.

## PM8 / PM8a (RECONSTRUCTED-SOURCE)

| Block | Before recon | After remediation | Notes |
|---|---|---|---|
| A Domain / Decimal | ABSENT | COMPLETE for persist_* money keys; residual JSON bags PARTIAL | `money.py` |
| B Write / same UoW | PARTIAL | COMPLETE for signal/order/execution/recon | nested `in_transaction` |
| C Outbox relay | ABSENT | COMPLETE local SQLite | PostgreSQL BLOCKED |
| D Recovery / checkpoints | PARTIAL | COMPLETE monotonic + file reload | |
| E Recon run aggregate | ABSENT | COMPLETE | venue cannot PASS |
| F Named projections | ABSENT | COMPLETE as read models | not canonical |
| G Data API | COMPLETE caveats | COMPLETE v1 | unsupported version rejected |
| H Restore-apply | ABSENT | COMPLETE isolated SQLite | live target refused; PG BLOCKED |

## PM7

| Capability | Status | Limitation |
|---|---|---|
| Durable journal reload | COMPLETE sqlite/file | memory mode does not persist |
| Immutable rows / ordering / lineage | COMPLETE in-process + reload | |
| Evidence / snapshot persist | COMPLETE sqlite/file sidecars | |
| Replay | COMPLETE in-process; reloadable source | session table not a warehouse |
| Integrity | PARTIAL | detection not proof |
| Retention/freeze | COMPLETE in-process | |
| Query/export | COMPLETE in-process | |
| Backup apply | metadata-only in PM7 | byte restore is PM8 |
| production_durable | BLOCKED | validator refuses |

PostgreSQL production durability: **BLOCKED**. Sequence 15: **BLOCKED**.

# PM8a Build Spec — reconstructed

Status: **Reconstructed** 2026-08-30 from the architect correction prompt.  
Original `PM8a_Build_Spec.md` was not found on Drive or GitHub. Reconcile if it appears.  
This file is the working spec for canonical Sequences **09** (consolidation) and **10** (hardening).

Live / demo / paper / production trading is out of scope. `production_durable` is refused.

## Sequence split

| Sequence | Scope |
|---|---|
| 09 | Consolidated schema, repositories, application services, versioned API, integrity/repair, backup/export capability, idempotency, outbox/inbox |
| 10 | Versioned migrations + rollback, backup schedules/retention, restore verification, corruption/ledger-drift tests, restart drills, runbooks |

## 13. Table families

Every family is append-friendly. Committed rows are immutable. Corrections are new rows linked by `causation_id`.

1. **event** — envelope, hash chain, sequence numbers  
2. **signal** — PM2/PM3 signal facts  
3. **order** — local order intent / OMS records (not venue tickets)  
4. **execution** — fills, acks, DEMO-*/SIM-* lifecycle  
5. **reliability** — idempotency keys, outbox, inbox  
6. **recovery** — checkpoints, schema_migrations  
7. **projection** — rebuildable read models  
8. **reconciliation** — local vs venue; no venue → `degraded` / `unavailable`, never silent pass  
9. **audit** — actor actions, integrity log, repair log, backup manifest, exports  

## 15. Repository protocols (minimum 19)

1. `EventRepository`  
2. `SignalRepository`  
3. `OrderRepository`  
4. `ExecutionRepository`  
5. `IdempotencyRepository`  
6. `OutboxRepository`  
7. `InboxRepository`  
8. `RecoveryRepository`  
9. `ProjectionRepository`  
10. `ReconciliationRepository`  
11. `AuditRepository`  
12. `SnapshotRepository`  
13. `IntegrityLogRepository`  
14. `BackupManifestRepository`  
15. `SchemaVersionRepository`  
16. `UnitOfWork`  
17. `RepairJournalRepository`  
18. `ExportPackageRepository`  
19. `PositionProjectionRepository`  

Downstream modules **must not** import these implementations. They use `PersistenceApiV1` only.

## 16. Application services (minimum 20)

1. `EventIngestService`  
2. `SignalPersistService`  
3. `OrderPersistService`  
4. `ExecutionPersistService`  
5. `IdempotencyGuardService`  
6. `OutboxEnqueueService`  
7. `OutboxDispatchService`  
8. `InboxConsumeService`  
9. `ProjectionRebuildService`  
10. `ReconciliationPersistService`  
11. `AuditTrailService`  
12. `IntegrityCheckService`  
13. `RepairPolicyService`  
14. `BackupExportService`  
15. `SnapshotCaptureService`  
16. `RecoveryCheckpointService`  
17. `VersionedQueryService`  
18. `TransactionCoordinatorService`  
19. `DedupService`  
20. `PersistenceHealthService`  

## 19. Idempotency edges

| Edge | Key | Effect |
|---|---|---|
| request | `idempotency_key` on command | Same key + scope returns stored result; no second write |
| event consumer | `event_id` | Duplicate envelope ignored (`duplicate_ignored`) |
| broker callback | `venue_callback_id` | Duplicate ack/fill does not mutate committed execution |
| projection | `projection_name` + `source_event_seq` | Rebuild is deterministic; duplicate apply is a no-op |

## 20. Outbox / inbox

Write the business row and the outbox row in **one** unit of work (at-least-once delivery).  
Inbox records processed `event_id` so consumers are **effectively-once** at the business layer.  
Dispatcher retries are bounded. Poison messages go to quarantine. Never drop silently.

## Repair policy

- Hash mismatch → `compromised`. Do not rewrite the chain.  
- Repair = new correction event + repair_log row.  
- Freeze blocks purge.  
- Restore must verify checksum before the API accepts writes.

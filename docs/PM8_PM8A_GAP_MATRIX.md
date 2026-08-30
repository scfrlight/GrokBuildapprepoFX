# PM8 / PM8a capability gap matrix

Reconciliation 2026-08-30. Sequence 15 not started.

**Identity:** `botmoduleproject1.modules.pm8_persistence` is the PM8 persistence engine. **PM8a is the build-spec / Seq 10 hardening identity of that same package**, not a second business module. Operator UX is Sequence 13 / `pm8_operator`.

**Spec:** reconstructed `docs/prompts/PM8a_Build_Spec.md`. Original Drive file is **SOURCE-MISSING**. Do not invent missing original clauses.

**Default bind:** `enable_pm8_persistence` YAML false → `NullStorage`. `production_durable` refused. Never a venue.

Statuses: COMPLETE | PARTIAL | ABSENT | BLOCKED | SOURCE-MISSING | NOT-IN-SCOPE.

COMPLETE requires implementation path **and** test or evidence. Catalog-only names without behaviour are not COMPLETE.

## A. Domain models

| Capability | Source | Implementation | Contract | Test | Evidence | Status | Limitation |
|---|---|---|---|---|---|---|---|
| Enums (families, edges, dispositions) | reconstructed §13, §19 | `contracts/v1/pm8_persistence.py` | same | `test_protocol_and_service_minimums` | Seq 09 report | COMPLETE | reconstructed spec |
| Typed write records | audit A | unused `PersistRecord`; writes are `dict`+JSON | `PersistRecord` unused on write path | none for typed rows | — | PARTIAL | no Signal/Order/Fill records in PM8 contract |
| Timezone-aware timestamps | ADR-003 | `utc_now().isoformat()` on writes | `ensure_aware_utc` on unused PersistRecord | ADR-003 tests elsewhere | — | PARTIAL | SQLite stores ISO strings |
| Decimal for accounting | audit A / rem | `money.py` + persist_* sanitize | canonical string | `test_decimal_round_trip_and_reject_float` | remediation | COMPLETE persist_* keys | residual JSON bags |
| Trade-intent / no-trade records | audit B | **none** | none | none | — | ABSENT | PM3 intents not first-class here |

## B. Write side

| Capability | Source | Implementation | Contract | Test | Evidence | Status | Limitation |
|---|---|---|---|---|---|---|---|
| Event archive + hash chain | §13 event | `PersistenceApiV1.ingest_event` | `TableFamily.EVENT` | `test_append_only_and_dedupe` | Seq 09 | COMPLETE | sqlite local |
| Signal persistence | §16 | `persist_signal` | SIGNAL family | Seq 09 edges | — | COMPLETE | family row committed **after** event UoW |
| Order ledger (local OMS) | §13 order | `persist_order` UNIQUE `client_order_id` | ORDER | `test_four_idempotency_edges` | — | PARTIAL | not full lifecycle ledger |
| Execution reports | §13 execution | `persist_execution`; rejects `pm5_broker` | EXECUTION | `test_broker_truth_label_rejected` | — | PARTIAL | fills only inside payload_json |
| Audit | §13 audit | `audit()` redacts secret keys | — | operator/PM8 tests | — | COMPLETE | in-process |
| Idempotency keys | §19 | `idempotency_keys` | `IdempotencyEdge` | `test_four_idempotency_edges` | — | COMPLETE | four edges |
| Family row + event same UoW | §20 | event+outbox yes; signal/order/execution rows after commit | — | none asserting same UoW for family rows | — | PARTIAL | crash window after event commit |

## C. Reliability

| Capability | Source | Implementation | Contract | Test | Evidence | Status | Limitation |
|---|---|---|---|---|---|---|---|
| Request idempotency | §19 | REQUEST edge | enum | `test_four_idempotency_edges` | — | COMPLETE | — |
| Event-consumer dedupe | §19 | EVENT_CONSUMER / `event_id` | enum | `test_append_only_and_dedupe` | — | COMPLETE | — |
| Broker-callback dedupe | §19 | `venue_callback_id` | enum | same | — | COMPLETE | simulated ids only |
| Projection dedupe | §19 | `apply_projection_event` | enum | same | — | COMPLETE | generic JSON bag |
| Outbox enqueue same UoW as event | §20 | `ingest_event` | `OutboxState` | `test_outbox_transactional_with_event` | — | COMPLETE | — |
| Outbox relay / bus | §20 | `dispatch_outbox` marks published in-process | — | none for external relay | — | ABSENT | not a message bus |
| Retry + quarantine | §20 | attempts > max → `quarantined` | state | none dedicated | — | PARTIAL | no backoff; quarantine is a state not a DLQ table |
| Inbox effectively-once | §20 | `consume_inbox` INSERT OR IGNORE | — | `test_inbox_effectively_once` | — | PARTIAL | handler after accept (crash skip) |

## D. Recovery

| Capability | Source | Implementation | Contract | Test | Evidence | Status | Limitation |
|---|---|---|---|---|---|---|---|
| Snapshots | §16 | `snapshot()` | dict | Seq 10 isolation | — | COMPLETE | events JSON dump |
| Checkpoints | §16 | `checkpoint` / `latest_checkpoint` | — | `test_pm8_checkpoint_monotonic` | reconciliation | PARTIAL→hardening | monotonic cursor now enforced |
| Restart drill | Seq 10 | `RestartDrill` | — | `test_restart_drill` | `docs/evidence/restart_drill.log` | COMPLETE | test/research |
| Projection rebuild | §16 | `rebuild_projections` → `family_counts` | — | `test_projection_rebuild_deterministic` | — | PARTIAL | not business read models |
| Monotonic checkpoint | audit D | `SqliteStore.save_checkpoint` rejects lower `cursor_seq` | — | `test_pm8_checkpoint_monotonic` | this recon | COMPLETE (this change) | — |
| Replay | PM7 / audit D | **not in PM8** | — | PM7 replay tests | — | ABSENT in PM8 | lives in PM7 journal |
| Recovery-before-trading | Seq 12 | `UnifiedRuntime.recover/tick` | — | `test_seq12_orchestrator.py` | — | COMPLETE | observe-only; no trade |
| Freeze blocks purge | reconstructed repair | **no freeze/purge in PM8** | — | — | — | ABSENT in PM8 | PM7 retention has freeze |

## E. Reconciliation

| Capability | Source | Implementation | Contract | Test | Evidence | Status | Limitation |
|---|---|---|---|---|---|---|---|
| No silent pass without venue | §13 recon | `persist_reconciliation` rejects `pass` if `venue_ref is None` | inline | `test_recon_without_venue_never_silent_pass` | — | COMPLETE | — |
| Recon run aggregate | audit E | **none** | none | none | — | ABSENT | single rows only |
| Item / severity / mismatch action | audit E | `state` string; no severity enum | none in pm8 contract | — | — | PARTIAL | typed recon remains in PM7 |
| Correction vs rewrite | repair policy | `repair()` emits new event | `RepairAction` | `test_integrity_and_repair_does_not_rewrite` | — | COMPLETE | hash-chain only |

## F. Named projections

| Projection | Status | Notes |
|---|---|---|
| open orders | COMPLETE (read model) | rebuilt from ORDER events; not canonical |
| open positions | COMPLETE (read model) | Decimal canonical qty/avg_px |
| closed trades | COMPLETE (read model) | filled/cancelled states |
| symbol performance | COMPLETE (read model) | last-event bag |
| profile performance | COMPLETE (read model) | producer bag |
| daily summary | COMPLETE (read model) | day key |
| operator dashboard view | COMPLETE (read model) | latest audit pointer |

Generic `projections` table + `family_counts` rebuild still exists. Named projections are rebuildable read models, not canonical truth.

## G. Data API

| Capability | Status | Notes |
|---|---|---|
| `PersistenceApiV1` only downstream path | COMPLETE | runtime + Seq 11 inject the API |
| No raw repository classes | PARTIAL | 19 protocols are types; one `SqliteStore`; `.store` is public; tests/scripts import store |
| API versioning | PARTIAL | v1 only; schema v1/v2 are migrations |
| Authorized query | COMPLETE | `query_events(authorized=True)` |

## H. Storage / backup / integrity

| Capability | Status | Notes |
|---|---|---|
| Schema v1 + v2 | COMPLETE | `schema/ddl.py` |
| Migrations + rollback policy | COMPLETE | v2→v1 allowed; v1 drop with journal refused |
| Backup file + checksum | COMPLETE | run-specific dump hash; `payload_canonical_sha256` is comparable |
| Restore **verification** | COMPLETE | mismatch raises; live seq untouched |
| Restore **apply** | COMPLETE isolated SQLite | live store refused; PostgreSQL BLOCKED |
| Integrity hash chain | COMPLETE | compromised → no rewrite |
| Venue-vs-ledger drift suite | PARTIAL | tamper + corrupt backup; not venue drift |
| `backup_schedules` table | PARTIAL | DDL v2 exists; not written by API |
| `production_durable` | **BLOCKED** | validator raises |

## Scoreboard

| Block | Status |
|---|---|
| A Domain models | PARTIAL |
| B Write side | PARTIAL |
| C Reliability | PARTIAL |
| D Recovery | PARTIAL (monotonic checkpoint hardened this recon) |
| E Reconciliation | PARTIAL |
| F Named projections | COMPLETE as read models (not canonical) |
| G Data API | COMPLETE with encapsulation caveats |
| H Storage | PARTIAL (SQLite isolated restore-apply COMPLETE; PostgreSQL BLOCKED) |

**Blocked module-wide:** production durability, MT5/broker commands, live/demo/paper trading readiness.

The system is NOT ready for live trading, demo trading, paper trading, or production.

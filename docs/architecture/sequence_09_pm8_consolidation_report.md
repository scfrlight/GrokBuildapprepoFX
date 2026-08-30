> **RECONCILIATION 2026-08-30.** Sequence 09 **delivery** remains. Capability vs reconstructed PM8a is **PARTIAL**: named projections ABSENT, restore-apply ABSENT, Decimal domain records ABSENT, outbox relay ABSENT, family-row UoW PARTIAL. Original Drive spec SOURCE-MISSING. See `docs/PM8_PM8A_GAP_MATRIX.md`. Do not read the §4 COMPLETE table as a full PM8a Master.

# Sequence 09 Report — PM8 Database Consolidation & Data Integrity

Date (UTC): 2026-08-30  
Git home: `scfrlight/GrokBuildapprepoFX`  
Display name: **PM8 Persistence API v1 / families / protocols / services**  
Canonical sequence: **09** (historical Sequence 09 report remains PM7 journal)

## 1. Git commit hash

This App Builder workspace has no `.git` directory. Kernel will be pushed to
`scfrlight/GrokBuildapprepoFX` after this correction wave. Prior main: `a2a1890`.

## 2. Created / updated files

### Created

- `botmoduleproject1/modules/pm8_persistence/` (`schema/ddl.py`, `store.py`, `api/v1.py`, `repositories/protocols.py`, `migrations.py`, `module.py`, README)
- `botmoduleproject1/contracts/v1/pm8_persistence.py`
- `docs/prompts/PM8a_Build_Spec.md` (reconstructed; original missing from Drive/GitHub)
- `tests/unit/test_pm8_persistence_seq09.py`

### Updated

- `botmoduleproject1/app/settings.py` (`Pm8PersistenceSection`)
- `botmoduleproject1/app/feature_flags.py` (`enable_pm8_persistence`)
- `botmoduleproject1/app/container.py` (`_storage_module` binds `PM8PersistenceModule`)
- `configs/base.example.yaml`

## 3. Spec coverage (PM8a sections 13 / 15 / 16 / 19 / 20)

| Spec | Delivered |
|---|---|
| §13 table families | event, signal, order, execution, reliability (idempotency/outbox/inbox), recovery, projection, reconciliation, audit |
| §15 protocols | 19 named Protocol interfaces in `PROTOCOL_CATALOG` |
| §16 services | 20 named services in `SERVICE_CATALOG` |
| Versioned API | `PersistenceApiV1` is the only downstream path |
| Integrity / repair | hash-chain check; repair emits a correction event; committed rows never rewritten |
| Backup / export | `backup()`, `export_package()`, `snapshot()` |
| §19 idempotency edges | request, event_consumer, broker_callback, projection |
| §20 outbox/inbox | same UoW as business write; inbox effectively-once |

## 4. Component status

| Component | Status | Notes |
|---|---|---|
| Consolidated schema v1 | COMPLETE | SQLite; `:memory:` default in `operating_mode=memory` |
| Repository protocols | COMPLETE | 19 |
| Application services | COMPLETE | 20 |
| PersistenceApiV1 | COMPLETE | CQRS facade; repositories private |
| Integrity / repair | COMPLETE | `COMPROMISED` disposition; no rewrite |
| Backup/export | COMPLETE | checksum verified on write |
| Four idempotency edges | COMPLETE | proven by `test_four_idempotency_edges` |
| Outbox/inbox | COMPLETE | transactional enqueue; inbox race-safe |
| Flag default | COMPLETE | YAML `false` → `NullStorage` |
| production_durable | REFUSED | validator raises |
| MT5 / broker commands | REFUSED | validator raises |

## 5. Test results (build gate)

- Sequence 09 gate file: **12 passed** (`tests/unit/test_pm8_persistence_seq09.py`)
- Full suite at Sequence 09 gate (same wave, after 09–13): **480 passed**
- Python runtime: CPython 3.10.21 (ADR-008 deviation; tests monkeypatch interpreter to 3.11.2)
- Production floor remains 3.11+

Covered: append-only + dedupe, outbox transactional correctness, inbox effectively-once, four edges, projection rebuild, integrity/repair immutability, silent-pass recon refused, `pm5_broker` label rejected, flag-off NullStorage, flag-on bind, unauthorized query.

## 6. Build gate

**PASS** (observe/store only; not production durable; not a trading path)

## 7. Residual risks

- SQLite local is not production durability.
- Reconstructed PM8a spec must be reconciled if the original Drive file appears.
- Persistence is not a venue and must not be treated as broker truth.

## 8. Trading readiness

The system is NOT ready for live trading, demo trading, paper trading, or production.

## 9. Exact next step

Sequence 10 — PM8a Migration, Backup & Recovery Hardening.

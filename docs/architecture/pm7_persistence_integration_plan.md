# PM7 Persistence — Integration Plan (Sequence 09)

Status: **Accepted before implementation**  
Date (UTC): 2026-08-28  
Package: `botmoduleproject1/modules/pm7_persistence/`  
Registry name: `pm7_ledger` (Sequence 00 stub name, preserved)  
Feature flags (YAML false; test/research env opt-in):
- `enable_pm7_persistence` (`feature_flags.pm7_persistence`) — master bind
- `enable_pm7_journal` (`feature_flags.pm7_journal`)
- `enable_pm7_replay` (`feature_flags.pm7_replay`)
- `enable_pm7_integrity` (`feature_flags.pm7_integrity`)
- `enable_pm7_retention` (`feature_flags.pm7_retention`)
- `enable_pm7_reporting` (`feature_flags.pm7_reporting`)

This plan is the pre-implementation gate required by Sequence 09. PM7 is the
**canonical append-only journal / evidence / replay / integrity** layer. It is
not a strategy engine, not a risk sizer, not an OMS/EMS, not a broker, and not
PM6 surveillance.

Default bind remains `NullLedger` when the master flag is off. `NullStorage`
(`pm8_persistence`) is unchanged: PM8 is still the future sole durable API.

---

## 1. Position in the pipeline

```text
PM2 RankedCandidate
  → PM3-Strategy Engine TradeIntent
    → PM3 forecasting / QRF ForecastOutput
      → PM4 RiskPublicationBundle
        → PM5 ExecutionPublicationBundle   (simulation / shadow; no venue)
          → PM6 OperationalTruthBundle     (observe-only; non-durable)
            → PM7 PersistencePublicationBundle  (this module)
              → future PM8 persistence API
                → future PM9 operator UX
```

Hard cuts:

- PM4 remains the only risk authorizer. PM7 never issues ALLOW or sizes risk.
- PM5 remains the only execution authority. PM7 never submits, cancels, or
  mutates OMS state.
- PM6 remains the only incident/surveillance engine. PM7 stores what PM6
  already classified; it does not re-detect.
- `SIM-*` is `pm5_simulation`. Never labelled `pm5_broker`.
- Reconciliation without a venue stays `degraded` / `unavailable`. Never a
  silent pass, even when persisted.
- Committed journal entries are immutable. Corrections are new events.
- `production_durable` is future-controlled and refused in Sequence 09.
- No Telegram. No MT5. No live. No secrets in journal/export.

---

## 2. Canonical journal ownership

PM7 owns the **canonical event stream** for PM2–PM6 facts that have already
been published. Existing `contracts/v1/journal.py::JournalEntry` remains the
PM1 identity envelope used by placeholders (`NullStorage.append`,
`NullMonitoring.observe`). Sequence 09 adds `contracts/v1/persistence.py` for
ledger, evidence, replay, snapshot, integrity, retention, query, export, and
recovery types. PM7 does not replace PM4/PM5/PM6 contracts.

Ingestion is one-way:

```text
PM4/PM5/PM6 publication  →  EventIngestionGateway
                           →  validate / classify truth / idempotency
                           →  JournalWriter.append  (hash-chained)
                           →  side stores (recon / evidence notes / snapshots)
                           →  PersistencePublicationBundle
```

Downstream consumers (future PM8/PM9) **read** via QueryEngine / ExportPackager.
They never write the canonical stream.

---

## 3. Append-only semantics

1. `append` assigns a monotonic `sequence` and a SHA-256 `content_hash`
   chained to `previous_hash`.
2. A committed record cannot be updated in place. `mutate` raises
   `ImmutableJournalError`.
3. Duplicate `event_id` / `idempotency_key` with identical canonical payload
   → `duplicate_ignored`.
4. Same identity, different payload → `contradiction_recorded` (quarantine +
   integrity warning). Original stays.
5. A correction is a **new** event with `causation_id` = original `event_id`,
   actor, reason, timestamp. Both records remain queryable.
6. Recovery / restore **must not** rewrite hashes. Restore is a metadata
   status plus continuity check.

---

## 4. Durable storage boundary

Explicit modes:

| Mode | Sequence 09 | Notes |
|---|---|---|
| `disabled` | default bind (`NullLedger`) | flag off |
| `memory` | default when flag on | in-memory; lost on process exit |
| `file_backed` | opt-in | JSONL under configured path; not distributed |
| `sqlite_local` | opt-in | local sqlite file; schema versioned; not production |
| `durable_candidate` | allowed as alias of sqlite_local | honesty flag: not production durability |
| `production_durable` | **refused** | future-controlled |

No cloud credentials. No `DATABASE_URL` ambient env. Path comes from prefixed
config (`pm7_persistence.storage_path`). Destructive purge is off by default
and blocked while frozen.

Existing `persistence:` YAML block remains PM8's future DSN reference and
stays `enabled: false`.

---

## 5. Simulation versus broker provenance

`PersistenceTruthSource`:

- `pm2_context` / `pm3_strategy` / `pm3_forecast` / `pm4_risk`
- `pm5_local_oms` / `pm5_simulation` / `pm5_broker`
- `pm6_monitoring` / `operator` / `derived` / `unknown`

Rules:

1. Ticket prefix `SIM-*` → `pm5_simulation`. Mapping to `pm5_broker` is
   reject + `truth_provenance_conflict`.
2. `mt5_used` / `broker_side_effect` on a stored payload is forbidden.
3. Derived reports keep `lineage_refs` to source events and cannot be labelled
   broker fact.
4. Every evidence bundle discloses `truth_source`.

---

## 6. Reconciliation history

PM7 stores PM5 `ReconciliationRecord` values as history. It does not invent
venue truth.

| Incoming | Stored |
|---|---|
| no venue / `broker_truth_available=false` | `degraded` or `unavailable` — never auto-`pass` |
| mismatch / critical | stored as-is; history retained |
| later resolution | **new** record, not an overwrite |

Query by order / session / symbol.

---

## 7. Snapshot / replay flow

1. Snapshot captures journal `sequence`, canonical checksum, schema version.
2. Replay selects an event chain (session / order / incident / symbol /
   strategy / control / recon), reconstructs in order, compares snapshot when
   present, reports divergence.
3. Replay never mutates source history.
4. Invalid event order → `failed` with reason.

---

## 8. Integrity verification

- Canonical JSON serialization (`sort_keys`, UTC ISO-8601).
- SHA-256 per committed record.
- Hash chain: `previous_hash` of genesis is 64 zero hex chars.
- Verification walks the chain; mismatch → `compromised` (visible, not silent).
- Repair is a **correction event**, not a rewrite.
- Export/archive carry checksums.
- Sequence 09 claims **tamper detection**, not tamper-proof storage.

---

## 9. Retention / archive

Tiers: `active` → `warm` → `cold` with journaled transitions.

- `retention_lock` and `legal/audit freeze` block purge.
- Purge without explicit policy is refused.
- Test mode may **simulate** archival without deleting source data
  (`simulate_archive: true` default).
- Archive manifest includes integrity summary.

---

## 10. Query authorization and export security

- Queries require `actor` + `authorized=true`. Missing/false → rejected.
- Limits/pagination always applied (`query_limit` config).
- Results include provenance and access metadata.
- Exports: JSON + Markdown summary + manifest + checksum.
- Secret-shaped keys (`password`, `token`, `secret`, `dsn`, `credential`)
  are stripped.
- No raw sqlite/file handle is exposed to UI.

---

## 11. PM8 / PM9 downstream handoff

Publication: `PersistencePublicationBundle` (`durable` reflects the **mode**,
not a production SLA). `persistence_handoff=pending_pm8` until PM8 exists.

If downstream is offline, PM7 still appends. Publication is fire-and-forget
to an in-process list; no network.

PM8 remains `NullStorage`. PM7 does not take over `pm8_persistence`.

---

## 12. Migration and recovery boundaries

- SQLite schema version is an integer pragma / table `schema_version`.
- No Alembic / Postgres migrations in Sequence 09.
- Recovery is **metadata**: backup reference, stale/unavailable,
  restore_pending, continuity check, verification_failed → requires_review.
- Sequence 09 does not provide an external backup service.

---

## 13. PM1 bind

| Flag | Bind |
|---|---|
| `enable_pm7_persistence` false (YAML default) | `NullLedger` as `pm7_ledger` |
| true (test/research env) | `PM7PersistenceModule` as `pm7_ledger` |

Sub-flags gate replay / integrity walk / retention mutations / reporting.
Core ingest + journal always run when the master flag is on.

Live profile remains hard-blocked. Demo cannot opt-in PM7.

---

## 14. What Sequence 09 will not do

- real MT5 / broker connection
- live / demo / paper execution loop
- Telegram
- production distributed database
- silent historical mutation
- silent purge
- claiming tamper-proof or production durability
- replacing PM4, PM5, or PM6

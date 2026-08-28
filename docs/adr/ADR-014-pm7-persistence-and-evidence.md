# ADR-014: PM7 persistence and evidence

- Status: Accepted
- Date: 2026-08-28
- Sequence: 09
- Supersedes: none (extends ADR-005, ADR-012, ADR-013)

## Context

PM4–PM6 hold in-memory operational truth. Sequence 00 reserved `pm7_ledger`
for durable evidence. Sequence 09 must remember what happened without becoming
a broker, a risk engine, or a silent history rewriter.

## Decision

1. **Canonical journal ownership.** PM7 is the append-only event stream for
   published PM2–PM6 facts. PM8 remains the future sole persistence API
   (`NullStorage` today).
2. **Immutable commits.** Committed records cannot be updated. Corrections are
   new events with `causation_id` pointing at the original.
3. **Truth provenance.** `SIM-*` is `pm5_simulation`. Mapping to `pm5_broker`
   is rejected. Derived reports keep lineage and cannot be labelled broker fact.
4. **Recon honesty.** No venue → store `degraded` / `unavailable`. Never rewrite
   to `pass`.
5. **Integrity is detection.** SHA-256 hash chain. Sequence 09 does not claim
   tamper-proof storage.
6. **Retention freeze.** Legal/audit freeze blocks purge. Test mode simulates
   archival without deleting source data.
7. **Storage modes.** Default `memory` when the flag is on. `file_backed` and
   `sqlite_local` are local candidates. `production_durable` is refused.
8. **Feature flags.** YAML false. Test/research env opt-in. Default bind
   `NullLedger`. Demo cannot opt-in.

## Consequences

- Composition root binds `PM7PersistenceModule` only when
  `enable_pm7_persistence` is on.
- Tests must prove append-only, no silent mutation, SIM/broker split, degraded
  recon, unauthorized query reject, freeze, and no orders/MT5.
- Sequence 10 (PM8 operator control / Telegram) is next. Distributed durability
  remains later.

## Alternatives considered

1. Fold the journal into PM5 — rejected; execution truth is not audit memory.
2. Overwrite records on correction — rejected.
3. Treat sqlite as production durable — rejected.
4. Treat degraded recon as pass once persisted — rejected.

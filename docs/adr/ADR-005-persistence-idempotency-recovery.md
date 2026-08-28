# ADR-005: Persistence, idempotency, recovery and reconciliation principles

- Status: Accepted
- Date: 2026-08-28
- Sequence: 00

## Context

Legacy execution used a JSON ledger and a hash window for duplicates. That is not recoverable after a crash mid-order, nor reconcilable with the broker. PM8/PM8a will own durability; this ADR freezes principles before schema work.

## Decision

- After PM8, **all durable access goes through the persistence API**.
- Writes that can be retried carry `idempotency_key`.
- Outbox/inbox for cross-module effects; no dual-write of "DB + Telegram" without outbox.
- Snapshots + checkpoints for recovery. Incomplete recovery ⇒ safe halt.
- Broker reconciliation is part of PM5 but *records* through PM8.
- CQRS: command writes are append-only facts; read models are projections.

## Consequences

- Sequence 00 creates no schema and no migrations.
- Side-file JSON ledgers are forbidden as the system of record once PM8 lands.
- Tests will use fakes until PM8a schema exists.

## Alternatives considered

1. SQLite files per module — rejected as system of record (allowed only as a future adapter behind the same API).
2. Event-sourcing everything from day one — deferred; append-only facts first.
3. Broker as system of record — rejected (broker can disagree after restart).

## Validation implications

- Recovery tests (PM8a): crash before ack, restart, no duplicate orders.
- Reconciliation tests: broker position ≠ ledger ⇒ halt, not silent "fix".

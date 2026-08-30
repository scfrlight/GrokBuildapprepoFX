# Unit of work

`PersistenceApiV1.in_transaction` is re-entrant. Nested writers share one IMMEDIATE transaction.

Critical persist paths (signal, order, execution, reconciliation) write:

1. append-only event
2. outbox row
3. idempotency key
4. family/business row
5. money record (when present)
6. audit

Failure injection points: `before_mutation`, `before_outbox`, `after_mutation`, `before_audit`, `before_commit`, `after_commit`.

Invariant: a fault before commit rolls back the entire unit. Half-written truth is refused.

# Transaction boundary map (PM8)

All writes go through `PersistenceApiV1.in_transaction` (re-entrant). PostgreSQL `BEGIN` / `COMMIT` / `ROLLBACK` on one connection.

| Flow | Same transaction | After commit |
|---|---|---|
| A Strategy/signal | signal row + event + outbox + idempotency + money + audit | named projection rebuild (explicit) |
| B Order intent | order row + event + outbox + idempotency + money + audit | relay |
| C Execution report | execution row + event + outbox + callback idempotency + optional position | relay |
| D Reconciliation | run/item/action + event + outbox + audit | none |
| E Inbox | unique insert then handler; failure marks retry/DLQ | none |

Fault injection points (`inject_fault`): `before_mutation`, `before_outbox`, `before_audit`, `after_mutation`, `before_commit`, `after_commit`. Expected: rollback, no silent success, retry-safe.

Outbox publish happens **after** commit (relay). Publish failure does not erase the business row; the outbox stays `failed` / `dead-letter`.

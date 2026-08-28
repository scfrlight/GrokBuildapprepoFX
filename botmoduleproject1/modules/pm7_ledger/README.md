# PM7 — trade ledger / evidence

Canonical implementation: `botmoduleproject1/modules/pm7_persistence/`.

This package re-exports `PM7PersistenceModule` so Sequence 00's `pm7_ledger`
registry name stays intact. Durable writes for other modules still go through
the future PM8 persistence API (`NullStorage` today).

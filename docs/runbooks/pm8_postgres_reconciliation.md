# Runbook — PM8 PostgreSQL reconciliation

id: pm8-postgres-reconciliation
owner: persistence
trading_must_halt: true

## Rules

- Unavailable venue cannot PASS.
- Critical mismatch → keep observe-only.
- Compensating records only; no silent UPDATE of history.

## Lifecycle

STARTED → COLLECTING / MISMATCH_FOUND → ACKNOWLEDGED → REMEDIATION_IN_PROGRESS → RESOLVED → CLOSED

Each item stores local_ref, venue_ref, classification, severity, state, actor, payload.

## Operator steps

1. `start_reconciliation_run(venue_available=...)`
2. Add items; never classification=pass without venue.
3. Acknowledge, remediate, resolve, close.
4. Unresolved critical mismatches keep trading_readiness false.

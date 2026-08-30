# ADR-016 Sequence 14 observability

Status: Accepted  
Date: 2026-08-30

## Decision

Observability is a first-class module (`botmoduleproject1.modules.observability`) bound always, with no trading feature flag. Health is multi-dimensional. Trading readiness is forced false for this sequence. Dump checksums of backups remain run-specific (UUIDs/timestamps); payload-canonical hashes are comparable.

## Consequences

- Doctor/observe remain the operator path.
- Logs, metrics, evidence, and exported reports are redacted.
- Sequence 15+ stays blocked until a separate written authorization.

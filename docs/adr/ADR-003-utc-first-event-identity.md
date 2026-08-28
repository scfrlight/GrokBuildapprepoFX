# ADR-003: UTC-first time and event identity policy

- Status: Accepted
- Date: 2026-08-28
- Sequence: 00

## Context

FX sessions, COT timestamps, broker server times, and operator timezones disagree. Naive datetimes and local clocks caused ambiguity in the legacy scanner (`pytz` mixed with implicit local time). Replay and recovery require stable event identity.

## Decision

- All stored and transmitted timestamps are timezone-aware UTC.
- Wire format is ISO-8601 (`2026-08-28T07:51:00Z` or offset form).
- Domain code receives time from `ClockPort`; tests inject a fake clock.
- Inter-module messages include `event_id`, `correlation_id`, `causation_id`, and `idempotency_key` when they represent an action or fact that may be retried.
- UUIDv4 (or ULIDs later) for ids; never broker ticket as the only identity.

## Consequences

- Broker/server times must be converted at the adapter boundary.
- Logs are UTC. UI may render local time but must label it.
- Replay becomes possible once PM7/PM8 exist.

## Alternatives considered

1. Store broker server time as canonical — rejected (broker-specific).
2. Unix epoch integers only — rejected for operator readability; epoch may be an *additional* field later.
3. Naive UTC (tzinfo stripped) — rejected (too easy to mix with local).

## Validation implications

- Contract tests reject naive datetime in envelopes.
- Adapters must fail if they cannot determine timezone of an inbound stamp.

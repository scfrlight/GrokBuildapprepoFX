# ADR-004: Contract-first integration and API versioning

- Status: Accepted
- Date: 2026-08-28
- Sequence: 00

## Context

PM modules will be built in sequence by different prompts/agents. Without frozen contracts, each sequence will invent incompatible TradeIntent shapes. Legacy scanners passed dicts and JSON files with no schema.

## Decision

- Sequence 01 introduces versioned Pydantic (or equivalent) models in `botmoduleproject1/contracts`.
- Public contracts are `v1` and additive until a documented `v2`.
- Modules communicate through contracts/events, not sibling internals.
- Additive fields must have defaults; removals require a major version.
- Operator and Telegram payloads are adapters of the same contracts, not a parallel API.

## Consequences

- Sequence 01 is "boring" on purpose: types, not strategies.
- Breaking changes need an ADR and a dual-read window.
- JSON dumps in tests must validate against schemas.

## Alternatives considered

1. Protobuf immediately — deferred (Python-first, extra toolchain).
2. Unversioned dicts — rejected.
3. GraphQL for operators — rejected for Sequence 00–01.

## Validation implications

- Contract test folder `tests/contract/` is mandatory from Sequence 01.
- CI should fail if a module imports another module's private types.

# ADR-006: Configuration and secrets governance

- Status: Accepted
- Date: 2026-08-28
- Sequence: 00

## Context

FXTGBOT stored Telegram tokens in JSON, later added `.env` overrides, and the example env still contained a real chat user id. App Builder forbids creating a real `.env` in this workspace.

## Decision

- Public config lives in YAML under `configs/*.example.yaml` (and later non-example overlays that still contain no secrets).
- Secrets live only in environment variables or a secret manager. Names are documented in `.env.example` with empty values.
- Source, tests, logs, ADRs, and the architecture console never print secret values.
- Logs may print secret *names* and redacted config snapshots.
- Account identifiers, tokens, passwords, and API keys are secrets.
- Default flags for unbuilt features are `false`.

## Consequences

- `.env` is gitignored and must not be committed.
- The architecture console shows placeholders, not operator credentials.
- CI uses `configs/test.example.yaml` plus dummy env.

## Alternatives considered

1. Encrypt secrets into the repo — rejected (key distribution).
2. Single JSON config with everything — rejected.
3. Docker secrets only — later, not Sequence 00.

## Validation implications

- Grep gate (future) for token-like literals in `botmoduleproject1/`, `docs/`, `configs/`, `tests/`.
- Config loader refuses to start if a secret required by an *enabled* adapter is missing; disabled adapters must not require secrets.

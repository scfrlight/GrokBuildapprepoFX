# ADR-001: Monorepo modular architecture and dependency direction

- Status: Accepted
- Date: 2026-08-28
- Sequence: 00

## Context

Legacy FXTGBOT evolved as versioned monoliths (V1–V7/V8) where scanning, Telegram, execution, ML, and journaling share files and process memory. BotModuleProject1 must be testable, recoverable, and expandable beyond EURUSD without copying that shape.

## Decision

Adopt a single Python monorepo with:

- one import root `botmoduleproject1`
- layer split: domain / application / infrastructure / adapters / contracts / runtime
- one package per PM bounded context under `modules/`
- dependency direction inward to domain and contracts
- composition root as the only binder of adapters

PM3-Strategy Engine and PM3 forecasting remain separate packages.

## Consequences

- Cross-module calls go through versioned contracts and events.
- Adapters are replaceable (fake MT5 in tests, demo MT5 later).
- More files and indirection than a scanner script; this is intended.
- Import linters / layer tests will be required from Sequence 01.

## Alternatives considered

1. Keep evolving `forex_scanner_vN.py` — rejected (untestable coupling).
2. Polyrepo per PM — rejected at this stage (coordination cost, empty repo).
3. Microservices now — rejected (ops burden before a single demo path exists).

## Validation implications

- Sequence 01 contract tests must fail if `adapters.mt5` imports strategy or risk modules.
- Package READMEs state allowed imports.
- CI (future) runs an import-linter or custom layer check.

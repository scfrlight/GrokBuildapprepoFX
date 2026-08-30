# Observability guide

Sequence 14 adds structured logs, a typed metric catalog, multi-dimensional health/readiness, an error taxonomy, and runbooks. It does **not** open a trading path.

## Commands

```text
PYTHONPATH=. python -m botmoduleproject1 observe --profile test --config configs/test.example.yaml --json
PYTHONPATH=. python -m botmoduleproject1 health --profile test --config configs/test.example.yaml
PYTHONPATH=. python -m botmoduleproject1 doctor --profile test --config configs/test.example.yaml
```

`observe`/`health` print an `ObservabilitySnapshot`. `trading_readiness` is false. `accept_trade` is false. `broker_venue` is `unavailable` while MT5 flags stay off.

## What is not observability

Aegis Desk is an operator console over kernel snapshots. It is not a substitute for the contracts in `botmoduleproject1.modules.observability`.

## Secrets

Secret values never belong in logs, metrics labels, evidence, or exported reports. See `redaction.py` and `docs/guides/incident_response.md`.

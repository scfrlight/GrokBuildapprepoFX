# ADR-009 — PM3-Strategy Engine governance

Status: Accepted  
Date (UTC): 2026-08-28  
Sequence: 04

## Context

Sequence 04 adds a strategy operating platform that emits `TradeIntent`. The repository already reserved the short name “PM3” for a **forecasting / QRF** module. Active strategy parameters must not be edited in place. In-memory stores are temporary.

## Decision

1. **Naming.** The module is **PM3-Strategy Engine** (`pm3_strategy_engine`). Forecasting remains `pm3_forecasting`. The short label “PM3” is not used for this engine in code, docs, or reports.

2. **Intent is not an order.** `TradeIntent` is an analytical hypothesis. It has no lot size (`requested_volume` stays `None`). Only a future PM4 `RiskVerdict.status == ALLOW` may unlock PM5. This module must not import execution or MT5.

3. **Immutable active versions.** Active profile versions are frozen. Edits clone a draft, validate, promote, then activate or roll back. No silent activation.

4. **Shadow-first.** Default operating mode is shadow / observe-only. Profile “active” means the branch may vote in the observe pipeline, not that trading is allowed. PM2 `handoff_eligibility=false` yields `NoTradeDecision` when policy requires handoff.

5. **In-memory repositories.** Sequence 04 stores profiles, versions, bindings, and trackers in process memory behind ports. This is not durable persistence (ADR-005). PM8 remains the sole future durable path.

## Consequences

- Downstream Sequence 05 (PM3 forecasting / QRF) enriches intents; it does not replace this engine.
- Replacing in-memory repos later must not change application service signatures.
- Operators must not treat a `TradeIntent` as a broker instruction.

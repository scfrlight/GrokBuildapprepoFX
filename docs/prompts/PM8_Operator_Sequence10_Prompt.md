# BOTMODULEPROJECT1 — SEQUENCE 10
# PM8 Operator Control Plane, Telegram Control Engine
# & Human-in-the-Loop Operations

Source-of-truth for Sequence 10 (persisted from the authorizing next-step
of Sequence 09). External PM8/PM9 master prompts were not available.

Project: BotModuleProject1.
Repository: GrokBuildapprepoFX.

IMPORTANT:
- Integration plan first: `docs/architecture/pm8_operator_integration_plan.md`.
- Do not declare the system ready to trade.
- Do not connect a real Telegram Bot API. Do not send orders. Do not enable live.

## 0. Current state

PM1–PM7 exist. Safety stubs: NullRiskGate DENY, DisabledExecution raises,
NullMonitoring default, NullLedger default, live disabled, no real MT5,
no paper loop. `execution_permitted=false`. SIM-* is simulation truth.

## 1. PM8 role

Human-in-the-loop operations plane: command intake, RBAC, HITL queue,
safe halt request, research studio proposals, operator read models,
command audit, Telegram encode/decode only.

PM8 is NOT a strategy, forecast, risk, OMS, broker, journal, or trading UI.

## 2. Non-negotiable safety rules

Never create/send broker orders. Never skip PM4. Never bind MT5. Never bind
Telegram Bot API. Never auto-rearm. Never auto-promote tuning to live.
Approvals are consent records, not OrderRequests. Secrets never logged.
YAML flags false. Test/research env opt-in. Live hard-blocked.

## 3. Package

`botmoduleproject1/modules/pm8_operator/`. Registry `pm8_operator`.
Compatibility re-export `pm9_operator_ux`. Default bind `NullOperator`.
`pm8_persistence` remains the CQRS stub.

## 4. Flags

enable_pm8_operator, enable_pm8_hitl, enable_pm8_command_audit,
enable_fine_tune_studio. enable_telegram_control is refused in Sequence 10.

## 5. Trading readiness

The system is NOT ready for live trading, demo trading, paper trading, or production.

Exact next step: Sequence 11 — PM9a Strategy Fine-Tune Studio hardening and/or
PM8 persistence CQRS/outbox (still pending), only after operator plane review.

# BOTMODULEPROJECT1 — SEQUENCE 07
# PM5 Execution & Broker Routing Layer
# Institutional Execution Control, OMS/EMS, Broker Truth Reconciliation,
# Independent Emergency Control, Surveillance, Replayable Observability & Reliability

Source-of-truth for Sequence 07 (persisted verbatim from the authorizing prompt).

Project: BotModuleProject1.
Repository: GrokBuildapprepoFX.

IMPORTANT:
- No access to external master prompts.
- This text is the source-of-truth for Sequence 07.
- Integration plan first: `docs/architecture/pm5_execution_integration_plan.md`.
- Do not declare the system ready to trade because an execution framework exists.
- Do not connect a real broker path without separate explicit safety gates.

## 0. Current state

PM1 kernel, PM2, PM3-Strategy Engine, PM3 forecasting/QRF, PM4 Risk Gate exist.
Safety stubs: NullRiskGate DENY, DisabledExecution raises, live disabled, no real MT5,
no paper loop, no Telegram, no durable ledger.
`execution_permitted=false` remains the Sequence 06 invariant.

## 1. PM5 role

PM5 is the execution truth layer / OMS-EMS fabric / broker adapter boundary /
order lifecycle / recon / exposure truth / independent control / surveillance /
quality / replay / reliability.

PM5 is not alpha, strategy, scanner, predictive model, risk allocator, Telegram,
or a monolithic MT5 wrapper.

Pipeline: PM2 → PM3-SE TradeIntent → PM3 ForecastOutput → PM4 RiskPublicationBundle → PM5 → future broker.

## 2. Absolute safety rules

1. Never accept intent from PM2/PM3 bypassing PM4.
2. Reject any request without valid PM4 authorization.
3. Do not change the risk decision.
4. Do not increase quantity above PM4.
5. Do not change direction, stop logic, or risk budget.
6. Do not turn TradeIntent into an execution command without RiskPublicationBundle.
7. If execution_permitted=false, reject broker path; simulation/shadow may record.
8. Real MT5 send disabled by default.
9. Live profile hard-blocked.
10. No hidden auto-enable.
11. No CLI/preview/test-helper/env fallback bypass.
12. No secrets in git/logs/diagnostics.
13. No actual broker send in this Sequence.
14. No working broker order in tests.
15. Do not claim demo/paper/production/live readiness.
16. Lifecycle changes are immutable events.
17. Idempotency on every order/request.
18. Reconciliation before new submission after reconnect.
19. On uncertainty: stop submissions, reconcile, alert, safe mode.
20. Kill-switch independent of normal submit flow.
21. PM5 execution and PM4 risk approval remain different bounded contexts.

## 3–32. Functional requirements

Implemented per the authorizing prompt: intake, OMS state machine, EMS adapters
(Disabled / Simulation / MT5 placeholder), independent control plane, recon,
exposure, surveillance/throttles, quality analytics, replay, reliability,
audit/incidents, publication, PM1 registry, feature flags, config, tests,
documentation, ADR-012.

Execution modes: disabled / shadow / simulation. demo_enabled and live blocked.

Feature flags (all YAML false):
- enable_pm5_execution (dangerous; does not bind MT5)
- enable_pm5_simulation (test/research env opt-in)
- enable_pm5_broker_adapter (refused)
- enable_mt5_demo_execution (refused)
- enable_live_execution (hard-blocked)

Default bind: DisabledExecution.

The system is NOT ready for live trading, demo trading, paper trading, or production.

Exact next step: Sequence 08 — PM6 Post-Trade, Reconciliation, Performance & Research Feedback Layer.

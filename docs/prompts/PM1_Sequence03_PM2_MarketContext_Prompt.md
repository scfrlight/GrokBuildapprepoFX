# BOTMODULEPROJECT1 — SEQUENCE 03
# PM2: Multi-Pair Adaptive Market Context, Regime, Confluence, Ranking & Calibration Engine

Persisted source-of-truth for Sequence 03. Original filename `PM2_Master_Prompt.md` was not found on Drive/GitHub; this is the complete Sequence 03 user prompt as executed on 2026-08-28.

You are the lead architect and implementation-orchestrator of an institutional modular Forex system for MT5 Demo.

Project: BotModuleProject1. Repository: GrokBuildapprepoFX.

IMPORTANT: there is no access to external master-prompt files. The context below is the only source-of-truth for this stage.

## 0. Context of previous stages (Sequence 00–02 — already complete)

Already created and must not be deleted without need:

- Full architecture baseline, dependency graph, runtime modes, ADR-001..008
- PM1 kernel: bootstrap, settings (pydantic-settings, env_prefix=BOTMODULEPROJECT1_), container, runtime, lifecycle (created→config_loaded→validated→preflight_checked→registry_ready→wired→startup_checked→warmed→ready→running/degraded→stopping→stopped→failed), health (STARTUP/READINESS/LIVENESS), registry, contracts, capabilities, diagnostics, logging_config, exceptions, stubs, python_version guard (>=3.11), secrets governance, profiles (demo/test/backtest/research/live), feature_flags, preflight
- Contracts v1 (schema_version 1.0.0): time, identity (EventEnvelope), market (Timeframe, Tick, OhlcvBar, SymbolMetadata), session (SessionContext, RegimeType, RegimeState), signals (SignalEvent, ConfluenceScore), strategy (TradeIntent — PM3-Strategy Engine namespace), forecasting (ForecastOutput — PM3 QRF namespace, separate from strategy), risk (RiskVerdict ALLOW/DENY/HALT), execution (OrderRequest requires risk_verdict_id), journal, alerts, roles, tuning
- RiskGate protocol as exclusive gate; NullRiskGate always DENY; DisabledExecution raises
- Feature flag `enable_pm2_market_data` (requires-review, default false) — reserved for this module
- Sequence 02 tests passing
- docs/prompts/PM1_Master_Prompt.md, docs/prompts/PM1_Sequence02_Configuration_Governance_Prompt.md — full previous prompts persisted

## 1. Non-negotiable safety rules (all project stages)

- MT5 Demo only by default; live trading explicitly disabled.
- No trade intent may reach execution without a positive risk verdict.
- No duplicate orders, silent retries, implicit parameter changes, unaudited actions.
- Stale data, broken connection, model invalidity, config error or uncertain state → safe halt / observe-only.
- Any architecture, contract or policy change is reflected first in documentation and tests.
- Do not rewrite code just to pass a test; fix the root cause.
- Secrets never enter git, logs, tests or documentation.
- This module (PM2) does NOT send orders, does NOT size, is NOT an ML/QRF layer.

## 2. Mandatory condition before start (build gate)

Activate feature flag `enable_pm2_market_data` only in test/research via explicit opt-in, as defined in Sequence 02 governance. YAML default must stay false; enable only via env in tests/research config. Record this explicitly in the report.

## 3. PM2 — full specification

Elite-level principal quant architect, senior Python systems engineer, institutional FX algo designer, MT5 integration specialist.

Task: design and implement PM2: Multi-Pair Adaptive Market Context, Regime, Confluence, Ranking & Calibration Engine as the second module of the modular Forex platform.

This is NOT a standalone bot and NOT an isolated signal script. It is an integration-native module, ready to attach to the existing PM1 core and to future downstream modules (PM3-Strategy Engine, PM3 forecasting/QRF, PM4 risk gate).

### Mission

Build an institutional pre-trade intelligence layer that:

- scans the allowed universe of Forex pairs,
- analyses market context on multiple timeframes,
- determines market regime,
- computes multi-factor confluence,
- ranks candidates across pairs,
- suppresses weak, redundant or conflicting situations,
- publishes shortlist, watchlist and suppressed outputs,
- records calibration-ready and attribution-ready telemetry,
- remains fully pair-agnostic,
- does NOT execute trades,
- does NOT duplicate the future QRF/predictive ML module (PM3 forecasting).

PM2 must function as the central market intelligence and candidate qualification engine of the platform.

### 1. Architectural role

PM2 is a pre-trade decision-support and candidate-qualification module.

It sits after the integration core (PM1) and before:

- the future ML/QRF module (PM3 forecasting),
- the risk module (PM4),
- the execution module (PM5),
- the portfolio orchestration layer,
- operator UI/Telegram/monitoring consumers (PM9).

PM2 must NOT:

- place trades,
- generate broker orders,
- perform final position sizing,
- replace the future QRF module,
- own execution routing,
- become a monolith containing future modules.

PM2 MUST:

- scan the market,
- classify regime,
- analyse context,
- perform weighted confluence scoring,
- qualify candidates,
- rank across pairs,
- suppress correlation/exposure redundancy,
- publish structured candidate artifacts,
- keep telemetry, attribution, calibration-ready logging,
- provide integration-safe handoff downstream.

Its outputs are ranked candidate intelligence artifacts, NOT BUY/SELL orders.

### 2. Main pipeline

Universe Scan → Feature Snapshot → Regime Detection → Context Analysis → Weighted Confluence Scoring → Qualification State Machine → Cross-Pair Ranking → Correlation/Exposure Suppression → Structured Publication → Telemetry/Attribution/Calibration Logging

Architecture must be: pair-agnostic, multi-timeframe, regime-first, ranking-oriented, suppression-first, deterministic, explainable, calibration-ready, fully integration-ready.

### 3. Integration with PM1

PM2 must integrate with the existing PM1 core:

- module registry (`app/registry.py`),
- typed contracts/Protocols (extend `contracts/v1/`),
- lifecycle hooks,
- readiness/health reporting (`HealthCheckProvider`),
- configuration injection (profile/settings),
- dependency injection via Container,
- structured logging,
- shared diagnostics,
- event/message publication,
- graceful degradation,
- versioned public interfaces.

PM2 must expose: module metadata, semantic version, declared dependencies, declared capabilities, readiness status, health status, calibration status, feature-set version, operating mode — via the existing ModuleMetadata contract.

Future modules must consume PM2 outputs without changing PM2 public interfaces.

### 4. Design principles

1. Regime first — no candidate is qualified before regime is understood.
2. Confluence is not redundancy — similar features must not duplicate as independent evidence.
3. Weighted scoring instead of fragile hard rules — score composition, penalties, vetoes, thresholds rather than huge binary AND-chains.
4. Ranking instead of pure classification — relative opportunity quality matters in a multi-pair system.
5. Suppression-first design — the module must excel at rejecting weak opportunities.
6. Deterministic explainability — every output must be reconstructable from inputs and configuration.
7. Calibration-ready telemetry — every published decision artifact must be auditable against realized outcomes later.
8. No leakage / no repaint — strict time alignment, confirmed-bar discipline, no future information.
9. Pair-agnostic design — no hardcoded assumptions about a specific pair.
10. Forward compatibility — future QRF/predictive models must plug in without redesigning PM2.

### 5. Functional decomposition

Implement PM2 as a composition of explicit submodules:

**5.1 Universe Scanner** — iterate configured Forex symbols, load market data on configured timeframes, validate freshness/completeness/alignment, build synchronized symbol snapshots, detect stale/missing/malformed bars, maintain symbol eligibility. Outputs: normalized symbol snapshot, freshness metadata, data quality status.

**5.2 Feature Snapshot Builder** — derive deterministic features from market data, split features into explicit families, create immutable context snapshot objects, preserve timestamp integrity, attach feature provenance metadata. Families: trend/bias, structure, momentum, volatility, session/liquidity, regime auxiliary, correlation/cross-pair, optionally macro overlay.

**5.3 Regime Engine** — hybrid regime detection: deterministic baseline classification, optional probabilistic/latent-state adapter layer, regime confidence score, regime persistence, transition tracking, smoothing/hysteresis, symbol-specific calibration support. Minimum regime classes: trending, ranging, volatile, compression, transitional/unstable, undefined/untradeable. Do NOT reduce regime to bullish/bearish.

**5.4 Directional Bias Engine** — multi-timeframe directional bias via weighted logic (not binary alignment), model directional asymmetry. Outputs: long_bias_score, short_bias_score, net_bias_score.

**5.5 Structure Engine** — structural price behaviour, swing state, HH/HL vs LH/LL abstractions, continuation/break/transition/invalidation states, structure quality score. No repainting.

**5.6 Momentum Engine** — directional pressure, strengthening vs weakening momentum, slope/acceleration/impulse quality, directional momentum scores and stability metrics.

**5.7 Volatility Phase Engine** — classify volatility state: compression, expansion, exhaustion, shock, dead-market. Adaptive tradability metrics. Not raw ATR alone — contextual and relative interpretation.

**5.8 Session & Liquidity Engine** — session context per pair, active sessions, overlap windows, rollover-risk periods, dead zones, tradability by time-of-day, spread/liquidity constraints if available. Session quality separate from directional bias.

**5.9 Confluence Scoring Engine** — combine independent evidence families, apply positive weights, penalties, vetoes, compute score components and final confluence score, output confidence and interpretability metadata. Scoring must: prevent family over-counting, support family caps, conflict penalties, regime-specific profiles, score banding, abstention on weak/unstable evidence quality.

**5.10 Qualification State Machine** — explicit states: neutral, forming, qualified, confirmed, cooldown, suppressed, invalidated, stale. Transitions depend on: score thresholds, persistence, regime compatibility, veto logic, freshness, cooldown rules, context expiry.

**5.11 Ranking Engine (required)** — compare candidates cross-sectionally over the active universe, compute relative opportunity rank, rank stability metrics, build shortlist and watchlist, top-N candidates. Initial implementation may be deterministic, but interfaces must be compatible with future learning-to-rank models (XGBoost/LambdaMART).

**5.12 Correlation/Exposure Suppressor** — identify redundant exposure clusters, model base/quote currency overlap, detect cross-pair dependence and conflict groups, penalize redundant candidates, optionally enforce one-per-cluster logic, publish conflict diagnostics.

**5.13 Publication & Handoff Gateway** — publish immutable structured candidate artifacts, expose shortlist/watchlist/suppressed sets, include diagnostic reasons, timestamp everything, downstream-safe interfaces.

**5.14 Attribution Engine** — deterministically record score-component contributions, identify dominant factor family, log why a candidate passed/failed/suppressed, preserve decision-time context for future review.

**5.15 Calibration & Feedback Layer** — prepare outputs for realized-outcome analysis, score-band tracking, reliability monitoring, degradation detection, ghost/abstain analytics. This layer MUST NOT automatically mutate production weights — diagnostics and recommendations only.

**5.16 Diagnostics & Health Layer** — readiness, liveness, calibration health, feature health, ranking health, regime-engine health, data freshness health, publication health, snapshot quality diagnostics.

### 6. Feature governance standard

Each feature belongs to exactly one family; each family has a max influence cap; highly correlated features cannot all contribute full weight; contributions are normalized; redundant evidence is penalized or capped; all feature families have version metadata. Required families: regime, directional bias, structure, momentum, volatility, session/liquidity, correlation/cross-pair, optionally macro overlay. The system must prevent fake confluence from several features measuring the same underlying condition.

### 7. Scoring standard

Required outputs per candidate: final_confluence_score (0–100), long_score, short_score, directional_edge_gap, regime_score, structure_score, momentum_score, volatility_score, session_score, liquidity_score, correlation_penalty, feature_redundancy_penalty, confidence_score, quality_tier.

Score bands: 0–39 = suppress, 40–59 = watch only, 60–74 = eligible, 75–89 = high quality, 90–100 = top tier.

Design rules: weighted additive logic with penalties and vetoes, regime-specific profiles, directional asymmetry, abstention on high uncertainty, long and short evidence split before merge, avoid collapse into binary pass/fail.

### 8. Ranking standard

Mode A (deterministic baseline): rank by confluence score, confidence, persistence, directional edge gap, session/liquidity quality, correlation-adjusted quality, regime compatibility.

Mode B (future learning-to-rank ready): public interfaces must allow future learning-to-rank models to replace/supplement deterministic ranking without breaking integration. Future ranker must consume: candidate feature vectors, group/query context by scan timestamp, realized ranking labels in future research mode.

### 9. State machine standard

Candidate lifecycle: neutral, forming, qualified, confirmed, cooldown, suppressed, invalidated, stale.

Transitions: neutral→forming, forming→qualified, qualified→confirmed, qualified→suppressed, confirmed→cooldown, confirmed→invalidated, any→stale on context expiry, suppressed→forming only after reset criteria.

Control concepts: confirmed-bar logic, persistence thresholds, cooldown timers, invalidation events, freshness/staleness TTL, duplicate suppression.

### 10. Output contracts

Define typed, stable, immutable-after-publication models (use existing versioned contracts/v1 from PM1, create contracts/v1/pm2.py or a separate namespace):

**CandidateContextSnapshot**: symbol, timestamp, timeframe map, feature-family summary, regime state, regime confidence, session/liquidity state, data-quality status.

**CandidateScoreCard**: long_score, short_score, final_confluence_score, score components, penalties, confidence_score, quality_tier, directional_edge_gap.

**CandidateQualificationState**: state, entered_at, persistence_count, cooldown_until, stale_after, last_transition_reason.

**RankedCandidate**: candidate_id, symbol, timestamp, final_rank, shortlist_rank, scorecard, state, suppression_info, correlation_cluster, handoff_eligibility, trace_id.

**SuppressionRecord**: symbol, timestamp, suppression_reasons, veto_triggers, conflict_group, ghost_tracking_eligibility.

**PublicationBundle**: shortlist, watchlist, suppressed, diagnostics_summary, health_summary, calibration_snapshot.

All models typed, serializable, versioned, immutable after publication. UTC-first time policy and event_id/correlation_id from Sequence 01 identity contract.

### 11. Telemetry, attribution, calibration (required)

Deterministic attribution: score-component vector, dominant factor family, veto reasons, regime at decision time, rank at decision time, suppression/eligibility cause — for every published candidate.

Calibration tracking: enough information for future computation of score-band hit rate, band expectancy, reliability curves, calibration drift, factor family degradation, regime-specific outcome quality.

Ghost/abstain analytics: tracking of suppressed, rejected, watchlisted-but-not-promoted, expired-before-confirmation candidates — for future analysis of whether suppression saved losses or missed quality opportunities.

Degradation alerts: hooks for alerts on factor-family degradation, regime instability, ranking instability, score-band drift, weak shortlist quality. NO auto-adjust of production weights.

### 12. Compatibility with PM3 (forecasting and Strategy Engine)

PM2 must pass downstream: ranked candidates, context snapshots, score components, regime state and confidence, qualification state, persistence metadata, correlation cluster, suppression history, deterministic factor vector.

PM2 must NOT pass as decisions: broker actions, final position sizes, execution instructions.

Future PM3 forecasting will add: return-distribution estimation, uncertainty quantiles, conditional expectancy, predictive probability calibration, QRF/RF inference — PM2 stays strictly upstream and does not duplicate those duties. Future PM3-Strategy Engine will consume RankedCandidate and CandidateContextSnapshot as part of its MarketContext/FeatureSnapshot input contract.

### 13. Compatibility with PM4/PM5

To the future risk module (PM4) PM2 exposes: shortlist rank, quality tier, regime compatibility, confidence score, correlation cluster, exposure-conflict info, freshness metadata.

To the future execution module (PM5) PM2 exposes: handoff eligibility, confirmation state, context expiry, directional side bias, timing validity window.

PM2 never routes orders directly.

### 14. Non-functional requirements

Implementation must be: modular, typed, deterministic, configuration-driven, explicitly interfaced, testable, auditable, observable, production-grade, ready for downstream MT5-compatible orchestration. Do NOT create a monolithic file or god-class.

### 15. Folder structure

Create a professional modular structure inside botmoduleproject1/modules/pm2_market_context/ (use the existing Sequence 00 placeholder, do not duplicate):

```
botmoduleproject1/modules/pm2_market_context/
  __init__.py
  module.py
  metadata.py
  contracts.py
  capabilities.py
  config/{schema.py, defaults.py}
  domain/{enums.py, ids.py, policies.py}
  models/{snapshots.py, scorecards.py, states.py, publications.py, diagnostics.py}
  scanner/{universe_scanner.py, synchronization.py, freshness.py}
  features/{builder.py, provenance.py, governance.py, normalization.py}
  regime/{regime_engine.py, baseline_rules.py, persistence.py, transitions.py, hmm_adapter.py, gmm_adapter.py}
  engines/{bias_engine.py, structure_engine.py, momentum_engine.py, volatility_engine.py, session_liquidity_engine.py, correlation_engine.py}
  scoring/{weights.py, penalties.py, vetoes.py, confluence_engine.py, confidence.py}
  qualification/{state_machine.py, persistence_rules.py, cooldowns.py, expiry.py}
  ranking/{deterministic_ranker.py, ltr_interface.py, shortlist_builder.py}
  suppression/{conflict_suppressor.py, redundancy_penalties.py, policies.py}
  publication/{publisher.py, handoff_gateway.py}
  telemetry/{attribution.py, calibration.py, ghost_tracking.py, degradation.py, metrics.py}
  diagnostics/{health.py, readiness.py, quality_checks.py}
```

Tests stay at repo-root `tests/` per project convention.

### 16. Public contracts

Create typed Protocol interfaces for: UniverseScanner, FeatureBuilder, RegimeEngine, ContextEngine, ConfluenceScorer, QualificationStateMachine, CandidateRanker, CorrelationSuppressor, PublicationGateway, AttributionRecorder, CalibrationTracker, HealthContributor, PM2Module. Interfaces must be stable, versioned where appropriate, integration-friendly, and registered in the PM1 Registry with ModuleMetadata (capabilities: market_data, regime_detection).

### 17. Configuration

Strictly configuration-driven. Config must support: symbol universe, active timeframes, feature-family toggles, score weights, family caps, penalties, veto policies, regime parameters, persistence windows, cooldown durations, ranking mode, correlation policies, publication thresholds, telemetry toggles, ghost-tracking policies, diagnostics verbosity, operating modes (shadow/paper/active-intelligence). Create configs/pm2.example.yaml, integrated with the existing profile system (demo/test/backtest/research must have different allowed pm2 configurations). Validation is strict, fail-fast on invalid configuration.

### 18. Readiness and health

PM2 exposes: startup readiness, runtime health, data freshness health, feature pipeline health, regime-engine health, ranking-engine health, publication health, calibration telemetry health — via the existing PM1 HealthCheckProvider. Degraded modes: no publication if data freshness fails; ranking degrade if correlation data unavailable; watchlist-only mode if calibration health is poor.

### 19. Testing (required)

Unit tests for each engine; contract tests for public interfaces; state-machine transition tests; no-lookahead tests; deterministic reproducibility tests; config validation tests; score decomposition tests; suppression logic tests; ranking consistency tests; telemetry attribution tests; ghost tracking tests; integration tests with PM1 core contracts; future-facing schema compatibility tests for PM3 handoff.

Critical anti-bias tests: no future leakage, no repainting, synchronized multi-timeframe alignment, no duplicate candidate publication, correct stale/expiry handling, correct regime persistence handling.

### 20. Forbidden on Sequence 03

Do not implement: PM3-Strategy Engine strategy logic, QRF/ML models, risk calculations/sizing, order sending, real MT5 live connection (placeholder/mock market data adapter generating synthetic OHLCV for tests is allowed), Telegram bot, full database schema/migrations, production deployment, any form of live trading.

For tests and development use a mock/synthetic market data adapter instead of the real MT5 API — real MT5 integration arrives with PM5 (execution) later.

## 4. Traceability requirement

Persist the full text of this prompt in `docs/prompts/PM1_Sequence03_PM2_MarketContext_Prompt.md`.

Update `docs/architecture/repository_assessment.md`, adding a "Sequence 03 inputs" section.

## 5. Mandatory final report

1. Created/updated files: full list with paths.
2. Feature flag activation status: confirmation that `enable_pm2_market_data` is enabled only in test/research.
3. PM2 submodules status: table of all 16 functional submodules (5.1–5.16) → COMPLETE/PARTIAL/BLOCKED.
4. Output contracts status: list of created typed models.
5. Test results: how many tests, whether all pass, breakdown by file.
6. Known risks and conflicts.
7. Build gate result: PASS / BLOCKED / NEEDS-DECISION.
8. Explicit statement that the system is NOT ready for trading, demo trading or production.
9. Exact next step: Sequence 04 — PM3 Signal Engine & Confluence Layer / PM3-Strategy Engine Orchestration.

Start by studying the existing placeholder directory modules/pm2_market_context/, then proceed to full PM2 implementation.

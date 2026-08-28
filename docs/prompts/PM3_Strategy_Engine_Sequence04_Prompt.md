# BOTMODULEPROJECT1 — SEQUENCE 04
# PM3-Strategy Engine: Strategy Operating Platform, Consensus & TradeIntent

Persisted source-of-truth for Sequence 04. Original filename `PM3_Strategy_Engine_Master_Prompt.md` was not found on Drive/GitHub; this is the complete Sequence 04 user prompt as executed on 2026-08-28.

You are a senior institutional-level Forex algorithmic trading systems architect and Python engineer.

Project: BotModuleProject1.
Repository: GrokBuildapprepoFX.

IMPORTANT: there is no access to files from Perplexity Spaces or external master prompts. The context below is the only source-of-truth for this stage. Read it fully before any changes.

==================================================
0. CRITICAL NAMING RULE
==================================================

The module name must be strictly:

PM3-Strategy Engine

Never shorten it to “PM3”:
- in code comments;
- in documentation;
- in class names;
- in variable names;
- in architecture notes;
- in the final report.

Reason: “PM3” is already used in the project as the name of a separate future forecasting/QRF module. Always distinguish explicitly:

1. PM3-Strategy Engine
   - strategies;
   - strategy profiles;
   - symbol pipes;
   - consensus;
   - TradeIntent;
   - strategy health;
   - tuning/version lifecycle.

2. PM3 forecasting/QRF
   - future predictive forecasting;
   - QRF;
   - uncertainty;
   - quantiles;
   - model calibration.
   - NOT implemented in this stage.

==================================================
1. PROJECT STATE BEFORE START
==================================================

Already exists and must not be deleted, rewritten from scratch, or weakened without need:

- Architecture baseline, dependency graph, runtime policy, ADR-001…ADR-008.
- PM1 integration kernel: bootstrap; pydantic-settings; dependency container; lifecycle state machine; module registry; capability model; health system; diagnostics; structured logging; CLI; fail-fast Python 3.11+ guard; profile system; secrets governance; feature flags; preflight checks.
- Profiles: demo, test, backtest, research, live.
- Profile live is recognized but hard-blocked; runtime cannot enter running with live profile.
- Settings env prefix: BOTMODULEPROJECT1_.
- Unprefixed environment variables (for example DATABASE_URL, TRADING_MODE) are ignored.
- Default safety posture: trading mode demo; live trading disabled; feature flags disabled; dangerous flags allowed only through explicit env opt-in; no secrets in git/logs/diagnostics.
- Versioned domain contracts v1: time, identity, market, session, signals, strategy, forecasting, risk, execution, journal, alerts, roles, tuning.
- PM2 Market Context Engine already implemented: universe scanning; synthetic confirmed-bar data only; feature snapshots; regime classification; confluence scoring; qualification state machine; ranking; correlation/exposure suppression; immutable publication bundles; attribution, ghost tracking, calibration-ready telemetry; shadow mode by default; handoff_eligibility=false by default.
- PM2 does NOT trade, does NOT create orders, and does NOT guarantee a trading edge.
- NullRiskGate always DENY.
- DisabledExecution always raises.
- Real MT5 connection, order routing, position sizing, database migrations, QRF/ML and Telegram bot are not yet implemented.
- Python baseline: 3.11+; sandbox may run tests on 3.10, documented in ADR-008. Do not weaken `requires-python >=3.11`.

==================================================
2. NON-NEGOTIABLE SAFETY RULES
==================================================

1. Only MT5 Demo is the future target trading venue.
2. Live trading remains disabled without exceptions.
3. No TradeIntent may become a broker order directly.
4. Any possible future path must be:
   PM2 context → PM3-Strategy Engine TradeIntent
   → PM3 forecasting/QRF enrichment
   → PM4 RiskVerdict ALLOW
   → PM5 Execution.
5. PM3-Strategy Engine has no right to bypass the PM4 Risk Gate.
6. PM3-Strategy Engine has no right to import or call MT5 execution internals.
7. PM3-Strategy Engine has no right to do lot sizing, portfolio heat, exposure limits, stop-risk validation, or risk approval.
8. PM3-Strategy Engine has no right to contain Telegram handlers/UI.
9. On stale data, incomplete context, untradeable regime, missing profile, invalid version, conflicting consensus, profile health degradation, or uncertain state — fail closed: return NoTradeDecision, suppress intent, or enter observe-only/degraded mode.
10. No silent fallback, unaudited parametric changes, or implicit activation.
11. Neither an active profile nor an active version is ever edited in place.
12. Any change of configuration, profile version, binding, activation, or rollback must be traceable and prepared for the journal/audit contract.
13. Do not claim trade readiness, demo readiness, paper readiness, production readiness, or a profitable edge.

==================================================
3. BUILD GATE BEFORE IMPLEMENTATION
==================================================

Before implementation:

1. Study the existing repository structure.
2. Find placeholder package `botmoduleproject1/modules/pm3_strategy_engine/` or create it only if it does not exist.
3. Study existing contracts (`strategy.py`, `pm2.py`, `session.py`, `risk.py`, `execution.py`, `tuning.py`), PM1 registry/container/health/lifecycle/settings, and PM2 public output contracts.
4. Do not create duplicate incompatible models. If a contract already exists, extend it backward-compatibly or create a clear adapter.
5. Before implementation add `docs/architecture/pm3_strategy_engine_integration_plan.md`.

The document must explicitly show:

- inputs from PM2;
- outputs to future PM3 forecasting/QRF and PM4 risk;
- prohibition of a direct path to PM5 execution;
- dependency directions;
- ownership of each contract;
- how naming collision is prevented;
- event flow;
- safe degraded behaviours.

Do not start implementation until the plan is created.

==================================================
4. CORE MISSION
==================================================

Build PM3-Strategy Engine as a headless, modular, event-driven, integration-ready strategic domain module for the larger modular Forex system.

PM3-Strategy Engine is NOT:
- an execution engine;
- a risk manager;
- a Telegram UI;
- a monolithic Expert Advisor;
- one fixed strategy;
- an ML/QRF forecasting module.

PM3-Strategy Engine IS:
- a modular strategy operating platform;
- a replaceable strategy domain;
- a symbol-aware strategic decision engine;
- a calibrated weighted consensus builder;
- a TradeIntent generator;
- a tracker/health-aware strategy governance layer;
- a backend domain ready for a future PM9 Telegram control plane;
- a downstream consumer of PM2 context/ranking outputs;
- an upstream producer for future forecasting/QRF and the risk gate.

==================================================
5. HIGH-LEVEL OBJECTIVES
==================================================

PM3-Strategy Engine must:

1. Support several Forex technical-analysis strategy families.
2. Allow replacing strategies without editing Python code.
3. Support several currency pairs through symbol-aware pipelines.
4. Use a standardized StrategyVote and a single TradeIntent contract.
5. Build symbol-level consensus through calibrated weighted ensemble logic.
6. Be ready for a Bayesian upgrade later, but not depend on it in v1.
7. Support user-friendly parameter tuning through schemas/presets/versions, not code edits.
8. Keep tracker, health, and degradation monitoring for each strategy profile/version.
9. Integrate safely into the PM1–PM7 architecture.
10. Expose clean application services for future PM9/TG1 without depending on UI internals.
11. Remain headless and UI-agnostic.
12. Create real code, tests, and architectural boundaries — not only a concept.

==================================================
6. STRATEGY FAMILIES
==================================================

Implement a common replaceable template architecture for the following strategy families:

First active phase:
1. Trend Pullback / Continuation.
2. ORB / Session Breakout.
3. Mean Reversion.

Second phase — implement as disabled-by-default, but working replaceable templates:
4. Liquidity Sweep Reversal.
5. Volatility Squeeze Breakout.

Requirements:

- Each family is a separate strategy template class implementing common `IStrategyTemplate`.
- All strategy templates must be deterministic and accept only standardized context.
- They must not receive data directly from MT5, PM2 internals, Telegram, or a database.
- They must not create broker orders.
- They may return only StrategyVote or abstain/no-vote.
- Do not create fake “returns”; strategies are rule-based technical templates, not validated alpha.
- For the first phase implement real deterministic logic based on existing PM2 feature/context contracts.
- For second-phase templates implement functional conservative logic, but default disabled and without claiming production readiness.

==================================================
7. STRATEGY MODULARITY
==================================================

The user must later replace strategy templates, profiles, profile versions, and symbol bindings without editing code.

Implement:

- template registry;
- profile registry;
- profile version registry;
- symbol binding registry;
- activation service;
- rollback service;
- immutable active-version policy;
- replace active binding service;
- version history query service.

Future PM9 must be able to:

- list available strategies;
- list active strategies on a symbol;
- replace the active strategy;
- switch presets;
- activate a profile version;
- roll back to a stable version.

In Sequence 04 do not create Telegram transport/UI. Create only headless services and stable payloads for a future consumer.

==================================================
8. MULTI-PAIR PIPE ARCHITECTURE
==================================================

Implement:

A. `GlobalSystemPipe`
- account-level strategic context handoff;
- portfolio context handoff;
- cross-symbol coordination hooks;
- system-level flags;
- hooks to global orchestration.
- Do not implement account/risk decisions: only typed pass-through context and safe guards.

B. `SymbolPipe` for each symbol
- symbol-specific market event handling;
- local state update;
- consumption of PM2 CandidateContextSnapshot / RankedCandidate / PublicationBundle;
- active symbol-bound strategy branch loading;
- template evaluation;
- calibrated votes;
- symbol-level consensus;
- TradeIntent or NoTradeDecision.

C. Strategy branches inside each SymbolPipe
- maximum 3 active strategy branches per symbol in the first phase;
- logical branches, not separate isolated applications;
- binding validation must reject more than 3 active branches.

D. `FeedbackPipe`
- accepts future fills/execution outcomes/slippage/spread damage/risk veto/realized R/live-vs-intent drift feedback;
- while execution/persistence do not exist, accept typed synthetic feedback events and update in-memory tracker state;
- do not call MT5 and do not create a DB;
- design must allow replacing the in-memory repository with a PM7/PM8 persistence adapter later.

If N symbols:
- 1 GlobalSystemPipe;
- N SymbolPipes;
- 1 FeedbackPipe;
- up to 3N active strategy branches.

==================================================
9. EVENT FLOW
==================================================

Mandatory per-symbol lifecycle:

1. SymbolPipe receives a confirmed market/context event from PM2.
2. SymbolState is updated.
3. FeatureSnapshot and RegimeState are extracted from standardized PM2 outputs.
4. Active symbol-bound strategy branches are loaded.
5. Each template evaluates context.
6. Each template returns StrategyVote or abstain.
7. Votes are calibrated.
8. ConsensusService builds SymbolConsensusResult.
9. IntentService creates TradeIntent or NoTradeDecision.
10. Output is published through an adapter/port only as a domain artifact.
11. FeedbackPipe later updates tracker and health.

No-lookahead:
- use only confirmed bars/context whose timestamp is not later than event time;
- reject future-dated features/bars;
- test this invariant;
- do not allow repainting.

==================================================
10. INPUT CONTRACTS
==================================================

PM3-Strategy Engine consumes only standardized contracts/adapters:

- MarketContext;
- FeatureSnapshot;
- RegimeState;
- SymbolState;
- SessionContext;
- PortfolioContext;
- RiskContext;
- ExecutionContext;
- SystemFlags;
- PM2 CandidateContextSnapshot;
- PM2 CandidateScoreCard;
- PM2 CandidateQualificationState;
- PM2 RankedCandidate;
- PM2 PublicationBundle.

Important:

- Do not reach into PM2 private/internal classes.
- Create an explicit PM2-to-Strategy context adapter.
- PortfolioContext/RiskContext/ExecutionContext may be read-only placeholders until PM4/PM5.
- Presence of RiskContext must not become risk approval.
- If PM2 handoff_eligibility=false, SymbolPipe may perform shadow evaluation for diagnostics, but must create `NoTradeDecision` / `observe-only` result, not a trading TradeIntent, if policy requires handoff eligibility.

==================================================
11. OUTPUT CONTRACTS
==================================================

Standardized outputs:

- StrategyVote;
- SymbolConsensusResult;
- TradeIntent;
- NoTradeDecision;
- ProfileHealthSnapshot;
- StrategyDiagnostics;
- ValidationReport;
- ConfigChangePreview;
- TrackerSnapshot;
- strategy lifecycle event payloads.

TradeIntent is the primary downstream strategic output, but not an order.

If existing `contracts/v1/strategy.py` already contains TradeIntent/ExitPlan/Direction/EntryType/ConsensusDecision/NoTradeDecision:
- do not duplicate them;
- extend with backward-compatible fields;
- ensure adapter compatibility;
- keep `schema_version = 1.0.0` or create a strictly versioned extension without breaking changes.

==================================================
12. TRADEINTENT CONTRACT
==================================================

TradeIntent must contain at least:

- intent_id;
- event_id;
- correlation_id;
- causation_id;
- idempotency_key;
- symbol;
- profile_id;
- version_id;
- direction;
- entry_type;
- entry_zone_low;
- entry_zone_high;
- confidence_score;
- setup_quality;
- consensus_score;
- regime_state;
- urgency_class;
- signal_expiry;
- exit_plan;
- diagnostics;
- source_candidate_id;
- pm2_rank;
- created_at.

ExitPlan must contain:

- stop_type;
- stop_price;
- tp_plan;
- trail_plan;
- time_stop_plan.

Critical constraints:

- TradeIntent has no lot-size field.
- TradeIntent is not an OrderRequest.
- TradeIntent has no permission to send an order.
- No TradeIntent is published as eligible for execution without a future PM4 RiskVerdict ALLOW.
- For any missing/invalid required context create NoTradeDecision.

==================================================
13. CONSENSUS ENGINE
==================================================

Do not use simple majority voting.

Build a calibrated weighted ensemble consensus engine.

Each StrategyVote contains at least:

- strategy_template_type;
- profile_id;
- version_id;
- symbol;
- direction;
- raw_probability;
- calibrated_probability;
- setup_quality;
- regime_fit;
- friction_fit;
- historical_reliability;
- recent_live_health;
- entry_type;
- entry hints;
- diagnostics;
- abstained flag/reason;
- timestamps;
- correlation_id.

Base weight formula:

w_i = 0.35 * H_i + 0.25 * R_i + 0.20 * Q_i + 0.10 * F_i + 0.10 * L_i

Where:
- H_i = historical_reliability;
- R_i = regime_fit;
- Q_i = setup_quality;
- F_i = friction_fit;
- L_i = recent_live_health.

Requirements:

- All weight inputs are normalized to range 0..1.
- Invalid/NaN/out-of-range values are rejected or safely normalized with diagnostics.
- Votes with disabled/degraded profile do not participate in selected votes.
- Compute P_long from long votes.
- Compute P_short from short votes.
- Use configurable thresholds.
- Return one of:
  - GO_LONG;
  - GO_SHORT;
  - WAIT;
  - NO_TRADE.
- Also return:
  - agreement_score;
  - conflict_score;
  - selected_votes;
  - dropped_votes;
  - diagnostics;
  - consensus confidence;
  - abstention reason, if applicable.
- Consensus must be deterministic and unit-testable.
- On close P_long/P_short, strong conflict, or lack of reliable votes — WAIT/NO_TRADE, do not guess direction.

==================================================
14. PROBABILITY CALIBRATION
==================================================

Raw strategy probabilities must not be used directly.

Create a calibration abstraction:

- `ICalibrationPolicy`;
- Platt scaling policy interface;
- isotonic calibration policy interface;
- reliability-table mapping policy;
- deterministic conservative fallback calibration.

For v1 a simple functional reliability-table style calibration is allowed, but:
- raw_probability and calibrated_probability must be separate;
- calibration metadata/version must be in StrategyVote;
- fallback must be explicitly marked in diagnostics;
- absence of validated calibration must not pretend statistical reliability;
- may return NO_TRADE/low-confidence when the required calibration policy is absent.

==================================================
15. BAYESIAN UPGRADE PATH
==================================================

Bayesian logic is not required as the v1 decision engine.

But the architecture must support future replacement/addition for:

- regime probability updating;
- strategy reliability posterior updating;
- small-sample smoothing;
- health-state smoothing.

Create `BayesianUpdatePolicy` / protocol boundary and a disabled/default implementation without heavy ML dependencies. No QRF/RF/ML at this stage.

==================================================
16. REGIME ROUTING
==================================================

Implement regime-aware strategy routing:

- trending regime → Trend Pullback / Continuation, ORB/Breakout;
- ranging regime → Mean Reversion, Liquidity Sweep Reversal;
- transitional/compression regime → ORB/Breakout, Volatility Squeeze Breakout;
- volatile/undefined/untradeable → configurable abstain/no-trade by default.

Requirements:

- RegimeState is consumed explicitly by each template.
- RegimeState participates in consensus weights through regime_fit.
- Binding/profile configuration determines supported regimes.
- An incompatible regime must create an abstain/veto reason, not an artificial vote.

==================================================
17. FINE-TUNING AND PROFILE ARCHITECTURE
==================================================

The user must never edit code to tune strategies.

Implement:

- ParameterSchema;
- StrategyPreset;
- StrategyProfile;
- ProfileVersion;
- StrategyDraft;
- ValidationReport;
- ConfigChangePreview;
- promotion lifecycle;
- rollback lifecycle;
- immutable snapshot/hash for each profile version.

Use/extend existing `contracts/v1/tuning.py` without duplication.

Tuning lifecycle:

active version
→ clone to draft
→ edit
→ validate
→ test
→ promote
→ activate
→ rollback if needed.

Support modes:

- SIMPLE;
- ADVANCED;
- RESEARCH.

ParameterSchema must contain:

- name;
- display_name;
- group;
- type;
- default;
- min/max;
- step;
- allowed_values;
- ui_mode;
- description;
- warning_text;
- requires_revalidation.

Validation must include:

- schema/type/range validation;
- regime compatibility;
- template compatibility;
- max 3 branches per symbol;
- no duplicate active template/profile binding;
- profile status compatibility;
- immutable active version protection;
- configuration fingerprint/hash;
- no unsafe implicit activation.

==================================================
18. VERSION LIFECYCLE
==================================================

Profile/version statuses:

- draft;
- validated;
- backtest_candidate;
- tested;
- paper;
- demo_candidate;
- active;
- watchlist;
- degraded;
- disabled;
- retired.

Requirements:

- An active version cannot be edited in place.
- Only a validated/tested/demo_candidate version may claim activation, according to policy.
- At this stage activation means only strategic activation in the shadow/observe-only pipeline, NOT trading permission.
- Disabled/degraded/retired cannot generate a selected vote.
- Each status change creates a typed audit-ready lifecycle event.
- Rollback must be deterministic, explicit, and preserve the previous active binding/version.

==================================================
19. TRACKERS AND HEALTH
==================================================

For each strategy profile version implement 3 tracker layers.

A. LiveTracker:
- signals_today;
- intents_today;
- trades_today (will be 0 or synthetic feedback only for now);
- realized_r;
- average_spread;
- average_slippage;
- current_state.

B. AnalyticalTracker:
- win_rate;
- expectancy_r;
- profit_factor;
- MAE/MFE;
- max_drawdown_r;
- hold_time_distribution;
- exit_reason_distribution;
- out_of_sample_delta;
- live_vs_backtest_drift.

Until PM5/PM7/PM8 these fields must be null/unknown/insufficient_data, not invented values.

C. HealthTracker:
- health_status;
- degradation_triggers;
- alerts;
- recommended_action;
- last_updated_at.

Health statuses:

- healthy;
- watchlist;
- degraded;
- disabled;
- retired.

Implement `IHealthPolicy` and a conservative default policy:
- absence of sufficient statistics = `watchlist` or `unknown`, not `healthy`;
- critical configuration invalidity = disabled;
- stale/inconsistent feedback = degraded;
- no health state may increase authority or bypass safety controls.

==================================================
20. PM9/TG1 READINESS WITHOUT TELEGRAM
==================================================

PM3-Strategy Engine must be PM9/TG1-ready, but PM9/TG1-independent.

Create headless application services for future requests:

- list_symbols;
- list_available_strategies;
- list_active_strategies_by_symbol;
- get_profile_tracker_snapshot;
- get_profile_health;
- get_version_history;
- get_tuning_schema;
- compare_versions;
- get_bindings;
- get_strategy_diagnostics.

Create headless commands:

- clone_draft;
- update_draft_parameter;
- apply_preset;
- validate_draft;
- run_backtest_hook;
- promote_version;
- activate_version;
- replace_active_strategy_binding;
- rollback_binding.

PM3-Strategy Engine must return:

- compact summary DTOs for chat UI;
- rich schema payloads for a future Telegram WebApp;
- no Telegram imports, handlers, routers, callbacks, or aiogram dependencies.

==================================================
21. PM1–PM7 INTEGRATION
==================================================

Implement:

- module manifest;
- accepted event types;
- produced event types;
- supported queries;
- supported commands;
- capability flags;
- graceful degradation support;
- clean external adapters/ports;
- module registration through existing PM1 Registry;
- health/readiness contributors using PM1 HealthCheckProvider.

PM3-Strategy Engine capabilities must include at least:

- strategy_evaluation;
- strategy_consensus;
- trade_intent_generation;
- profile_governance;
- strategy_health;
- strategy_diagnostics.

Feature flag:
- add `enable_pm3_strategy_engine`;
- safety class `requires-review`;
- default false;
- YAML default false;
- allowed only in test/research through prefixed environment opt-in;
- demo/backtest/live must not automatically create an active trade-capable path;
- even with opt-in there must be no execution capability.

==================================================
22. REQUIRED ENUMS
==================================================

Implement or backward-compatible extend:

- StrategyTemplateType;
- ProfileStatus;
- Direction;
- EntryType;
- ConsensusDecision;
- RegimeType;
- HealthStatus;
- UiMode;
- ParamType;
- StrategyEventType;
- VoteAbstentionReason;
- UrgencyClass;
- StopType;
- ProfileChangeAction.

Do not duplicate existing `Direction`, `EntryType`, `RegimeType` if they already exist in contracts/v1. Use canonical imports/adapters.

==================================================
23. REQUIRED MODELS
==================================================

Implement/extend at least:

- ParameterSchema;
- StrategyPreset;
- StrategyProfile;
- ProfileVersion;
- StrategyDraft;
- SymbolStrategyBinding;
- MarketContext;
- FeatureSnapshot;
- RegimeState adapter/view;
- SymbolState;
- PortfolioContext;
- RiskContext;
- ExecutionContext;
- SystemFlags;
- StrategyVote;
- SymbolConsensusResult;
- ExitPlan;
- TradeIntent;
- NoTradeDecision;
- TrackerSnapshot;
- ProfileHealthSnapshot;
- StrategyDiagnostics;
- ValidationReport;
- ConfigChangePreview;
- StrategyFeedbackEvent;
- ModuleManifest.

All published domain artifacts:
- typed;
- serializable;
- versioned;
- immutable after publication;
- timezone-aware UTC;
- must support correlation/causation/idempotency semantics where applicable.

==================================================
24. REQUIRED PROTOCOLS
==================================================

Implement at least:

- IStrategyTemplate;
- IConsensusPolicy;
- ICalibrationPolicy;
- IBayesianUpdatePolicy;
- IHealthPolicy;
- IVersioningPolicy;
- IProfileRepository;
- IVersionRepository;
- IBindingRepository;
- ITrackerRepository;
- IStrategyEventPublisher;
- IPM2ContextAdapter;
- IStrategyManifestProvider.

In-memory repositories are allowed at this stage, but:
- must be isolated in infrastructure;
- must not leak into domain/application;
- must be easily replaceable by PM7/PM8 persistence repositories later;
- must not present themselves as durable persistence.

==================================================
25. REQUIRED APPLICATION SERVICES
==================================================

Implement at least:

- ProfileService;
- SymbolBindingService;
- DraftService;
- ValidationService;
- CalibrationService;
- ConsensusService;
- IntentService;
- TrackerService;
- HealthService;
- ActivationService;
- RollbackService;
- StrategyControlBridgeService (do not name it TG1BridgeService, so as not to freeze an obsolete UI name);
- StrategyModuleService;
- PM2HandoffService.

==================================================
26. REQUIRED PIPELINE CLASSES
==================================================

Implement:

- GlobalSystemPipe;
- SymbolPipe;
- FeedbackPipe.

SymbolPipe is the main orchestration sequence market/context event → TradeIntent/NoTradeDecision.

Mandatory protective controls of SymbolPipe:

- Checks the feature flag.
- Checks profile status.
- Checks PM2 data quality.
- Checks staleness/expiry.
- Checks PM2 handoff eligibility.
- Checks regime compatibility.
- Checks max active branches.
- Prevents duplicate intent with idempotency key.
- Does not create TradeIntent if consensus is WAIT/NO_TRADE.
- Does not create TradeIntent if global system flags forbid strategy evaluation.
- Does not call the risk engine, execution engine, or MT5.
- Returns detailed diagnostics output for every refusal.

==================================================
27. RECOMMENDED CODE ORGANIZATION
==================================================

Use a professional layered structure inside:

`botmoduleproject1/modules/pm3_strategy_engine/`

Proposed structure:

```text
botmoduleproject1/modules/pm3_strategy_engine/
  __init__.py
  module.py
  manifest.py
  contracts.py
  capabilities.py
  api/
    queries.py
    commands.py
    dto.py
  application/
    profile_service.py
    binding_service.py
    draft_service.py
    validation_service.py
    calibration_service.py
    consensus_service.py
    intent_service.py
    tracker_service.py
    health_service.py
    activation_service.py
    rollback_service.py
    control_bridge_service.py
    pm2_handoff_service.py
  domain/
    enums.py
    entities.py
    value_objects.py
    policies.py
    events.py
    factories.py
  templates/
    base.py
    trend_pullback.py
    orb_session_breakout.py
    mean_reversion.py
    liquidity_sweep_reversal.py
    volatility_squeeze_breakout.py
    registry.py
  consensus/
    weighted_ensemble.py
    calibration.py
    bayesian_adapter.py
    thresholds.py
  pipelines/
    global_system_pipe.py
    symbol_pipe.py
    feedback_pipe.py
  infrastructure/
    repositories/
      in_memory_profiles.py
      in_memory_versions.py
      in_memory_bindings.py
      in_memory_trackers.py
    adapters/
      pm2_context_adapter.py
      event_publisher.py
  config/
    schema.py
    defaults.py
  diagnostics/
    health.py
    readiness.py
    snapshots.py
  tests/
```

The structure may be improved, but:
- do not create god classes;
- do not mix domain, application, infrastructure;
- do not put strategy business logic in CLI;
- do not duplicate contracts/v1;
- do not name the package simply `pm3`; use strictly `pm3_strategy_engine`.

==================================================
28. CONFIGURATION
==================================================

Create:

- `configs/pm3_strategy_engine.example.yaml`;
- profile-aware defaults/extensions for test/research;
- typed Pydantic config schema.

Configuration must contain:

- strategy template registry policy;
- enabled template list;
- active-first-phase vs disabled-second-phase templates;
- symbol universe;
- symbol-specific bindings;
- max active branches per symbol = 3;
- strategy profile definitions;
- profile versions;
- parameter schemas;
- presets;
- consensus thresholds;
- consensus base weights;
- calibration policy selection;
- regime routing policy;
- cooldown/persistence defaults;
- stale context TTL;
- signal expiry defaults;
- profile health thresholds;
- shadow/observe-only operating mode;
- audit/event publishing toggle;
- no-trade policy;
- feedback policy;
- feature flag integration.

Validation requirements:

- weights sum or are normalized appropriately;
- thresholds in [0,1];
- no duplicate binding;
- no more than three active branches per symbol;
- no active profile without version;
- no active version with draft status;
- second-phase templates disabled by default;
- live profile refused;
- no config option can enable order sending;
- no config option can bypass the PM4 risk gate;
- explicit validation errors human-readable.

==================================================
29. TESTING REQUIREMENTS
==================================================

Add real, meaningful tests. Do not fake tests or weaken assertions for a green suite.

Mandatory groups:

1. Strategy templates
2. Consensus (exact base-weight formula; GO_LONG/GO_SHORT/WAIT/NO_TRADE; determinism; calibration before consensus; degraded/disabled dropped)
3. Calibration (raw != calibrated; conservative fallback diagnostics)
4. Profiles/drafts/versions (clone, immutability, validation, promotion, rollback, no implicit activation)
5. Symbol binding (mapping, replacement, duplicate prevention, max three, disabled cannot bind as active)
6. SymbolPipe (PM2 event → TradeIntent in shadow-safe test; handoff_eligibility=false → NoTradeDecision; stale/bad quality; duplicate idempotency; system flag; no PM4/risk/execution calls)
7. FeedbackPipe and trackers
8. PM1/PM2 integration
9. Anti-bias and safety traceability (no look-ahead; confirmed-bar-only; no repainting; no order object; TradeIntent has no lot size)
10. Python 3.11+; if sandbox uses 3.10, do not change the project requirement. State in the final report that a full compliance-run on Python 3.11 is required outside the sandbox.

Add traceability document `docs/architecture/pm3_strategy_engine_test_traceability.md`.

==================================================
30. DOCUMENTATION AND TRACEABILITY
==================================================

Create/update:

1. `docs/prompts/PM3_Strategy_Engine_Sequence04_Prompt.md` — this file.
2. `docs/architecture/sequence_04_report.md`
3. `docs/architecture/pm3_strategy_engine_integration_plan.md`
4. `docs/architecture/pm3_strategy_engine_test_traceability.md`
5. `docs/architecture/repository_assessment.md` — “Sequence 04 inputs”
6. `README.md` — PM3-Strategy Engine creates only analytical TradeIntent/NoTradeDecision; do not declare the system a trading system.
7. ADR-009 `docs/adr/ADR-009-pm3-strategy-engine-governance.md`

==================================================
31. FORBIDDEN ON SEQUENCE 04
==================================================

Do not implement:

- QRF, Random Forest, ML training/inference;
- predictive probability/return distribution forecasting;
- risk sizing;
- portfolio heat;
- drawdown calculations;
- broker routing;
- real MT5 connection;
- broker order creation/sending;
- position management;
- real fills;
- database schema/migrations;
- durable ledger;
- Telegram bot/UI/router/callbacks;
- live trading;
- paper-trading execution;
- real connection to an external market data API.

For tests use synthetic confirmed context from PM2.

==================================================
32. FINAL REPORT FORMAT
==================================================

After completion provide a Markdown report with:

1. Git commit hash.
2. Created / updated files — full path list.
3. Pre-implementation integration-plan status.
4. PM3-Strategy Engine component status table.
5. TradeIntent boundary.
6. Strategy templates.
7. Safety controls.
8. Test results.
9. Known risks and limitations.
10. Build gate: PASS / BLOCKED / NEEDS-HARDENING.
11. Trading readiness sentence: “The system is NOT ready for live trading, demo trading, paper trading, or production.”
12. Exact next step: Sequence 05 — PM3 Forecasting / QRF Research-to-Inference Pipeline.

Start with repository inspection and creation of `pm3_strategy_engine_integration_plan.md`. Then implement PM3-Strategy Engine fully within the bounds of this prompt.

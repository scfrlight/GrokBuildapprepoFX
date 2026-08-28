# Sequence 06 Report — PM4 Risk Gate

Date (UTC): 2026-08-28  
Git home: `scfrlight/GrokBuildapprepoFX`  
Display name: **PM4 Risk Gate** (Adaptive Risk Allocation / Kill-Switch)

## 1. Git commit hash

This App Builder workspace has no `.git` directory. Sequence 06 landed on
`scfrlight/GrokBuildapprepoFX` as `aa8f79eb4f47321fb24edf9a59618c2edd54f2eb`.
Docs follow-up records that hash.

## 2. Created / updated files

### Created

- `botmoduleproject1/modules/pm4_risk_gate/` (config, domain, models, intake,
  budgeting, sizing, heat, concentration, drawdown, controls, kill, governance,
  publication, health, infrastructure, module, capabilities, contracts, manifest)
- `configs/pm4_risk_gate.example.yaml`
- `docs/architecture/pm4_risk_gate_integration_plan.md` (pre-implementation)
- `docs/architecture/pm4_risk_gate_test_traceability.md`
- `docs/adr/ADR-011-pm4-risk-gate-governance.md`
- `docs/prompts/PM4_Risk_Gate_Sequence06_Prompt.md`
- `tests/unit/pm4_support.py`
- `tests/unit/test_pm4_*.py`
- `tests/contract/test_pm4_risk_contracts.py`

### Updated

- `botmoduleproject1/contracts/v1/risk.py` (cards, enums, publication bundle)
- `botmoduleproject1/contracts/v1/__init__.py`
- `botmoduleproject1/app/feature_flags.py`, `settings.py`, `container.py`, `stubs.py`
- `botmoduleproject1/modules/pm4_risk/` (compatibility re-export)
- `configs/base.example.yaml`
- README files, ADR index, architecture baseline, dependency graph,
  repository assessment, pyproject.toml, tests/README.md
- Architecture desk (`src/lib/desk/*`, `src/routes/index.tsx`)

## 3. Pre-implementation integration-plan status

`docs/architecture/pm4_risk_gate_integration_plan.md` written **before** module
implementation. ADR-011 accepted.

Plan covers: exact PM2 / PM3-SE / PM3 forecasting inputs, PM5-bound outputs,
no-bypass, deny-by-default, degraded modes, kill-switch scopes, in-memory
limitation before PM7/PM8, inventory/audit, no direct order creation.

## 4. PM4 component status

| Component | Status (COMPLETE / PARTIAL / BLOCKED) | Notes |
|---|---|---|
| Risk Intake Gateway | COMPLETE | schema, freshness, lookahead, consistency |
| Hierarchical Risk Budgeting | COMPLETE | book → sleeve → regime → cluster → symbol → candidate |
| Risk Admission Control | COMPLETE | approve / reduce / reject / freeze / kill_protected |
| Position Sizing | COMPLETE | stop-distance baseline × quality × uncertainty × dd × liq × corr × heat cap |
| Portfolio Heat | COMPLETE | raw / effective / cluster / directional / residual |
| Correlation / Concentration | COMPLETE | FX overlap, USD block, European basket, one-per-cluster |
| Drawdown Governor | COMPLETE | ladder + throttle factors |
| Pre-Trade Controls | COMPLETE | fat-finger, collar, burst, notional, route recorded closed |
| Kill-Switch | COMPLETE | scoped latch; no auto-rearm; policy recovery |
| Governance / Inventory / Audit | COMPLETE | in-memory; journal events |
| Degraded Modes / Recovery | COMPLETE | normal…kill_protected + close_only / no_new_risk |
| Publication / Handoff | COMPLETE | RiskPublicationBundle; `execution_permitted=false` |
| PM1 integration | COMPLETE | registry name `pm4_risk`; flag-gated bind |
| feature flag | COMPLETE | YAML false; test/research env opt-in |
| config | COMPLETE | pydantic schema; example YAML |
| tests | COMPLETE | 46 added; 235 / 235 passed |
| documentation | COMPLETE | plan, ADR-011, prompt, traceability, this report |

## 5. Risk boundary

PM4 **approves** (ALLOW / REDUCE) only when every hard control is clear and a
positive size survives discounts. It **denies** on missing/stale/invalid
upstream artifacts, heat/concentration/budget breaches, close-only / no-new-risk,
and freeze. It **halts** when the kill-switch latches or drawdown reaches
`kill_protected`.

Output is not an order because:

- no `OrderRequest` is constructed
- `execution_permitted` cannot be true
- PM5 `DisabledExecution.submit` still raises

PM5 is still required to bind a broker route to an ALLOW verdict.

## 6. Safety controls

- deny-by-default
- no direct execution
- stale artifact rejection
- no risk bypass (evaluate without PM2/PM3 DENYs)
- kill-switch latch + scoped block
- drawdown throttle ladder
- heat / concentration enforcement
- no hidden auto-rearm

## 7. Test results

- Collected / passed: **235 / 235**
- Prior Sequences 00–05: 189
- Sequence 06 added: 46
- Sandbox runtime: CPython 3.10.21 with ADR-008 interpreter_version patch
- Project floor remains Python 3.11+; a full compliance-run on 3.11 is required
  outside this sandbox

| File | Tests |
|---|---|
| `tests/contract/test_pm4_risk_contracts.py` | 5 |
| `tests/unit/test_pm4_safety.py` | 10 |
| `tests/unit/test_pm4_intake.py` | 7 |
| `tests/unit/test_pm4_engines.py` | 9 |
| `tests/unit/test_pm4_kill_governance.py` | 8 |
| `tests/unit/test_pm4_integration.py` | 7 |
| prior Sequences 00–05 | 189 |
| **total** | **235** |

## 8. Known risks and limitations

- Synthetic upstream data (PM2/PM3 fixtures and residual envelope)
- No durable persistence yet (in-memory control state)
- No real MT5
- No PM5 execution
- No real broker cancel-on-disconnect (placeholder policy only)
- Feature flag must stay false in YAML
- Runtime still boots DEGRADED when the flag is off (`NullRiskGate` not ready)

## 9. Build gate

**PASS**

## 10. Trading readiness

The system is NOT ready for live trading, demo trading, paper trading, or production.

## 11. Exact next step

Sequence 07 — PM5 Execution & Broker Routing Layer.

# Sequence 11 Report — PM6 MT5 Execution & Exit Engine (Demo-only)

Date (UTC): 2026-08-30  
Git home: `scfrlight/GrokBuildapprepoFX`  
Display name: **Demo MT5 adapter + structural exits**  
Master Orchestration name: **PM6 MT5 Execution & Exit Engine**  
Package home: `adapters/mt5` + `pm5_execution` routing/exit (existing `pm6_post_trade` **not** renamed)

## 1. Git commit hash

Workspace has no `.git`. Prior main: `a2a1890`.

## 2. Created / updated files

### Created

- `botmoduleproject1/adapters/mt5/capabilities.py`
- `botmoduleproject1/adapters/mt5/demo_gateway.py`
- `botmoduleproject1/modules/pm5_execution/demo_routing.py`
- `botmoduleproject1/modules/pm5_execution/exit_engine.py`
- `tests/unit/test_seq11_mt5_exit.py`

### Unchanged (still blocked)

- `botmoduleproject1/modules/pm5_execution/ems/mt5_adapter.py` (`Mt5BrokerAdapter.submit` still raises `ExecutionDisabledError`)

## 3. Dual PM6 naming

Master Orchestration Sequence 11 is titled PM6 MT5 Execution. This repo already used PM6 for post-trade (Sequence 08) and PM5 for OMS/EMS. Packages stay. Sequence 11 content lands in the MT5 adapter + PM5 routing/exit engine.

## 4. Component status

| Component | Status | Notes |
|---|---|---|
| Demo MT5 adapter | COMPLETE | `DemoMt5Gateway`; tickets `DEMO-*`; simulated=True in tests |
| Live account probe | REFUSED | `probe_environment(account_kind="live")` raises |
| Real terminal on Linux | FAIL-CLOSED | `simulated=False` and no terminal → `ExecutionDisabledError` |
| Capability checks | COMPLETE | demo-only |
| Idempotent routing | COMPLETE | same `client_order_id` returns duplicate |
| Duplicate guards | COMPLETE | gateway map + persistence broker_callback edge |
| Bounded retries | COMPLETE | `max_retries`; excess → rejected |
| Reconciliation | COMPLETE | disconnect → `degraded`, `silent_pass=False`; never silent pass |
| Structural SL/TP | COMPLETE | `ExitEngine` |
| Breakeven lock | COMPLETE | +1R moves SL to entry |
| Time stops | COMPLETE | `time_stop_seconds` |
| Exit lifecycle | COMPLETE | armed → breakeven/time_stop/sl/tp → closed |
| Entry must not talk to venue | COMPLETE | `DemoRouter` requires PM4 ALLOW; Sequence 07 placeholder still blocked |
| `python -m botmoduleproject1 live` | FAIL-CLOSED | `LiveTradingDisabledError` |

## 5. Test results (build gate)

- Sequence 11 gate file: **6 passed** (`tests/unit/test_seq11_mt5_exit.py`)
- Full suite: **480 passed**
- Python: CPython 3.10.21 (ADR-008 deviation)

Covered: live probe refused, Sequence 07 placeholder blocked, duplicate + retry + disconnect recon, non-ALLOW cannot reach gateway, SL/TP/BE, live CLI fail-closed.

## 6. Build gate

**PASS** (Demo-only simulated gateway; live remains closed; DEMO-* is not broker truth)

## 7. Residual risks / NEEDS-HARDENING

- No MetaTrader5 package / terminal on this Linux host. Real demo terminal send is **BLOCKED** until a Windows/Demo terminal is in the environment. Unlock condition: architect-approved Demo terminal + still-fail-closed live.
- `DEMO-*` must never be labeled broker truth (persistence rejects `pm5_broker`).

## 8. Trading readiness

The system is NOT ready for live trading, demo trading, paper trading, or production.

## 9. Exact next step

Sequence 12 — Unified Runtime Orchestrator.

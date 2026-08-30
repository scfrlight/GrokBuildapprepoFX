# Sequence 11 Report — MT5 Execution & Exit Engine (Demo-only)

Date (UTC): 2026-08-30  
Git home: `scfrlight/GrokBuildapprepoFX`  
Display name: **mt5_execution_engine**  
Master Orchestration **title** (not a package name): “PM6 MT5 Execution & Exit Engine”  
Package home: `botmoduleproject1.modules.mt5_execution_engine`  
Adapter: `botmoduleproject1.adapters.mt5`  
`pm6_post_trade` is **not** this module. See `docs/MODULE_NUMBERING_MAP.md`.

## 1. Git commit hash

Stamped after the numbering-correction push.

## 2. Created / updated files

### Created

- `botmoduleproject1/modules/mt5_execution_engine/` (`demo_routing.py`, `exit_engine.py`, `module.py`, README)
- `botmoduleproject1/adapters/mt5/capabilities.py`
- `botmoduleproject1/adapters/mt5/demo_gateway.py`
- `tests/unit/test_seq11_mt5_exit.py`
- `docs/MODULE_NUMBERING_MAP.md`

### Removed (old dual home)

- `botmoduleproject1/modules/pm5_execution/demo_routing.py`
- `botmoduleproject1/modules/pm5_execution/exit_engine.py`

### Unchanged (still blocked)

- `botmoduleproject1/modules/pm5_execution/ems/mt5_adapter.py` (`Mt5BrokerAdapter.submit` still raises `ExecutionDisabledError`)

## 3. Naming

Sequence 11 is **`mt5_execution_engine`**. Bare `pm6` is `pm6_post_trade` only.

## 4. Component status

| Component | Status | Notes |
|---|---|---|
| Demo MT5 adapter | COMPLETE | `DemoMt5Gateway`; tickets `DEMO-*`; simulated=True in tests |
| Live account probe | REFUSED | `probe_environment(account_kind="live")` raises |
| Real terminal on Linux | FAIL-CLOSED | `simulated=False` and no terminal → `ExecutionDisabledError` |
| Idempotent routing | COMPLETE | same `client_order_id` returns duplicate |
| Reconciliation | COMPLETE | disconnect → `degraded`, `silent_pass=False` |
| Structural SL/TP / BE / time stop | COMPLETE | `ExitEngine` |
| Entry must not talk to venue | COMPLETE | `DemoRouter` requires PM4 ALLOW |
| `python -m botmoduleproject1 live` | FAIL-CLOSED | `LiveTradingDisabledError` |

## 5. Tests

Gate file: `tests/unit/test_seq11_mt5_exit.py`. Official counts live in CI / `docs/evidence/pytest-3.11.log`.

## 6. Residual risks

- No MetaTrader5 terminal on Linux. Real demo send is **BLOCKED**.
- `DEMO-*` must never be labeled broker truth.

## 7. Trading readiness

The system is NOT ready for live trading, demo trading, paper trading, or production.

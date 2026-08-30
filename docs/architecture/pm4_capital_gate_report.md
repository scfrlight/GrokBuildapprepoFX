# PM4 capital-management gate report

Date (UTC): 2026-08-30  
Git home: `scfrlight/GrokBuildapprepoFX`  
Classification: **CAPITAL GATE HARDENING COMPLETE WITH PARTIALS — Sequence 11+ trading enablement remains blocked**

This is **not** Sequence 07 as a new canonical identity. Historical Master
Orchestration title “Sequence 07 / PM5 Risk Gate” maps to **canonical Sequence 06
`pm4_risk_gate`**. Canonical Sequence 07 remains `pm5_execution`. No competing
PM5 capital package was created. Sequence 15+ was not started.

## 1. Main SHA

Recorded at commit time on `main` (this report lands in the same commit). Parent
at start of this wave: `78928a4674dcc46e1c7c9864c33931a4d818d27e` (PM8 PostgreSQL
durability).

## 2. Changed files

### Created

- `botmoduleproject1/contracts/v1/pm4_capital.py`
- `botmoduleproject1/modules/pm4_risk_gate/capital/` (catalog, checks, sizing,
  portfolio, drawdown ledger, evaluation, persistence, adapters, safe-halt,
  hashing, metrics, boundary)
- `tests/unit/test_pm4_capital_gate.py`
- `tests/unit/test_pm4_capital_persistence.py`
- `docs/guides/pm4_capital_gate.md`
- `docs/architecture/pm4_capital_gate_report.md`
- `docs/evidence/pm4_capital/`

### Updated

- `botmoduleproject1/modules/pm4_risk_gate/module.py` (`evaluate_capital`)
- `botmoduleproject1/modules/pm4_risk_gate/config/schema.py`
- `botmoduleproject1/app/settings.py`
- `botmoduleproject1/contracts/v1/__init__.py`
- `configs/pm4_risk_gate.example.yaml`
- `docs/MODULE_NUMBERING_MAP.md`, `docs/TRACEABILITY_MATRIX.md`,
  `docs/architecture/pm4_risk_gate_test_traceability.md`, READMEs,
  known limitations, architecture inventory

Trading, broker, Telegram, and Sequence 15 modules were not enabled.

## 3. Sequence 00–14 status

| Seq | Content | Status |
|---|---|---|
| 00–05 | Kernel through forecasting | COMPLETE (historical, flags off) |
| **06** | **PM4 risk gate + capital hardening** | COMPLETE exclusive gate; capital pipeline added; flag off |
| 07 | PM5 OMS/EMS sim | COMPLETE `SIM-*`; not a risk gate |
| 08 | PM6 post-trade | COMPLETE in-memory |
| 09–10 | PM8 / PM8a | COMPLETE sequence; `production_durable` refused |
| 11 | `mt5_execution_engine` | COMPLETE sim/test-safe; real terminal BLOCKED |
| 12 | Unified runtime | COMPLETE observe pipeline |
| 13 | Operator UX | COMPLETE; Telegram unbound |
| 14 | Observability | COMPLETE observe-only |
| 15+ | — | **BLOCKED** |

## 4. PM module status

| PM | Status after this wave |
|---|---|
| PM4 | Exclusive risk gate. Capital pipeline is `evaluate_capital`. ALLOW / approved intent ≠ order. |
| PM5 | Unchanged OMS/EMS simulation. Not rewritten. |
| PM6 | Cannot submit or size. Unchanged. |
| PM7 | PARTIAL evidence-journal. Unchanged. |
| PM8 | Canonical persistence API used by the capital gate. PostgreSQL NUMERIC path used in tests. `production_durable` refused. |

## 5. Test matrix

See `docs/evidence/pm4_capital/pytest-3.11.log`. Capital tests:
`tests/unit/test_pm4_capital_gate.py`, `tests/unit/test_pm4_capital_persistence.py`
(PostgreSQL marked `postgres`). Existing PM4 safety tests remain green.

## 6. Python 3.10 fail-fast

ADR-008 unchanged. `doctor` on 3.10 must exit 1.

## 7. CI

`.github/workflows/tests.yml` already runs pytest 3.11/3.12 with `postgres:16`
and `BOTMODULEPROJECT1_DATABASE_URL`. Capital postgres tests use the same marker
and DSN discovery as PM8 durability.

## 8. Raw evidence

`docs/evidence/pm4_capital/` — pytest log, exported JSON snapshot, checksums.
No DSN / `postgresql://` in evidence (hygiene).

## 9. Forty-check coverage

Catalog in `capital/catalog.py`. Every evaluation, including fail-closed,
emits all 40 names. Missing data → `block`.

## 10. Sizing / heat / drawdown

- Lots = budget / (effective_stop × contract × conversion_rate), `ROUND_DOWN`
  to lot step. Never round up through a risk limit.
- Transaction costs: spread+slippage in effective stop; commission subtracted
  from budget.
- Heat = (open + pending + projected) / equity vs `max_effective_heat`.
- Drawdown ledger persists `risk.drawdown.snapshot`; peak is monotonic across
  restart; UTC day roll zeros daily loss only.

## 11. Persistence / idempotency / replay

- `PersistenceApiV1` only. No second database.
- Same key + same hash → stored result (in-process memo and PM8 lookup).
- Same key + different hash → `ValueError` conflict, not approval.
- Replay uses `persist=False`, `use_memo=False`. Divergence event does not
  overwrite the original decision.

## 12. Fail-closed / safe-halt

Exceptions, persistence down, unknown exposure, injected faults →
`ERROR_FAIL_CLOSED` or the matching `BLOCKED_*` state, size zero, no executable
intent. Safe-halt recovery refuses `actor=automatic`.

## 13. Safety locks (still held)

- `execution_allowed=false`, `execution_permitted=false`, `trading_readiness=false`
- `creates_order=false`
- Live CLI fail-closed
- Telegram refused
- `/buy` REFUSED
- PM4 exclusive
- PM6/PM7/PM8 cannot submit/order/size
- No `sequence_15_report.md`, no `enable_sequence_15`
- Venue absence ≠ PASS
- Simulation ticket ≠ broker truth

## 14. App Builder viewer

Ops console tab reads `/observability/pm4_capital_gate.json`. Auth/DB remain
OFF. Neon is not wired. Not a trading UI.

## 15. Known limitations

- Feature flag `enable_pm4_risk_gate` still defaults false; container still
  binds `NullRiskGate` unless env-opted.
- Capital restart-safe drawdown requires PM8 persistence to be injected;
  `from_settings` does not auto-bind PM8.
- Replay divergence is detected; automatic repair is refused.
- `production_durable` remains refused.
- Fitted QRF / real MT5 / Sequence 15 remain out of scope.

## 16. What this is not

Not Sequence 11, 12, 13, 14, 15, 16, or 17 as a completion claim. Not a PM5
rewrite. Not trading enablement. Not auto-rearm. Not an order router.

## 17. Classification

**CAPITAL GATE HARDENING COMPLETE WITH PARTIALS — Sequence 11+ trading
enablement remains blocked.**

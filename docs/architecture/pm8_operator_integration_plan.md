> **RECLASSIFIED 2026-08-30.** This plan was written as Sequence 10. Canonical home is **Sequence 13** (PM9 Operator UX). See `docs/SEQUENCE_CORRECTION.md`.

# PM8 Operator Control Plane — Integration Plan

Status: Accepted before the operator early build; reclassified Sequence 13  
Date (UTC): 2026-08-29  
Sequence: 13 preview / early build (historically labeled Sequence 10)

This plan is written **before** module implementation. It is the Sequence 10
source-of-truth together with `docs/prompts/PM8_Operator_Sequence10_Prompt.md`
and ADR-015.

## 1. Naming (deliberate)

Sequence 09 named this step **PM8 Operator Control Plane**. The Sequence 00
module map used `pm8_persistence` for CQRS/outbox and `pm9_operator_ux` for
Telegram/HITL.

Sequence 09 already delivered the append-only journal (PM7). CQRS/outbox
(`pm8_persistence` / NullStorage) remains a **future** persistence API and is
**not** implemented here. Sequence 10 implements the operator control plane:

| Item | Value |
|---|---|
| Package | `botmoduleproject1/modules/pm8_operator/` |
| Registry name | `pm8_operator` |
| Compatibility re-export | `modules/pm9_operator_ux` |
| Default bind | `NullOperator` (flag off) |
| Flag-on transport | `SimulatedTransport` |
| Real Telegram Bot API | refused |
| `pm8_persistence` | unchanged stub (`NullStorage`) |

## 2. Role

PM8 is the **human-in-the-loop operations plane**:

- command ingestion (slash text or structured)
- RBAC
- HITL approval queue
- safe-direction halt request
- research tuning proposals (PM9a studio, never auto-live)
- operator read models
- audit of every command
- Telegram **encode/decode only** (no business logic in the adapter)

PM8 is **not** a strategy engine, risk gate, OMS/EMS, broker adapter, journal,
or a Telegram bot that can trade.

```text
Operator / Simulated transport / Telegram decoder
  → OperatorCommand (contracts)
  → RBAC
  → Router (accept / refuse / HITL)
  → Application ports (status, halt request, ack, propose)
  → CommandReceipt + audit
  → Encoder (text out)
```

## 3. Safety invariants

1. No broker orders. `/buy`, `/sell`, `/order`, `PLACE_ORDER` are **refused**.
2. No MT5. `CONNECT_MT5` is refused. Adapter never imports `adapters.mt5`.
3. No live enable. `ENABLE_LIVE` is refused.
4. No auto-rearm. `RESUME` / `REARM` are refused.
5. Approval does **not** skip PM4 and does **not** become an `OrderRequest`.
6. Telegram transport contains **no** trading logic.
7. Secrets (bot token) are never logged, exported, or put in receipts.
8. YAML flags stay false. Test/research env opt-in only for the control plane.
9. Real Telegram Bot API is refused in Sequence 10 (dangerous flag cannot bind it).
10. Dual-control and HITL never authorize execution.
11. Studio `auto_promote_to_live` is always `false`.
12. Default bind remains `NullOperator`. Live/demo/paper/production stay unauthorized.

## 4. Feature flags

| Flag | Field | Safety | Profiles | Effect |
|---|---|---|---|---|
| `enable_pm8_operator` | `pm8_operator` | requires-review | test, research | Master bind |
| `enable_pm8_hitl` | `pm8_hitl` | requires-review | test, research | Approval queue |
| `enable_pm8_command_audit` | `pm8_command_audit` | requires-review | test, research | Audit trail |
| `enable_fine_tune_studio` | `fine_tune_studio` | requires-review | test, research | Studio proposals |
| `enable_telegram_control` | `telegram` | dangerous | — | **Refused** in Sequence 10 |

Prefixed env only: `BOTMODULEPROJECT1_FEATURE__ENABLE_PM8_*`.

## 5. Commands

**Allowed (RBAC gated):** `HELP`, `STATUS`, `HEALTH`, `DOCTOR`, `PENDING`,
`LIST_ALERTS`, `QUERY_JOURNAL`, `ACK`, `HALT`, `APPROVE`, `REJECT`,
`PROPOSE_TUNING`.

**Always refused:** `PLACE_ORDER`, `BUY`, `SELL`, `RESUME`, `REARM`,
`ENABLE_LIVE`, `CONNECT_MT5`.

Roles: `observer` < `operator` < `risk_officer` < `admin`. Halt and HITL
decisions require `risk_officer` or `admin`. Observer is read-only.

## 6. Transports

| Mode | When | Network |
|---|---|---|
| `disabled` | flag off (`NullOperator`) | none |
| `simulated` | flag on (default) | none |
| `telegram_api` | never in Sequence 10 | refused |

`adapters/telegram` may decode/encode message shapes. It must not decide
verbs, authorize actors, or call MT5.

## 7. Integration

- PM1 registry / health / capabilities / manifest.
- Consumes PM7 query/publication **if bound**; otherwise read models say
  `ledger_unavailable` (honest). Never writes the PM7 canonical stream except
  as optional audit events through the ledger port.
- Must not reimplement PM4/PM5/PM6/PM7.

## 8. Build gate

Pass when: flags off by default, NullOperator default, refused verbs stay
refused, HITL cannot skip PM4, simulated transport only, tests green, docs
updated. The system is **not** ready to trade.

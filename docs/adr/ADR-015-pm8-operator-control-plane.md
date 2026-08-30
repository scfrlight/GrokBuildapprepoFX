> **RECLASSIFIED 2026-08-30.** This ADR was written as Sequence 10. Canonical sequence for the operator plane is **13**. See `docs/SEQUENCE_CORRECTION.md`.

# ADR-015 — PM8 operator control plane and HITL boundary

Status: Accepted (sequence number corrected to 13)  
Date (UTC): 2026-08-29  
Sequence: 13 (historically labeled 10)

## Context

Sequence 09 delivered an append-only journal (PM7). Sequence 00 reserved
`pm8_persistence` for CQRS/outbox and `pm9_operator_ux` for Telegram.
Sequence 09's next step named Sequence 10 **PM8 Operator Control Plane,
Telegram Control Engine & Human-in-the-Loop Operations**.

## Decision

1. Implement the operator control plane as `modules/pm8_operator` (registry
   `pm8_operator`). Re-export via `pm9_operator_ux`.
2. Leave `pm8_persistence` / `NullStorage` as the future CQRS path.
   PM7 publication handoff remains `pending_pm8`.
3. Default bind is `NullOperator`. Flag-on bind uses `SimulatedTransport`.
4. Real Telegram Bot API is refused. The adapter may only encode/decode.
5. Commands never become orders. HITL approval does not skip PM4.
6. Studio proposals cannot auto-promote to live.
7. `/buy` `/sell` `/order` `/resume` `/rearm` `/live` `/mt5` are refused.

## Consequences

Operators can inspect, halt (safe direction), ack, and record HITL consent
in test/research. They cannot trade. Telegram remains a future transport.

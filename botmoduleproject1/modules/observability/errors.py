"""Unified error taxonomy. Public messages never include secrets or paths."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.observability import ErrorCode, ErrorSeverity, ErrorSpec

ERROR_CATALOG: tuple[ErrorSpec, ...] = (
    ErrorSpec(code=ErrorCode.CONFIGURATION_ERROR, severity=ErrorSeverity.ERROR, retryable=False, operator_action="Inspect YAML/env against configuration guide. Do not force-start.", system_action="Fail closed. Do not enter ready.", trading_must_halt=True, audit_required=True, public_safe_message="Configuration is invalid. Process will not start."),
    ErrorSpec(code=ErrorCode.UNSUPPORTED_PYTHON_VERSION, severity=ErrorSeverity.CRITICAL, retryable=False, operator_action="Restart on Python 3.11+.", system_action="Exit 1 before importing settings.", trading_must_halt=True, audit_required=True, public_safe_message="Python version is not supported. Python 3.11+ is required."),
    ErrorSpec(code=ErrorCode.VALIDATION_ERROR, severity=ErrorSeverity.ERROR, retryable=False, operator_action="Correct the payload against the v1 contract.", system_action="Reject the message. Do not mutate state.", trading_must_halt=False, audit_required=True, public_safe_message="Payload failed contract validation."),
    ErrorSpec(code=ErrorCode.CONTRACT_ERROR, severity=ErrorSeverity.ERROR, retryable=False, operator_action="Stop the producer and file an incident.", system_action="Drop the event. Do not coerce types.", trading_must_halt=True, audit_required=True, public_safe_message="Contract mismatch between modules."),
    ErrorSpec(code=ErrorCode.STALE_DATA_ERROR, severity=ErrorSeverity.WARNING, retryable=True, operator_action="Observe only. Do not force a tick.", system_action="Safe-stop routing. Mark operational health degraded.", trading_must_halt=True, audit_required=True, public_safe_message="Market data is stale. Observe-only."),
    ErrorSpec(code=ErrorCode.PERSISTENCE_ERROR, severity=ErrorSeverity.CRITICAL, retryable=True, operator_action="Follow persistence-unavailable runbook. Do not rewrite history.", system_action="Mark persistence not-ready. Refuse writes that cannot be journaled.", trading_must_halt=True, audit_required=True, public_safe_message="Persistence is unavailable."),
    ErrorSpec(code=ErrorCode.INTEGRITY_ERROR, severity=ErrorSeverity.CRITICAL, retryable=False, operator_action="Preserve the ledger. Escalate. Do not repair by rewrite.", system_action="Halt writes. Record a correction event only.", trading_must_halt=True, audit_required=True, public_safe_message="Ledger integrity check failed."),
    ErrorSpec(code=ErrorCode.IDEMPOTENCY_CONFLICT, severity=ErrorSeverity.WARNING, retryable=False, operator_action="Inspect the original record. Do not retry with a new identity.", system_action="Ignore the duplicate. Keep the first commit.", trading_must_halt=False, audit_required=True, public_safe_message="Idempotent request already committed."),
    ErrorSpec(code=ErrorCode.DUPLICATE_EVENT, severity=ErrorSeverity.INFO, retryable=False, operator_action="Confirm the original event id. No action if identical.", system_action="Return duplicate-ignored.", trading_must_halt=False, audit_required=True, public_safe_message="Duplicate event ignored."),
    ErrorSpec(code=ErrorCode.DUPLICATE_EXECUTION, severity=ErrorSeverity.WARNING, retryable=False, operator_action="Do not resubmit. Inspect SIM/DEMO ticket, never treat as broker truth.", system_action="Refuse the second submit.", trading_must_halt=False, audit_required=True, public_safe_message="Duplicate execution attempt refused."),
    ErrorSpec(code=ErrorCode.BROKER_UNAVAILABLE, severity=ErrorSeverity.ERROR, retryable=True, operator_action="Do not send orders. Venue absence is degraded, not pass.", system_action="Set broker venue unavailable. Reconciliation cannot pass.", trading_must_halt=True, audit_required=True, public_safe_message="Broker venue is unavailable."),
    ErrorSpec(code=ErrorCode.BROKER_REJECTED, severity=ErrorSeverity.WARNING, retryable=False, operator_action="Read the simulated rejection. Do not coerce to fill.", system_action="Record DEMO/SIM rejection. Do not invent a fill.", trading_must_halt=False, audit_required=True, public_safe_message="Simulated execution was rejected."),
    ErrorSpec(code=ErrorCode.RECONCILIATION_MISMATCH, severity=ErrorSeverity.ERROR, retryable=False, operator_action="Do not force pass. Follow reconciliation-degraded runbook.", system_action="Status=degraded. Never auto-pass without a venue.", trading_must_halt=True, audit_required=True, public_safe_message="Reconciliation mismatch. Status is degraded."),
    ErrorSpec(code=ErrorCode.PROJECTION_ERROR, severity=ErrorSeverity.ERROR, retryable=True, operator_action="Do not rebuild against a live write path.", system_action="Keep the projection stale. Schedule an isolated rebuild.", trading_must_halt=True, audit_required=True, public_safe_message="Projection rebuild failed."),
    ErrorSpec(code=ErrorCode.RECOVERY_ERROR, severity=ErrorSeverity.CRITICAL, retryable=True, operator_action="Do not promote. Recovery must finish before any routing.", system_action="trading_readiness=false. Stay degraded.", trading_must_halt=True, audit_required=True, public_safe_message="Recovery did not complete."),
    ErrorSpec(code=ErrorCode.PERMISSION_DENIED, severity=ErrorSeverity.WARNING, retryable=False, operator_action="Do not escalate privileges ad hoc.", system_action="Deny the command. Audit the attempt.", trading_must_halt=False, audit_required=True, public_safe_message="Operator permission denied."),
    ErrorSpec(code=ErrorCode.UNSAFE_OPERATION, severity=ErrorSeverity.CRITICAL, retryable=False, operator_action="Stop. Do not retry live, paper, or Telegram bind.", system_action="Fail closed.", trading_must_halt=True, audit_required=True, public_safe_message="Unsafe operation refused."),
    ErrorSpec(code=ErrorCode.SECRET_HANDLING_ERROR, severity=ErrorSeverity.CRITICAL, retryable=False, operator_action="Rotate the exposed credential. Follow secret-exposure runbook.", system_action="Redact, halt export, mark evidence compromised if needed.", trading_must_halt=True, audit_required=True, public_safe_message="Secret handling failed. Values are never logged."),
    ErrorSpec(code=ErrorCode.UNEXPECTED_INTERNAL_ERROR, severity=ErrorSeverity.CRITICAL, retryable=False, operator_action="Preserve logs. Do not paste traces into chat with secrets.", system_action="Fail the operation. Do not leak traceback to operator-facing text.", trading_must_halt=True, audit_required=True, public_safe_message="Internal error. Trading remains halted."),
)

ERROR_BY_CODE: dict[ErrorCode, ErrorSpec] = {spec.code: spec for spec in ERROR_CATALOG}


def public_message(code: ErrorCode) -> str:
    return ERROR_BY_CODE[code].public_safe_message


def trading_must_halt(code: ErrorCode) -> bool:
    return ERROR_BY_CODE[code].trading_must_halt

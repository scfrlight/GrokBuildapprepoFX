"""Operator roles and permission scopes (PM9)."""

from __future__ import annotations

from enum import Enum


class OperatorRole(str, Enum):
    OBSERVER = "observer"
    OPERATOR = "operator"
    RISK_OFFICER = "risk_officer"
    ADMIN = "admin"


class PermissionScope(str, Enum):
    READ_STATUS = "read_status"
    RUN_DOCTOR = "run_doctor"
    ISSUE_COMMAND = "issue_command"
    APPROVE_INTENT = "approve_intent"
    CHANGE_TUNING = "change_tuning"
    HALT_SYSTEM = "halt_system"

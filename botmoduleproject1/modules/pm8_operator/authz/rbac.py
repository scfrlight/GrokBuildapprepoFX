"""Role → verb matrix. Observer is read-only. Nobody may place orders."""

from __future__ import annotations

from botmoduleproject1.contracts.v1.operator import READ_VERBS, REFUSED_VERBS, OperatorVerb
from botmoduleproject1.contracts.v1.roles import OperatorRole, PermissionScope

_OPERATOR_EXTRA = frozenset({OperatorVerb.ACK, OperatorVerb.PROPOSE_TUNING})
_RISK_EXTRA = frozenset({OperatorVerb.HALT, OperatorVerb.APPROVE, OperatorVerb.REJECT})


def allowed_verbs(role: OperatorRole) -> frozenset[OperatorVerb]:
    allowed = set(READ_VERBS)
    if role in {OperatorRole.OPERATOR, OperatorRole.RISK_OFFICER, OperatorRole.ADMIN}:
        allowed |= _OPERATOR_EXTRA
    if role in {OperatorRole.RISK_OFFICER, OperatorRole.ADMIN}:
        allowed |= _RISK_EXTRA
    return frozenset(allowed) - REFUSED_VERBS


def has_permission(role: OperatorRole, verb: OperatorVerb) -> bool:
    if verb in REFUSED_VERBS:
        return False
    return verb in allowed_verbs(role)


def scopes_for(role: OperatorRole) -> frozenset[PermissionScope]:
    scopes = {PermissionScope.READ_STATUS, PermissionScope.RUN_DOCTOR}
    if role is OperatorRole.OBSERVER:
        return frozenset(scopes)
    scopes.add(PermissionScope.ISSUE_COMMAND)
    if role in {OperatorRole.OPERATOR, OperatorRole.RISK_OFFICER, OperatorRole.ADMIN}:
        scopes.add(PermissionScope.CHANGE_TUNING)
    if role in {OperatorRole.RISK_OFFICER, OperatorRole.ADMIN}:
        scopes.add(PermissionScope.APPROVE_INTENT)
        scopes.add(PermissionScope.HALT_SYSTEM)
    return frozenset(scopes)

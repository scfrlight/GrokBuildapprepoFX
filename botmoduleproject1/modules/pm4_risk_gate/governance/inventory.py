from __future__ import annotations

from datetime import datetime
from typing import Any

from botmoduleproject1.modules.pm4_risk_gate.domain.policies import CONTROL_VERSION, POLICY_OWNER, PRODUCER


class GovernanceRegistry:
    def __init__(self) -> None:
        self.algorithms: list[dict[str, Any]] = [
            {
                "id": PRODUCER,
                "version": CONTROL_VERSION,
                "owner": POLICY_OWNER,
                "kind": "risk_gate",
                "last_review": None,
            }
        ]
        self.controls: list[dict[str, Any]] = [
            {"id": "admission", "owner": POLICY_OWNER},
            {"id": "budget", "owner": POLICY_OWNER},
            {"id": "sizing", "owner": POLICY_OWNER},
            {"id": "heat", "owner": POLICY_OWNER},
            {"id": "concentration", "owner": POLICY_OWNER},
            {"id": "drawdown", "owner": POLICY_OWNER},
            {"id": "pretrade", "owner": POLICY_OWNER},
            {"id": "kill_switch", "owner": POLICY_OWNER},
        ]
        self.approvals: list[dict[str, Any]] = []
        self.parameter_history: list[dict[str, Any]] = []

    def note_review(self, now: datetime, actor: str, reason: str) -> None:
        self.approvals.append(
            {"at": now.isoformat(), "actor": actor, "reason": reason, "status": "reviewed"}
        )
        self.algorithms[0]["last_review"] = now.isoformat()

    def note_param_change(self, now: datetime, name: str, before: str, after: str, actor: str) -> None:
        self.parameter_history.append(
            {
                "at": now.isoformat(),
                "name": name,
                "before": before,
                "after": after,
                "actor": actor,
            }
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "algorithms": list(self.algorithms),
            "controls": list(self.controls),
            "approvals": list(self.approvals),
            "parameter_history": list(self.parameter_history),
            "durable": False,
        }

from __future__ import annotations

from botmoduleproject1.modules.pm3_strategy_engine.domain.entities import StrategyProfile


class ProfileService:
    def __init__(self, profiles, versions) -> None:
        self.profiles = profiles
        self.versions = versions

    def get(self, profile_id: str) -> StrategyProfile | None:
        return self.profiles.get(profile_id)

    def list_all(self) -> tuple[StrategyProfile, ...]:
        return self.profiles.list_all()

    def version_history(self, profile_id: str):
        return self.versions.list_for_profile(profile_id)

    def compare_versions(self, left_id: str, right_id: str) -> dict:
        left = self.versions.get(left_id)
        right = self.versions.get(right_id)
        if left is None or right is None:
            raise ValueError("unknown version")
        keys = set(left.parameters) | set(right.parameters)
        diff = {
            k: {"left": left.parameters.get(k), "right": right.parameters.get(k)}
            for k in sorted(keys)
            if left.parameters.get(k) != right.parameters.get(k)
        }
        return {"left": left_id, "right": right_id, "diff": diff}

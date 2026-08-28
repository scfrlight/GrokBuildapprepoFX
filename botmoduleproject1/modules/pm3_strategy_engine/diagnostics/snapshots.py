from typing import Any


def module_snapshot(*, enabled: bool, last: str | None) -> dict[str, Any]:
    return {
        "module": "pm3_strategy_engine",
        "display_name": "PM3-Strategy Engine",
        "enabled": enabled,
        "observe_only": True,
        "last": last,
    }

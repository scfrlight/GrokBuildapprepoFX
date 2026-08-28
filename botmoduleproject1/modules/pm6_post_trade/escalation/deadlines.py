def deadline_for(severity: str) -> int:
    return {"critical": 0, "high": 300, "medium": 3600}.get(severity, 86400)

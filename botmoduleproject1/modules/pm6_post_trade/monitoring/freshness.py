from datetime import datetime, timedelta


def age_seconds(stamp: datetime | None, now: datetime) -> int:
    if stamp is None:
        return 0
    return max(0, int((now - stamp).total_seconds()))


def is_stale(stamp: datetime | None, now: datetime, ttl: int) -> bool:
    if stamp is None:
        return True
    return now - stamp > timedelta(seconds=ttl)

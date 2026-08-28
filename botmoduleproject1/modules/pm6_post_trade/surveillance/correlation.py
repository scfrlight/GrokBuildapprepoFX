from __future__ import annotations

from botmoduleproject1.contracts.v1.post_trade import PostTradeAlert


def correlate(alerts: tuple[PostTradeAlert, ...]) -> dict[str, list[PostTradeAlert]]:
    groups: dict[str, list[PostTradeAlert]] = {}
    for alert in alerts:
        key = alert.scope
        if alert.linked_orders:
            key = str(alert.linked_orders[0])
        groups.setdefault(key, []).append(alert)
    return groups

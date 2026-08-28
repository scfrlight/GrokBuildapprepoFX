from botmoduleproject1.contracts.v1.risk import KillSwitchScope


def matches(scope: KillSwitchScope, scope_id: str | None, symbol: str, sleeve: str | None, cluster: str | None) -> bool:
    if scope is KillSwitchScope.ACCOUNT:
        return True
    if scope is KillSwitchScope.SYMBOL:
        return (scope_id or "").upper() == symbol.upper()
    if scope is KillSwitchScope.STRATEGY:
        return bool(sleeve) and scope_id == sleeve
    if scope is KillSwitchScope.CLUSTER:
        return bool(cluster) and scope_id == cluster
    return False

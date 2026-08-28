def may_purge(*, frozen: bool, allow_purge: bool, simulate: bool) -> tuple[bool, str]:
    if frozen:
        return False, "frozen"
    if not allow_purge:
        return False, "purge_disabled"
    if simulate:
        return False, "simulated_only"
    return True, "allowed"

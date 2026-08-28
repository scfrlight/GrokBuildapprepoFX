from botmoduleproject1.modules.pm7_persistence.domain.errors import RetentionFrozenError


def assert_not_frozen(frozen: bool) -> None:
    if frozen:
        raise RetentionFrozenError("legal/audit freeze blocks purge")

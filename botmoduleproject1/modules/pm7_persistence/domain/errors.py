class Pm7Error(Exception):
    """PM7 persistence error."""


class ImmutableJournalError(Pm7Error):
    """Committed records cannot be mutated."""


class UnauthorizedQueryError(Pm7Error):
    """Query lacked authorization."""


class RetentionFrozenError(Pm7Error):
    """Purge/archive blocked by freeze or lock."""


class ProductionDurableRefused(Pm7Error):
    """production_durable is not available in Sequence 09."""

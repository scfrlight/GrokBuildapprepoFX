from botmoduleproject1.contracts.v1.persistence import ArchiveTier, IntegrityState, ReplayState, SnapshotState

ACTIVE_REPLAY = {ReplayState.SCHEDULED, ReplayState.RUNNING}
TERMINAL_SNAPSHOT = {SnapshotState.STALE, SnapshotState.SUPERSEDED, SnapshotState.CORRUPT}
LOCKED_TIERS = {ArchiveTier.FROZEN, ArchiveTier.RETENTION_LOCK}

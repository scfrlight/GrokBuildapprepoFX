from __future__ import annotations

from botmoduleproject1.contracts.v1.persistence import ArchiveTier, RetentionStatus
from botmoduleproject1.modules.pm7_persistence.domain.errors import RetentionFrozenError
from botmoduleproject1.modules.pm7_persistence.retention.archive import TIER_ORDER
from botmoduleproject1.modules.pm7_persistence.retention.manifests import archive_manifest
from botmoduleproject1.modules.pm7_persistence.retention.purge_policy import may_purge


class RetentionService:
    def __init__(self, *, simulate_archive: bool = True, allow_purge: bool = False) -> None:
        self.tier = ArchiveTier.ACTIVE
        self.frozen = False
        self.lock_reason = None
        self.simulate_archive = simulate_archive
        self.allow_purge = allow_purge
        self.actions: list[str] = []

    def status(self, *, now, sequence: int = 0, tip: str | None = None) -> RetentionStatus:
        manifest = archive_manifest(tier=self.tier, sequence=sequence, frozen=self.frozen, checksum_tip=tip)
        return RetentionStatus(
            occurred_at=now,
            tier=self.tier,
            frozen=self.frozen,
            lock_reason=self.lock_reason,
            purge_eligible=self.tier is ArchiveTier.PURGE_ELIGIBLE and not self.frozen,
            simulated=self.simulate_archive,
            manifest_checksum=manifest["checksum"],
        )

    def transition(self, tier: ArchiveTier, *, now) -> RetentionStatus:
        if self.frozen and tier is ArchiveTier.PURGED_IF_ALLOWED:
            raise RetentionFrozenError("frozen")
        self.tier = tier
        self.actions.append(f"{now.isoformat()}:{tier.value}")
        return self.status(now=now)

    def freeze(self, *, reason: str, now) -> RetentionStatus:
        self.frozen = True
        self.lock_reason = reason
        self.tier = ArchiveTier.FROZEN
        self.actions.append(f"{now.isoformat()}:freeze:{reason}")
        return self.status(now=now)

    def lock(self, *, reason: str, now) -> RetentionStatus:
        self.frozen = True
        self.lock_reason = reason
        self.tier = ArchiveTier.RETENTION_LOCK
        return self.status(now=now)

    def purge(self, *, now, deleted: list | None = None) -> tuple[RetentionStatus, str]:
        ok, why = may_purge(frozen=self.frozen, allow_purge=self.allow_purge, simulate=self.simulate_archive)
        if not ok:
            if self.frozen:
                raise RetentionFrozenError(why)
            self.actions.append(f"{now.isoformat()}:purge_blocked:{why}")
            return self.status(now=now), why
        if deleted is not None:
            deleted.clear()
        self.tier = ArchiveTier.PURGED_IF_ALLOWED
        return self.status(now=now), "purged"

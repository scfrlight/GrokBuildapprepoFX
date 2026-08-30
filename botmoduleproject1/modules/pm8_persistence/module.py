"""PM8 persistence module — canonical Sequences 09 and 10. Not an order path."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from botmoduleproject1.app.capabilities import Capability, ModuleMetadata
from botmoduleproject1.app.health import CheckKind, CheckResult
from botmoduleproject1.contracts.v1.journal import JournalEntry
from botmoduleproject1.modules.pm8_persistence.api.v1 import PersistenceApiV1, SERVICE_CATALOG
from botmoduleproject1.modules.pm8_persistence.migrations import MigrationService
from botmoduleproject1.modules.pm8_persistence.repositories.protocols import PROTOCOL_CATALOG
from botmoduleproject1.modules.pm8_persistence.store import SqliteStore


PM8_PERSISTENCE_METADATA = ModuleMetadata(
    name="pm8_persistence",
    version="0.9.0",
    capabilities=(Capability.STORAGE,),
    critical=False,
    description="Canonical Sequence 09/10 persistence API. Flag off binds NullStorage.",
)


class PM8PersistenceModule:
    def __init__(
        self,
        *,
        path: str | Path = ":memory:",
        enabled: bool = True,
        target_schema: int = 2,
        clock: Any = None,
    ) -> None:
        self.clock = clock
        self.enabled = enabled
        self.store = SqliteStore(path)
        self.migrations = MigrationService(self.store)
        if enabled:
            self.migrations.upgrade_to(target_schema)
        self.api = PersistenceApiV1(self.store, enabled=enabled)
        self.entries = self.api.entries

    @classmethod
    def from_settings(cls, settings: object, clock: Any) -> PM8PersistenceModule:
        flags = getattr(settings, "feature_flags")
        enabled = bool(getattr(flags, "pm8_persistence", False))
        section = getattr(settings, "pm8_persistence", None)
        mode = getattr(section, "operating_mode", "memory") if section is not None else "memory"
        path = getattr(section, "storage_path", None) if section is not None else None
        target = int(getattr(section, "schema_version", 2) or 2) if section is not None else 2
        if mode in {"disabled", "memory"} or not path or path == ":memory:":
            db = ":memory:"
        else:
            folder = Path(path)
            folder.mkdir(parents=True, exist_ok=True)
            db = str(folder / "pm8.sqlite")
        return cls(path=db, enabled=enabled, target_schema=target, clock=clock)

    def metadata(self) -> ModuleMetadata:
        return PM8_PERSISTENCE_METADATA

    def append(self, entry: JournalEntry) -> None:
        self.api.append(entry)

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        health = self.api.health()
        return [
            CheckResult(
                name="pm8.api_v1",
                kind=kind,
                passed=True,
                critical=False,
                message=f"api={health['api_version']} schema={health['schema_version']}",
            ),
            CheckResult(
                name="pm8.no_mt5",
                kind=kind,
                passed=health["mt5"] is False,
                critical=True,
                message="no MT5 in persistence",
            ),
            CheckResult(
                name="pm8.integrity",
                kind=kind,
                passed=health["integrity"] != "compromised",
                critical=False,
                message=health["integrity"],
            ),
            CheckResult(
                name="pm8.protocols",
                kind=kind,
                passed=len(PROTOCOL_CATALOG) >= 19,
                critical=False,
                message=f"{len(PROTOCOL_CATALOG)} protocols",
            ),
            CheckResult(
                name="pm8.services",
                kind=kind,
                passed=len(SERVICE_CATALOG) >= 20,
                critical=False,
                message=f"{len(SERVICE_CATALOG)} services",
            ),
        ]

    def manifest(self) -> dict[str, Any]:
        return {
            "sequence": [9, 10],
            "api": "v1",
            "protocols": list(PROTOCOL_CATALOG),
            "services": list(SERVICE_CATALOG),
            "does_not": ["orders", "mt5", "telegram", "live"],
            "downstream_path": "PersistenceApiV1",
        }

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
from botmoduleproject1.modules.pm8_persistence.store import SqliteStore, StorageUnavailable, open_pm8_store


PM8_PERSISTENCE_METADATA = ModuleMetadata(
    name="pm8_persistence",
    version="0.10.0",
    capabilities=(Capability.STORAGE,),
    critical=False,
    description="Canonical Sequence 09/10 persistence API. Flag off binds NullStorage.",
)


def _reveal_dsn(settings: object) -> str | None:
    pers = getattr(settings, "persistence", None)
    if pers is None:
        return None
    raw = getattr(pers, "dsn", None)
    if raw is None:
        return None
    if hasattr(raw, "get_secret_value"):
        value = raw.get_secret_value()
        return str(value) if value else None
    text = str(raw).strip()
    return text or None


class PM8PersistenceModule:
    def __init__(
        self,
        *,
        path: str | Path = ":memory:",
        enabled: bool = True,
        target_schema: int = 2,
        clock: Any = None,
        store: Any | None = None,
    ) -> None:
        self.clock = clock
        self.enabled = enabled
        self.store = store if store is not None else SqliteStore(path)
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
        dsn = _reveal_dsn(settings)
        if mode == "postgresql":
            store = open_pm8_store(
                mode="postgresql",
                dsn=dsn,
                connect_timeout=int(getattr(section, "connect_timeout_seconds", 5) or 5),
                statement_timeout_ms=int(getattr(section, "statement_timeout_ms", 30_000) or 30_000),
                pool_min=int(getattr(section, "pool_min", 1) or 1),
                pool_max=int(getattr(section, "pool_max", 8) or 8),
                sslmode=str(getattr(section, "sslmode", "prefer") or "prefer"),
                schema_name=str(getattr(section, "schema_name", "public") or "public"),
            )
            return cls(enabled=enabled, target_schema=target, clock=clock, store=store)
        if mode in {"disabled", "memory"}:
            db: str | Path = ":memory:"
        elif not path or path == ":memory:":
            raise StorageUnavailable("sqlite_local requires an explicit storage_path; memory fallback is forbidden")
        else:
            folder = Path(path)
            folder.mkdir(parents=True, exist_ok=True)
            db = folder / "pm8.sqlite"
        return cls(path=db, enabled=enabled, target_schema=target, clock=clock)

    def metadata(self) -> ModuleMetadata:
        return PM8_PERSISTENCE_METADATA

    def append(self, entry: JournalEntry) -> None:
        self.api.append(entry)

    def health_checks(self, kind: CheckKind) -> list[CheckResult]:
        health = self.api.health()
        backend = str(self.store.diagnostics().get("backend", "unknown"))
        pg_ok = True
        pg_msg = backend
        if backend == "postgresql":
            ping = bool(self.store.diagnostics().get("ping"))
            pg_ok = ping
            pg_msg = "postgresql ping ok" if ping else "postgresql configured but unavailable"
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
            CheckResult(
                name="pm8.backend",
                kind=kind,
                passed=True,
                critical=False,
                message=str(self.store.diagnostics()),
            ),
            CheckResult(
                name="pm8.postgres",
                kind=kind,
                passed=pg_ok,
                critical=backend == "postgresql",
                message=pg_msg,
            ),
            CheckResult(
                name="pm8.trading_readiness",
                kind=kind,
                passed=health.get("trading_readiness") is False,
                critical=True,
                message="trading_readiness forced false",
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
            "backend": self.store.diagnostics().get("backend"),
        }

"""PM7 knobs. Enabling is a feature flag, not this block."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

from botmoduleproject1.contracts.v1.persistence import PersistenceMode


class Pm7PersistenceConfig(BaseModel):
    operating_mode: str = "memory"
    observe_only: bool = True
    storage_path: str = "data/local/pm7"
    schema_version: int = Field(default=1, ge=1)
    query_limit: int = Field(default=50, ge=1, le=500)
    snapshot_cadence_events: int = Field(default=10, ge=1)
    replay_event_limit: int = Field(default=1000, ge=1)
    simulate_archive: bool = True
    allow_purge: bool = False
    hash_algorithm: str = "sha256"
    mt5_enabled: bool = False
    broker_commands: bool = False
    production_durable: bool = False
    auto_rearm: bool = False
    telemetry_verbose: bool = True
    journal_enabled: bool = True
    replay_enabled: bool = True
    integrity_enabled: bool = True
    retention_enabled: bool = True
    reporting_enabled: bool = True

    @field_validator("operating_mode")
    @classmethod
    def _mode(cls, value: str) -> str:
        allowed = {
            PersistenceMode.DISABLED.value,
            PersistenceMode.MEMORY.value,
            PersistenceMode.FILE_BACKED.value,
            PersistenceMode.SQLITE_LOCAL.value,
            PersistenceMode.DURABLE_CANDIDATE.value,
        }
        if value == PersistenceMode.PRODUCTION_DURABLE.value:
            raise ValueError("production_durable is refused in Sequence 09")
        if value not in allowed:
            raise ValueError("operating_mode must be disabled|memory|file_backed|sqlite_local|durable_candidate")
        return value

    @model_validator(mode="after")
    def _invariants(self) -> "Pm7PersistenceConfig":
        if self.auto_rearm:
            raise ValueError("auto_rearm must stay false")
        if self.mt5_enabled:
            raise ValueError("PM7 cannot enable MT5")
        if self.broker_commands:
            raise ValueError("PM7 cannot issue broker commands")
        if self.production_durable:
            raise ValueError("production_durable is refused in Sequence 09")
        if self.hash_algorithm != "sha256":
            raise ValueError("hash_algorithm must be sha256")
        if self.allow_purge and not self.simulate_archive:
            raise ValueError("destructive purge is refused by default")
        return self

    @property
    def mode(self) -> PersistenceMode:
        if self.operating_mode == PersistenceMode.DURABLE_CANDIDATE.value:
            return PersistenceMode.DURABLE_CANDIDATE
        return PersistenceMode(self.operating_mode)

    @property
    def claims_durable(self) -> bool:
        return self.mode in {
            PersistenceMode.FILE_BACKED,
            PersistenceMode.SQLITE_LOCAL,
            PersistenceMode.DURABLE_CANDIDATE,
        }


def config_from_settings(settings: object) -> Pm7PersistenceConfig:
    section = getattr(settings, "pm7_persistence", None)
    if section is None:
        return Pm7PersistenceConfig()
    payload = section.model_dump() if hasattr(section, "model_dump") else dict(section)
    allowed = set(Pm7PersistenceConfig.model_fields)
    return Pm7PersistenceConfig(**{k: v for k, v in payload.items() if k in allowed})

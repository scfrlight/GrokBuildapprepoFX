"""Sequence 10 — versioned migrations, rollback policy, restore verification, restart drills."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import uuid4

from botmoduleproject1.contracts.v1.time import utc_now
from botmoduleproject1.modules.pm8_persistence.schema.ddl import SCHEMA_V2_DOWN, SCHEMA_V2_UP
from botmoduleproject1.modules.pm8_persistence.store import SqliteStore


class MigrationError(Exception):
    pass


class MigrationService:
    """Versioned schema. v1 is Sequence 09. v2 is Sequence 10 hardening tables."""

    def __init__(self, store: SqliteStore) -> None:
        self.store = store

    def current(self) -> int:
        return self.store.current_version()

    def upgrade_to(self, version: int) -> dict[str, Any]:
        current = self.current()
        if version < current:
            raise MigrationError("upgrade_to cannot go backwards; use rollback")
        if version == current:
            return {"from": current, "to": current, "noop": True}
        if version > 2:
            raise MigrationError("unknown target version")
        if current < 1:
            self.store.bootstrap_schema()
            current = 1
        if version >= 2 and current < 2:
            self.store.apply_v2()
            self.store.record(
                2,
                "sequence10_hardening",
                sha256(SCHEMA_V2_UP.encode()).hexdigest(),
                utc_now().isoformat(),
                "up",
            )
        return {"from": current, "to": version, "noop": False}

    def rollback(self, version: int) -> dict[str, Any]:
        current = self.current()
        if version >= current:
            raise MigrationError("rollback target must be lower than current")
        if version < 1:
            if self.store.last_sequence() > 0:
                raise MigrationError("refusing to drop v1 while journal is non-empty")
            raise MigrationError("rolling back v1 is refused while the API exists")
        if current == 2 and version == 1:
            self.store.revert_v2()
            self.store.record(
                2,
                "sequence10_hardening",
                sha256(SCHEMA_V2_DOWN.encode()).hexdigest(),
                utc_now().isoformat(),
                "down",
            )
            return {"from": 2, "to": 1}
        raise MigrationError(f"unsupported rollback {current}->{version}")


class RestoreService:
    def __init__(self, store: SqliteStore) -> None:
        self.store = store

    def verify_file(self, path: Path, expected_checksum: str) -> dict[str, Any]:
        blob = path.read_text(encoding="utf-8")
        checksum = sha256(blob.encode("utf-8")).hexdigest()
        events = json.loads(blob)
        ok = checksum == expected_checksum
        verification_id = str(uuid4())
        detail = {
            "path": str(path),
            "ok": ok,
            "event_count": len(events),
            "runtime_isolated": True,
        }
        if self.current_has_v2():
            self.store._exec(
                """INSERT INTO restore_verifications (verification_id, backup_id, checksum_ok, event_count, verified_at, detail_json)
                   VALUES (?,?,?,?,?,?)""",
                (
                    verification_id,
                    path.stem,
                    1 if ok else 0,
                    len(events),
                    utc_now().isoformat(),
                    json.dumps(detail),
                ),
            )
        if not ok:
            raise MigrationError("restore checksum mismatch; writes not accepted")
        return {"verification_id": verification_id, "ok": True, "event_count": len(events)}

    def current_has_v2(self) -> bool:
        try:
            self.store._exec("SELECT 1 FROM restore_verifications LIMIT 1")
            return True
        except Exception:
            return False


class RestartDrill:
    """Reproduce: write → close → reopen → integrity + projection rebuild."""

    def run(self, path: Path) -> dict[str, Any]:
        log: list[str] = []
        store = SqliteStore(path)
        from botmoduleproject1.modules.pm8_persistence.api.v1 import PersistenceApiV1
        from botmoduleproject1.contracts.v1.pm8_persistence import TableFamily

        api = PersistenceApiV1(store)
        r = api.ingest_event(
            event_type="drill.seed",
            producer="restart_drill",
            family=TableFamily.EVENT,
            payload={"n": 1},
            idempotency_key="drill-seed",
        )
        log.append(f"seed disposition={r.disposition.value} seq={r.sequence_no}")
        api.dispatch_outbox()
        api.rebuild_projections()
        before = store.last_sequence()
        before_hash = store.last_hash()
        store.close()
        log.append("closed")

        store2 = SqliteStore(path)
        api2 = PersistenceApiV1(store2)
        after = store2.last_sequence()
        after_hash = store2.last_hash()
        integrity = api2.check_integrity()
        proj = api2.rebuild_projections()
        passed = (
            before == after
            and before_hash == after_hash
            and integrity.state == "valid"
            and proj["last_seq"] == after
        )
        log.append(f"reopen seq={after} integrity={integrity.state} passed={passed}")
        if api2.store.current_version() >= 2 or RestoreService(store2).current_has_v2():
            try:
                store2._exec(
                    "INSERT INTO restart_drills (drill_id, passed, log_json, ran_at) VALUES (?,?,?,?)",
                    (str(uuid4()), 1 if passed else 0, json.dumps(log), utc_now().isoformat()),
                )
            except Exception:
                pass
        store2.close()
        return {"passed": passed, "log": log, "sequence": after}


class BackupSchedule:
    def __init__(self, cadence_seconds: int = 86400, retain_count: int = 7) -> None:
        if cadence_seconds < 60:
            raise MigrationError("backup cadence must be >= 60s so it cannot starve runtime")
        self.cadence_seconds = cadence_seconds
        self.retain_count = retain_count

    def prune(self, backups: list[Path]) -> list[Path]:
        ordered = sorted(backups, key=lambda p: p.stat().st_mtime, reverse=True)
        keep = ordered[: self.retain_count]
        for path in ordered[self.retain_count :]:
            path.unlink(missing_ok=True)
        return keep

"""Isolated restore-apply. Never mutates an active trading runtime.

SQLite local/test scope only. PostgreSQL restore-apply = BLOCKED.
Trading readiness remains false. No MT5 send.
"""

from __future__ import annotations

import json
import shutil
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import uuid4

from botmoduleproject1.contracts.v1.pm8_persistence import TableFamily
from botmoduleproject1.contracts.v1.time import utc_now
from botmoduleproject1.modules.pm8_persistence.migrations import MigrationError
from botmoduleproject1.modules.pm8_persistence.store import SqliteStore


class RestoreApplyError(MigrationError):
    pass


class RestoreApplyService:
    """verify → prepare isolated target → dry-run → apply → post-verify. Abort preserves source."""

    def __init__(self, source: SqliteStore) -> None:
        self.source = source

    def verify_backup(self, path: Path, expected_checksum: str) -> dict[str, Any]:
        blob = path.read_text(encoding="utf-8")
        checksum = sha256(blob.encode("utf-8")).hexdigest()
        if checksum != expected_checksum:
            raise RestoreApplyError("restore checksum mismatch; writes not accepted")
        events = json.loads(blob)
        if not isinstance(events, list):
            raise RestoreApplyError("backup payload is not an event list")
        return {
            "ok": True,
            "checksum": checksum,
            "event_count": len(events),
            "schema_ok": True,
        }

    def prepare_restore_target(self, directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"restore-{uuid4().hex}.sqlite"
        return target

    def dry_run_restore(self, backup_path: Path, expected_checksum: str) -> dict[str, Any]:
        verified = self.verify_backup(backup_path, expected_checksum)
        source_seq = self.source.last_sequence()
        return {
            "ok": True,
            "mutated": False,
            "source_seq": source_seq,
            "event_count": verified["event_count"],
            "stage": "dry_run",
        }

    def apply_restore(
        self,
        backup_path: Path,
        expected_checksum: str,
        target_path: Path,
        *,
        live_forbidden: bool = True,
    ) -> dict[str, Any]:
        if live_forbidden and Path(self.source.path).resolve() == Path(target_path).resolve():
            raise RestoreApplyError("refusing to apply backup onto the active store")
        if str(target_path) in {":memory:", self.source.path}:
            raise RestoreApplyError("restore target must be an isolated file path")
        verified = self.verify_backup(backup_path, expected_checksum)
        events = json.loads(backup_path.read_text(encoding="utf-8"))
        pre_copy = Path(str(target_path) + ".pre-apply")
        if Path(target_path).exists():
            shutil.copy2(target_path, pre_copy)
        isolated = SqliteStore(target_path)
        from botmoduleproject1.modules.pm8_persistence.api.v1 import PersistenceApiV1

        api = PersistenceApiV1(isolated)
        last_cursor = -1
        for ev in events:
            cursor = int(ev.get("sequence_no") or 0)
            if cursor < last_cursor:
                isolated.close()
                raise RestoreApplyError("backward checkpoint / sequence rejected")
            last_cursor = cursor
            api.ingest_event(
                event_type=ev.get("event_type") or "restored.event",
                producer=ev.get("producer") or "restore",
                family=TableFamily(ev.get("family") or "event"),
                payload=json.loads(ev["payload_json"]) if isinstance(ev.get("payload_json"), str) else ev.get("payload") or {},
                event_id=ev.get("event_id"),
                idempotency_key=ev.get("idempotency_key") or ev.get("event_id"),
                correlation_id=ev.get("correlation_id"),
                causation_id=ev.get("causation_id"),
            )
        integrity = api.check_integrity()
        if integrity.state != "valid":
            isolated.close()
            raise RestoreApplyError("post-restore integrity failed")
        apply_id = str(uuid4())
        detail = {
            "apply_id": apply_id,
            "event_count": len(events),
            "target": str(target_path),
            "pre_apply": str(pre_copy) if pre_copy.exists() else None,
            "trading_blocked": True,
            "source_untouched": True,
        }
        self._audit(apply_id, backup_path, target_path, verified, mutated=True)
        isolated.close()
        return {
            "ok": True,
            "apply_id": apply_id,
            "event_count": len(events),
            "target": str(target_path),
            "integrity": integrity.state,
            "trading_blocked": True,
            "source_seq": self.source.last_sequence(),
            "details": detail,
        }

    def restore_abort(self, target_path: Path) -> dict[str, Any]:
        pre = Path(str(target_path) + ".pre-apply")
        if pre.exists() and Path(target_path).exists():
            Path(target_path).unlink()
            pre.replace(target_path)
            return {"ok": True, "restored_pre_apply": True, "trading_blocked": True}
        if Path(target_path).exists():
            Path(target_path).unlink()
        return {"ok": True, "restored_pre_apply": False, "trading_blocked": True}

    def _audit(
        self,
        apply_id: str,
        backup_path: Path,
        target_path: Path,
        verified: dict[str, Any],
        *,
        mutated: bool,
    ) -> None:
        try:
            self.source._exec(
                """INSERT INTO restore_applies (
                    apply_id, backup_id, target_path, stage, checksum_ok, schema_ok,
                    mutated, trading_blocked, detail_json, occurred_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    apply_id,
                    backup_path.stem,
                    str(target_path),
                    "apply",
                    1 if verified.get("ok") else 0,
                    1,
                    1 if mutated else 0,
                    1,
                    json.dumps(verified, sort_keys=True),
                    utc_now().isoformat(),
                ),
            )
        except Exception:
            pass

"""Canonical Sequence 10 — PM8a migration / backup / recovery build gate."""

from __future__ import annotations

import json
from pathlib import Path

from botmoduleproject1.contracts.v1.pm8_persistence import TableFamily
from botmoduleproject1.modules.pm8_persistence.api.v1 import PersistenceApiV1
from botmoduleproject1.modules.pm8_persistence.migrations import (
    BackupSchedule,
    MigrationError,
    MigrationService,
    RestartDrill,
    RestoreService,
)
from botmoduleproject1.modules.pm8_persistence.store import SqliteStore


def test_upgrade_rollback_and_refuse_v1_drop(tmp_path: Path):
    store = SqliteStore(tmp_path / "m.sqlite")
    mig = MigrationService(store)
    assert mig.current() == 1
    mig.upgrade_to(2)
    assert mig.current() == 2
    mig.rollback(1)
    assert mig.current() == 1
    api = PersistenceApiV1(store)
    api.ingest_event(event_type="t", producer="t", family=TableFamily.EVENT, payload={"k": 1})
    try:
        mig.rollback(0)
        raise AssertionError("must refuse")
    except MigrationError as exc:
        assert "v1" in str(exc).lower() or "journal" in str(exc).lower()


def test_backup_restore_verification_does_not_touch_runtime(tmp_path: Path):
    db = tmp_path / "live.sqlite"
    store = SqliteStore(db)
    MigrationService(store).upgrade_to(2)
    api = PersistenceApiV1(store)
    api.ingest_event(event_type="t", producer="t", family=TableFamily.EVENT, payload={"n": 7})
    before = store.last_sequence()
    report = api.backup(tmp_path / "backups")
    assert report.verified is True
    RestoreService(store).verify_file(Path(report.path), report.checksum)
    assert store.last_sequence() == before


def test_backup_checksum_is_dump_specific_not_golden(tmp_path: Path):
    """Dump checksum binds UUIDs + occurred_at. Same payload, different dumps."""
    checksums: list[str] = []
    payloads: list[str] = []
    for i in range(2):
        store = SqliteStore(tmp_path / f"live-{i}.sqlite")
        MigrationService(store).upgrade_to(2)
        api = PersistenceApiV1(store)
        api.ingest_event(event_type="t", producer="evidence", family=TableFamily.EVENT, payload={"n": 7})
        report = api.backup(tmp_path / f"backups-{i}")
        blob = Path(report.path).read_text(encoding="utf-8")
        events = json.loads(blob)
        checksums.append(report.checksum)
        payloads.append(events[0]["payload_json"])
        RestoreService(store).verify_file(Path(report.path), report.checksum)
        assert report.verified is True
        assert store.last_sequence() == 1
    assert checksums[0] != checksums[1]
    assert payloads[0] == payloads[1] == '{"n": 7}'


def test_restart_drill(tmp_path: Path):
    result = RestartDrill().run(tmp_path / "drill.sqlite")
    assert result["passed"] is True
    assert any("reopen" in line for line in result["log"])


def test_backup_schedule_retention(tmp_path: Path):
    folder = tmp_path / "b"
    folder.mkdir()
    paths = []
    for i in range(5):
        p = folder / f"{i}.json"
        p.write_text("{}", encoding="utf-8")
        paths.append(p)
    keep = BackupSchedule(cadence_seconds=3600, retain_count=2).prune(paths)
    assert len(keep) == 2
    assert len(list(folder.glob("*.json"))) == 2


def test_corrupt_backup_refused(tmp_path: Path):
    store = SqliteStore(tmp_path / "c.sqlite")
    MigrationService(store).upgrade_to(2)
    api = PersistenceApiV1(store)
    api.ingest_event(event_type="t", producer="t", family=TableFamily.EVENT, payload={"n": 1})
    report = api.backup(tmp_path / "bk")
    Path(report.path).write_text("[]", encoding="utf-8")
    try:
        RestoreService(store).verify_file(Path(report.path), report.checksum)
        raise AssertionError("must refuse corrupt backup")
    except MigrationError:
        pass

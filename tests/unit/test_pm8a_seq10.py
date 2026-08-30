"""Canonical Sequence 10 — PM8a migration / backup / recovery build gate."""

from __future__ import annotations

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

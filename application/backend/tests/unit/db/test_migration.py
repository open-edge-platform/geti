# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for MigrationManager's real SQLite backup/restore code paths."""

import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.db.migration import MigrationManager


def _manager(tmp_path: Path) -> MigrationManager:
    settings = SimpleNamespace(data_dir=tmp_path, database_file="geti.db")
    return MigrationManager(settings)  # type: ignore[arg-type]


def _create_db(path: Path, value: str) -> None:
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("CREATE TABLE t (v TEXT)")
        conn.execute("INSERT INTO t (v) VALUES (?)", (value,))
        conn.commit()
    finally:
        conn.close()


def _read_value(path: Path) -> str:
    conn = sqlite3.connect(str(path))
    try:
        return conn.execute("SELECT v FROM t").fetchone()[0]
    finally:
        conn.close()


class TestBackupDatabase:
    def test_returns_none_on_fresh_install(self, tmp_path: Path) -> None:
        assert _manager(tmp_path).backup_database() is None

    def test_creates_consistent_backup(self, tmp_path: Path) -> None:
        manager = _manager(tmp_path)
        _create_db(manager.database_path, "original")

        backup = manager.backup_database()

        assert backup is not None
        assert backup.exists()
        assert _read_value(backup) == "original"


class TestRestoreDatabase:
    def test_restores_original_contents(self, tmp_path: Path) -> None:
        manager = _manager(tmp_path)
        _create_db(manager.database_path, "original")
        backup = manager.backup_database()
        assert backup is not None

        # Simulate a destructive migration.
        conn = sqlite3.connect(str(manager.database_path))
        conn.execute("UPDATE t SET v = 'corrupted'")
        conn.commit()
        conn.close()
        assert _read_value(manager.database_path) == "corrupted"

        manager.restore_database(backup)

        assert _read_value(manager.database_path) == "original"

    def test_removes_stale_wal_and_shm_sidecars(self, tmp_path: Path) -> None:
        manager = _manager(tmp_path)
        _create_db(manager.database_path, "original")
        backup = manager.backup_database()
        assert backup is not None

        db_path = manager.database_path
        wal = db_path.with_name(f"{db_path.name}-wal")
        shm = db_path.with_name(f"{db_path.name}-shm")
        wal.write_bytes(b"stale")
        shm.write_bytes(b"stale")

        manager.restore_database(backup)

        assert not wal.exists()
        assert not shm.exists()


class TestInitializeDatabaseRollback:
    """Tests for the two-stage automatic rollback on a failed upgrade.

    Alembic is mocked so the orchestration can be exercised without a real
    schema: the forward upgrade fails, and the manager must (1) downgrade to the
    starting revision to revert in-script filesystem changes and (2) restore the
    database from the pre-upgrade backup.
    """

    def _prepare(self, tmp_path: Path, monkeypatch, upgrade_fails: bool) -> tuple[MigrationManager, list[str]]:
        from app.db import migration as migration_module

        manager = _manager(tmp_path)
        _create_db(manager.database_path, "original")

        calls: list[str] = []
        monkeypatch.setattr(manager, "check_connection", lambda: True)
        monkeypatch.setattr(manager, "check_migration_status", lambda: (True, "needs migration"))
        monkeypatch.setattr(manager, "get_current_revision", lambda: "start_rev")
        monkeypatch.setattr(manager, "get_alembic_config", lambda: object())
        monkeypatch.setattr(manager, "restore_database", lambda backup: calls.append("restore"))

        def fake_upgrade(_cfg, _target):
            calls.append("upgrade")
            if upgrade_fails:
                raise RuntimeError("migration exploded")

        def fake_downgrade(_cfg, target):
            calls.append(f"downgrade:{target}")

        monkeypatch.setattr(migration_module.command, "upgrade", fake_upgrade)
        monkeypatch.setattr(migration_module.command, "downgrade", fake_downgrade)
        return manager, calls

    def test_failed_upgrade_triggers_downgrade_then_restore(self, tmp_path: Path, monkeypatch) -> None:
        from app.db import MigrationFatalError

        manager, calls = self._prepare(tmp_path, monkeypatch, upgrade_fails=True)

        with pytest.raises(MigrationFatalError):
            manager.initialize_database()

        # Two-stage rollback: revert to the starting revision, then restore the DB.
        assert calls == ["upgrade", "downgrade:start_rev", "restore"]

    def test_successful_upgrade_does_not_roll_back(self, tmp_path: Path, monkeypatch) -> None:
        manager, calls = self._prepare(tmp_path, monkeypatch, upgrade_fails=False)

        assert manager.initialize_database() is True
        assert "downgrade:start_rev" not in calls
        assert "restore" not in calls

# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for MigrationManager's real SQLite backup/restore code paths."""

import sqlite3
from pathlib import Path
from types import SimpleNamespace

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
        assert _manager(tmp_path)._backup_database() is None

    def test_creates_consistent_backup(self, tmp_path: Path) -> None:
        manager = _manager(tmp_path)
        _create_db(manager.database_path, "original")

        backup = manager._backup_database()

        assert backup is not None
        assert backup.exists()
        assert _read_value(backup) == "original"

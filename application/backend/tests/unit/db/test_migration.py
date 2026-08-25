# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for MigrationManager's real SQLite backup/restore code paths."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from alembic.script.revision import ResolutionError

from app.db.migration import MigrationManager, RevisionNotFoundError


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


@contextmanager
def _mock_connect():
    yield MagicMock()


def _read_value(path: Path) -> str:
    conn = sqlite3.connect(str(path))
    try:
        return conn.execute("SELECT v FROM t").fetchone()[0]
    finally:
        conn.close()


def _mock_migration_script(current_head: str, known_revisions: set[str]) -> MagicMock:
    script = MagicMock()
    script.get_current_head.return_value = current_head

    def _get_revision(rev_id: str) -> MagicMock:
        if rev_id not in known_revisions:
            raise ResolutionError("Can't locate revision", rev_id)
        return MagicMock()

    script.get_revision.side_effect = _get_revision
    return script


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


class TestCheckMigrationStatus:
    def test_intermediate_revision_is_recognized(self, tmp_path: Path) -> None:
        """Regression test for #7355: an intermediate (non-head, non-base) revision
        must not be mistaken for an unrecognized schema revision."""
        manager = _manager(tmp_path)
        script = _mock_migration_script(current_head="head_rev", known_revisions={"base_rev", "mid_rev", "head_rev"})

        with (
            patch.object(manager, "get_alembic_config", return_value=MagicMock()),
            patch("app.db.migration.ScriptDirectory.from_config", return_value=script),
            patch("app.db.migration.db_engine.connect", side_effect=_mock_connect),
            patch("app.db.migration.migration.MigrationContext.configure") as mock_configure,
        ):
            mock_configure.return_value.get_current_revision.return_value = "mid_rev"

            needs_migration, status = manager.check_migration_status()

        assert needs_migration is True
        assert "mid_rev" in status

    def test_unknown_revision_raises(self, tmp_path: Path) -> None:
        manager = _manager(tmp_path)
        script = _mock_migration_script(current_head="head_rev", known_revisions={"base_rev", "head_rev"})

        with (
            patch.object(manager, "get_alembic_config", return_value=MagicMock()),
            patch("app.db.migration.ScriptDirectory.from_config", return_value=script),
            patch("app.db.migration.db_engine.connect", side_effect=_mock_connect),
            patch("app.db.migration.migration.MigrationContext.configure") as mock_configure,
        ):
            mock_configure.return_value.get_current_revision.return_value = "unknown_rev"

            with pytest.raises(RevisionNotFoundError):
                manager.check_migration_status()

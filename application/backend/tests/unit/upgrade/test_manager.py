# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for the upgrade orchestration (UpgradeManager)."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.db import MigrationFatalError
from app.upgrade.data_version import DATA_VERSION_FILE, read_data_version, write_data_version
from app.upgrade.manager import UpgradeManager


class FakeMigrationManager:
    """Test double for MigrationManager.
    Emulates the three outcomes of ``initialize_database``: success, a transient
    failure (returns ``False``), and a fatal failure (raises).
    """

    def __init__(self, data_dir: Path, *, result: bool = True, fatal: bool = False) -> None:
        self.database_path = data_dir / "geti.db"
        self._result = result
        self._fatal = fatal
        self.calls: list[str] = []

    def initialize_database(self) -> bool:
        self.calls.append("initialize_database")
        if self._fatal:
            raise MigrationFatalError("boom", backup_path=self.database_path.with_suffix(".bak"))
        return self._result


def _settings(tmp_path: Path, version: str) -> SimpleNamespace:
    return SimpleNamespace(data_dir=tmp_path, version=version)


def _seed_existing_db(tmp_path: Path, baseline: str = "3.0.0") -> None:
    (tmp_path / "geti.db").write_bytes(b"SQLite format 3\x00")
    write_data_version(tmp_path, baseline)


class TestUpgradeManagerRun:
    def test_transient_failure_returns_false_without_stamping(self, tmp_path: Path) -> None:
        _seed_existing_db(tmp_path, baseline="3.0.0")
        mm = FakeMigrationManager(tmp_path, result=False)
        manager = UpgradeManager(
            _settings(tmp_path, "3.1.0"),  # pyrefly: ignore[bad-argument-type]
            migration_manager=mm,  # pyrefly: ignore[bad-argument-type]
        )
        assert manager.run() is False
        assert read_data_version(tmp_path, mm.database_path) == "3.0.0"

    def test_fatal_failure_propagates_without_stamping(self, tmp_path: Path) -> None:
        _seed_existing_db(tmp_path, baseline="3.0.0")
        mm = FakeMigrationManager(tmp_path, fatal=True)
        manager = UpgradeManager(
            _settings(tmp_path, "3.1.0"),  # pyrefly: ignore[bad-argument-type]
            migration_manager=mm,  # pyrefly: ignore[bad-argument-type]
        )
        with pytest.raises(MigrationFatalError):
            manager.run()
        assert read_data_version(tmp_path, mm.database_path) == "3.0.0"

    def test_successful_upgrade_advances_recorded_version(self, tmp_path: Path) -> None:
        _seed_existing_db(tmp_path, baseline="3.0.0")
        mm = FakeMigrationManager(tmp_path, result=True)
        manager = UpgradeManager(
            _settings(tmp_path, "3.1.0"),  # pyrefly: ignore[bad-argument-type]
            migration_manager=mm,  # pyrefly: ignore[bad-argument-type]
        )
        assert manager.run() is True
        assert read_data_version(tmp_path, mm.database_path) == "3.1.0"

    def test_fresh_install_records_version(self, tmp_path: Path) -> None:
        mm = FakeMigrationManager(tmp_path, result=True)
        manager = UpgradeManager(
            _settings(tmp_path, "3.1.0"),  # pyrefly: ignore[bad-argument-type]
            migration_manager=mm,  # pyrefly: ignore[bad-argument-type]
        )
        assert manager.run() is True
        assert (tmp_path / DATA_VERSION_FILE).exists()
        assert read_data_version(tmp_path, mm.database_path) == "3.1.0"

    def test_noop_when_already_at_target_version(self, tmp_path: Path) -> None:
        _seed_existing_db(tmp_path, baseline="3.1.0")
        mm = FakeMigrationManager(tmp_path, result=True)
        manager = UpgradeManager(
            _settings(tmp_path, "3.1.0"),  # pyrefly: ignore[bad-argument-type]
            migration_manager=mm,  # pyrefly: ignore[bad-argument-type]
        )
        assert manager.run() is True
        assert read_data_version(tmp_path, mm.database_path) == "3.1.0"
        assert "initialize_database" in mm.calls

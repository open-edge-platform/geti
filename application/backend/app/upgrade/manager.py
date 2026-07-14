# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""End-to-end orchestration of an application-data upgrade.
The heavy lifting - migrating the SQLite database schema **and**, per the project
convention (see ``docs/migration-guidelines.md``), the on-disk filesystem layout
that Alembic migration scripts move in lockstep with the schema - is performed by
:class:`~app.db.migration.MigrationManager`, which also takes a pre-upgrade backup
and automatically rolls back both on failure.
:class:`UpgradeManager` wraps that with data-version bookkeeping: it records the
application version the on-disk data was last brought up to. The recorded version
is informational (the Alembic revision remains the authoritative schema/layout
version) but is useful for support, tooling and the deployment upgrade scripts to
tell which version a data directory belongs to.
"""

from pathlib import Path

from loguru import logger

from app.db import MigrationManager
from app.settings import Settings
from app.upgrade.data_version import read_data_version, write_data_version


class UpgradeManager:
    """Coordinates data migration and application-data version tracking."""

    def __init__(self, settings: Settings, migration_manager: MigrationManager | None = None) -> None:
        """Initialise the manager.
        Args:
            settings: Application settings (data directory, version, ...).
            migration_manager: Database/storage migration manager; a default one
                bound to ``settings`` is created when omitted.
        """
        self.settings = settings
        self.migration_manager = migration_manager or MigrationManager(settings)

    @property
    def data_dir(self) -> Path:
        """The application data directory."""
        return self.settings.data_dir

    def run(self) -> bool:
        """Bring the on-disk data up to the running application version.
        Returns:
            ``True`` when the data is ready to use. ``False`` signals a *transient*
            failure (e.g. the database is momentarily unreachable) that a restart
            may resolve.
        Raises:
            MigrationFatalError: for fatal, non-restartable failures. The database
                and any in-script filesystem changes have been rolled back to the
                pre-upgrade state before this is raised.
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)
        target_version = self.settings.version
        current_version = read_data_version(self.data_dir, self.migration_manager.database_path)
        logger.info(
            "Upgrade check: current data version={}, target version={}",
            current_version or "fresh install",
            target_version,
        )
        # Migrate the database + filesystem, with automatic rollback on failure.
        if not self.migration_manager.initialize_database():
            # Transient failure; let the launcher/supervisor retry on restart.
            return False
        # Record the version the data now conforms to. Skipped when unchanged so
        # we avoid needless writes on every startup.
        if current_version != target_version:
            write_data_version(self.data_dir, target_version)
            logger.info("\u2713 Application data is now at version {}", target_version)
        else:
            logger.info("Application data is already at version {}", target_version)
        return True

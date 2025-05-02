# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module is responsible for migrating the documents and binaries to the latest version after they have been imported
"""

import logging

from geti_types import CTX_SESSION_VAR, ID, Session
from iai_core.versioning import DataVersion
from migration.utils import VersionManager

from job.entities.exceptions import ProjectUpgradeFailedException

logger = logging.getLogger(__name__)


class DataMigrationUseCase:
    """
    This class is responsible for migrating the documents and binaries to the latest version after they have been
    imported
    """

    @staticmethod
    def upgrade_project_to_current_version(project_id: ID, version: DataVersion) -> None:
        """
        Upgrades the data by running the necessary migration scripts from the specified version to the current one.

        :param project_id: ID of the project to upgrade
        :param version: the data version of the project to upgrade
        """
        session: Session = CTX_SESSION_VAR.get()
        current_version = DataVersion.get_current()
        versions_to_upgrade = VersionManager.find_all_minor_releases_in_range(
            start_version=version.version_string,
            end_version=current_version.version_string,
            include_end=True,
        )
        try:
            for v in versions_to_upgrade:
                logger.info(
                    "Upgrading data of imported project '%s' to version '%s'.",
                    project_id,
                    v,
                )
                metadata = VersionManager.get_changeset_metadata_by_version(version=v)
                if metadata.skip_on_project_import:
                    logger.info(
                        "Skipped upgrade script to version '%s' as specified in the metadata.",
                        v,
                    )
                    continue
                script = VersionManager.get_migration_script_cls_by_version(version=v)
                script.upgrade_project(
                    organization_id=str(session.organization_id),
                    workspace_id=str(session.workspace_id),
                    project_id=str(project_id),
                )
        except Exception:
            logger.exception(
                "Failed to upgrade project '%s' from version '%s' to '%s'.",
                project_id,
                version.version_string,
                current_version.version_string,
            )
            raise ProjectUpgradeFailedException

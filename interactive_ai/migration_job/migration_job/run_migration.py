# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Script to migrate DB data across Geti versions"""

import argparse
import os
from datetime import datetime, timezone

from geti_logger_tools.logger_config import initialize_logger
from migration.utils.metadata import ChangesetMetadata
from migration.utils.migration_script import IMigrationScript
from migration.utils.version_manager import VersionManager
from pymongo import MongoClient

from migration_job.mongodb_upgrades_history import MigrationHistory, MigrationStepDocument
from migration_job.utils import create_mongo_client

logger = initialize_logger(__name__, use_async=False)

DEFAULT_DATABASE_NAME = "geti"


class MigrationScriptDescriptor:
    def __init__(self, filename: str, metadata: ChangesetMetadata, script: IMigrationScript, data_version: str):
        self.filename = filename
        self.metadata = metadata
        self.script = script
        self.data_version = data_version


def parse_args() -> argparse.Namespace:
    """
    Script arguments.
    """
    parser = argparse.ArgumentParser(description="A script for executing platform migration scripts.")

    parser.add_argument(
        "--dry-run",
        default=False,
        help="Only prints which scripts will be invoked",
        action="store_true",
    )
    return parser.parse_args()


class UpgradeFailedDowngradeFailed(Exception):
    """Exception for failed downgrade of migration"""


class UpgradeFailedDowngradeSuccessful(Exception):
    """Exception for successful downgrade of migration"""


class MissingDatabaseName(Exception):
    """Exception for missing mongodb database name"""


def get_all_projects(client: MongoClient) -> list[dict]:
    """
    Get all projects to upgrade
    """
    db_name = os.getenv("MONGODB_DATABASE_NAME")
    if db_name is None:
        raise MissingDatabaseName
    db = client[db_name]
    return list(db["project"].find())


def downgrade(
    script_descriptors: list,
    failed_script_index: int,
    projects: list[dict],
    failed_proj_index: int,
    data_version_before_upgrade: str,
) -> None:
    """
    Downgrade migration
    """
    failed_script_desc = script_descriptors[failed_script_index]

    # Undo the changes from the last upgrade script, the one that failed, if possible
    if failed_script_desc.metadata.supports_downgrade:
        failed_script_desc.script.downgrade_non_project_data()
        for project in projects[:failed_proj_index]:
            logger.info(
                f"Starting downgrade of project {str(project['_id'])} from version"
                f" {failed_script_desc.metadata.data_version} to previous one"
            )
            failed_script_desc.script.downgrade_project(
                organization_id=str(project["organization_id"]),
                workspace_id=str(project["workspace_id"]),
                project_id=str(project["_id"]),
            )
            logger.info(
                f"Completed downgrade of project {str(project['_id'])} from version"
                f" {failed_script_desc.metadata.data_version} to previous one"
            )
    else:
        logger.exception(
            f"Upgrade to data version {failed_script_desc.data_version} failed and downgrade is not possible"
        )
        raise UpgradeFailedDowngradeFailed

    # Undo the changes from all the previous upgrade scripts (which run successfully on all projects), in reverse order
    for script_desc in script_descriptors[failed_script_index - 1 :: -1]:
        if script_desc.metadata.supports_downgrade:
            logger.info(
                f"Starting downgrade of non-project data from version {script_desc.metadata.data_version}"
                f" to previous one"
            )
            script_desc.script.downgrade_non_project_data()
            logger.info(
                f"Completed downgrade of non-project data from version {script_desc.metadata.data_version}"
                f" to previous one"
            )
            for project in projects:
                script_desc.script.downgrade_project(
                    organization_id=str(project["organization_id"]),
                    workspace_id=str(project["workspace_id"]),
                    project_id=str(project["_id"]),
                )
                logger.info(
                    f"Completed downgrade of project {str(project['_id'])} from version"
                    f" {script_desc.metadata.data_version} to previous one"
                )
        else:
            logger.exception(
                f"Upgrade to data version {failed_script_desc.data_version} "
                f"failed and downgrade was only possible down to version {script_desc.data_version}"
            )
            raise UpgradeFailedDowngradeFailed
    logger.exception(
        f"Upgrade to data version {failed_script_desc.data_version} "
        f"failed and all data was successfully downgraded to the initial version {data_version_before_upgrade}"
    )
    raise UpgradeFailedDowngradeSuccessful


def run_migration(start_version: str, target_version: str, history: MigrationHistory, client: MongoClient) -> None:
    """
    Run migration for Geti > 2.0

    :param start_version: Data version before running the migration
    :param target_version: Data version to reach after the migration
    :param history: MigrationHistory that keeps track of previously executed migrations
    :param client: MongoDB client
    """
    curr_data_version = start_version
    intermediate_versions = VersionManager.find_all_minor_releases_in_range(
        start_version=start_version, end_version=target_version, include_end=True
    )
    logger.info(
        f"Migration from data version {start_version} to {target_version} will go through {intermediate_versions}."
    )
    script_descriptors = []
    all_projects_upgraded_successfully: bool = True
    failed_script_index: int = -1
    failed_proj_index: int = -1
    for intermediate_target_version in intermediate_versions:
        try:
            script_filename, _ = VersionManager.find_migration_script_file_by_version(intermediate_target_version)
            metadata = VersionManager.get_changeset_metadata_by_version(intermediate_target_version)
            migration_script = VersionManager.get_migration_script_cls_by_version(intermediate_target_version)
            script_descriptors.append(
                MigrationScriptDescriptor(
                    filename=script_filename,
                    metadata=metadata,
                    script=migration_script,
                    data_version=intermediate_target_version,
                )
            )
        except ValueError:
            logger.exception(f"Failed to setup migration script for version {intermediate_target_version}")
            raise
    for script_idx, script_desc in enumerate(script_descriptors):
        start_time = datetime.now(tz=timezone.utc)
        try:
            # With each data version, find and try to upgrade the individual projects
            projects = get_all_projects(client)
            for project_idx, project in enumerate(projects):
                logger.info(f"Starting upgrade of project {str(project['_id'])} to {script_desc.data_version}")
                script_desc.script.upgrade_project(
                    organization_id=str(project["organization_id"]),
                    workspace_id=str(project["workspace_id"]),
                    project_id=str(project["_id"]),
                )
                logger.info(f"Completed upgrade of project {str(project['_id'])} to {script_desc.data_version}")
            logger.info(f"Starting upgrade of non-project data to {script_desc.data_version}")
            script_desc.script.upgrade_non_project_data()
            logger.info(f"Completed upgrade of non-project data to {script_desc.data_version}")
            stop_time = datetime.now(tz=timezone.utc)
            document = MigrationStepDocument(
                filepath=script_desc.filename,
                description=script_desc.metadata.description,
                downgradability=script_desc.metadata.supports_downgrade,
                current_version=curr_data_version,
                target_version=script_desc.data_version,
                start_date=start_time,
                stop_date=stop_time,
            )
            if history.insert_document(document):
                logger.info(
                    f"The following document has been inserted into {history.COLLECTION_NAME} collection:{document}"
                )
            else:
                err_msg = (
                    f"MongoDB client failed to insert into {history.COLLECTION_NAME} collection "
                    f"the following document: {document}"
                )
                logger.error(err_msg)
                raise RuntimeError(err_msg)
            curr_data_version = script_desc.data_version
        except Exception as e:
            # something went wrong while upgrading a project with the i-th script
            logger.exception(e)
            failed_script_index = script_idx
            failed_proj_index = project_idx
            all_projects_upgraded_successfully = False
            break

    if all_projects_upgraded_successfully:
        logger.info(f"All data updated successfully to {target_version}")
    else:
        downgrade(
            script_descriptors=script_descriptors,
            failed_script_index=failed_script_index,
            failed_proj_index=failed_proj_index,
            projects=projects,
            data_version_before_upgrade=start_version,
        )


def run(dry_run: bool = False) -> None:
    """
    Validate the versions and run the migration

    :param dry_run: If true, skip the execution of the migration scripts. For test/debug purposes only.
    """
    if dry_run:
        logger.warning("Skipping migration script execution due to dry run.")
    else:
        client = create_mongo_client()
        db_name = os.getenv("MONGODB_DATABASE_NAME", DEFAULT_DATABASE_NAME)
        logger.info("=== Platform migrations job script ===")
        logger.info(f"MongoDB database: '{db_name}'")
        migration_history = MigrationHistory(client=client, db_name=db_name)
        migration_history.create_collection_if_not_exists()
        current_data_version = migration_history.get_current_data_version()
        run_migration(
            start_version=current_data_version,
            target_version=VersionManager.find_latest_version_in_changelog(),
            history=migration_history,
            client=client,
        )
        client.close()

    logger.info("Successfully finished job")


def main():  # noqa: ANN201
    """The script's entry point."""
    args = parse_args()
    run(**vars(args))


if __name__ == "__main__":
    main()

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import inspect
import json
import logging
import os
from functools import cache
from importlib import import_module, resources

from migration import changelog, metadata
from migration.utils import ChangesetMetadata, IMigrationScript

logger = logging.getLogger(__name__)


class VersionManager:
    @staticmethod
    def _find_all_versions_in_changelog() -> list[str]:
        # Assumption: files are named <int>.json (e.g. 3.json) and minor number does not matter
        return [
            f"{f.with_suffix('').name}.0"  # type: ignore[attr-defined]
            for f in resources.files(changelog).iterdir()
        ]

    @staticmethod
    def find_latest_version_in_changelog() -> str:
        """
        Find the most recent version in the changelog.

        :return: The latest version in the changelog
        """
        return max(VersionManager._find_all_versions_in_changelog(), key=lambda v_str: int(v_str.split(".")[0]))

    @staticmethod
    def find_all_minor_releases_in_range(
        start_version: str,
        end_version: str,
        include_start: bool = False,
        include_end: bool = False,
    ) -> tuple[str, ...]:
        """
        Given two release numbers, find all the Geti releases that exist between these two tags, in arithmetic order.

        Example:
        find_all_minor_releases_in_range("1.5", "2.1") -> ("1.6", "1.7", "2.0")

        :param start_version: The starting release version (exclusive by default).
        :param end_version: The ending release version (exclusive by default).
        :param include_start: Whether to include the starting version in the result (default False).
        :param include_end: Whether to include the ending version in the result (default False).
        :return: A tuple of Geti releases in arithmetic order between the start and end versions.
        """

        def convert_to_float(version: str):
            return float(version.replace("_", "."))

        def filter_version(version: float) -> bool:
            if include_start and version == _start_version:
                return True
            if include_end and version == _end_version:
                return True
            return _start_version < version < _end_version

        all_str_versions = VersionManager._find_all_versions_in_changelog()
        numeric_version_lookup = {convert_to_float(v): v for v in all_str_versions}

        # Sort and filter the versions in ascending arithmetic order
        _start_version = convert_to_float(start_version)
        _end_version = convert_to_float(end_version)
        valid_float_versions = sorted([num_v for num_v in numeric_version_lookup if filter_version(num_v)])

        # Converts back to the original string version
        return tuple(numeric_version_lookup[num_v] for num_v in valid_float_versions)

    @staticmethod
    @cache
    def find_migration_script_file_by_version(version: str) -> tuple[str, str]:
        """
        Find the file names of the migration script and its metadata for a given data version.

        :param version: Target data version
        :return: Tuple containing the names of the migration script and the corresponding metadata file
        """
        # Assumption: changesets are named <major_version>.json
        major_version = os.path.splitext(version)[0]
        try:
            changeset_json = json.loads(resources.files(changelog).joinpath(f"{major_version}.json").read_text())
        except FileNotFoundError:
            raise ValueError(f"Could not find migration script file for version '{version}'")

        try:
            script_filename = changeset_json["script"]
            metadata_filename = changeset_json["metadata"]
        except KeyError:
            logger.exception(f"Changeset for version '{version}' does not have the expected format: {changeset_json}")
            raise

        return script_filename, metadata_filename

    @staticmethod
    def get_migration_script_cls_by_version(version: str) -> IMigrationScript:
        """
        Get the MigrationScript class for a certain data version.

        :param version: Target data version
        :return: the MigrationScript class
        """
        script_file, _ = VersionManager.find_migration_script_file_by_version(version)
        script_name = script_file.split(".")[0]  # module name (w/o extension)
        module = import_module("migration.scripts." + script_name)
        for cls, path in inspect.getmembers(module, inspect.isclass):
            if script_name in str(path):
                return getattr(module, cls)
        raise ValueError(f"Could not find MigrationScript class for version '{version}'")

    @staticmethod
    def get_changeset_metadata_by_version(version: str) -> ChangesetMetadata:
        """
        Get the metadata relative to the changeset for a certain data version.

        :param version: Target data version
        :return: ChangesetMetadata object
        """
        _, metadata_file = VersionManager.find_migration_script_file_by_version(version)

        try:
            metadata_json = resources.files(metadata).joinpath(metadata_file).read_text()
        except FileNotFoundError:
            raise ValueError(f"Could not find metadata file for version '{version}'")

        return ChangesetMetadata.from_json(metadata_json)  # type: ignore[attr-defined]

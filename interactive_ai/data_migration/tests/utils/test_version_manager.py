# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import pytest

from migration.utils import VersionManager


class TestVersionManager:
    def test_find_latest_version_in_changelog(self) -> None:
        # Arrange
        all_versions = ["1.0", "2.0", "11.0", "3.0", "10.0"]
        with patch.object(VersionManager, "_find_all_versions_in_changelog", return_value=all_versions):
            # Act
            latest_version = VersionManager.find_latest_version_in_changelog()

        # Assert
        assert latest_version == "11.0"

    @pytest.mark.parametrize("include_start", [False, True])
    @pytest.mark.parametrize("include_end", [False, True])
    def test_find_all_minor_releases_in_range(self, include_start, include_end) -> None:
        # Arrange
        all_versions = ["1.1", "1.2", "1.3", "1.4", "1.5", "2.0", "2.1", "3.0", "10.0", "11.0"]
        expected_result_raw = ("1.3", "1.4", "1.5", "2.0", "2.1")
        expected_result_start_index = 0 if include_start else 1
        expected_result_end_index = None if include_end else -1
        with patch.object(VersionManager, "_find_all_versions_in_changelog", return_value=all_versions):
            # Act
            found_releases = VersionManager.find_all_minor_releases_in_range(
                start_version="1.3", end_version="2.1", include_start=include_start, include_end=include_end
            )

        # Assert
        assert found_releases == expected_result_raw[expected_result_start_index:expected_result_end_index]

    def test_load_all_migrations(self) -> None:
        """
        Run migration for Geti > 2.0
        """
        intermediate_versions = VersionManager.find_all_minor_releases_in_range(
            start_version="0_0", end_version="100000_0", include_end=False
        )
        loading_errors = {}
        for version in intermediate_versions:
            try:
                VersionManager.find_migration_script_file_by_version(version)
                VersionManager.get_changeset_metadata_by_version(version)
                VersionManager.get_migration_script_cls_by_version(version)
            except Exception as e:
                loading_errors[version] = e

        assert not loading_errors, "Not all migration scripts could be loaded"

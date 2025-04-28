# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import pytest
from bson import ObjectId
from geti_types import ID
from migration.utils import ChangesetMetadata, IMigrationScript, MongoDBConnection, VersionManager
from sc_sdk.versioning.data_version import DataVersion

from job.entities.exceptions import ProjectUpgradeFailedException
from job.usecases.data_migration_usecase import DataMigrationUseCase

TEST_DATABASE = "test_database"
TEST_DB_COLLECTION_FOO = "foo"
TEST_DB_COLLECTION_BAR = "bar"


def replace_old_field_in_doc(doc_to_update: dict) -> dict:
    doc_to_update["new_field"] = doc_to_update["old_field"]
    del doc_to_update["old_field"]
    return doc_to_update


class MockedMigrationScriptFoo(IMigrationScript):
    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        conn = MongoDBConnection()
        database = conn.client.get_database(TEST_DATABASE)
        collection = database.get_collection(name=TEST_DB_COLLECTION_FOO)
        for doc_to_update in collection.find({}):
            collection.replace_one({"_id": doc_to_update["_id"]}, replace_old_field_in_doc(doc_to_update))

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        pass


class MockedMigrationScriptBar(IMigrationScript):
    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        conn = MongoDBConnection()
        database = conn.client.get_database(TEST_DATABASE)
        collection = database.get_collection(name=TEST_DB_COLLECTION_BAR)
        for doc_to_update in collection.find({}):
            collection.replace_one({"_id": doc_to_update["_id"]}, replace_old_field_in_doc(doc_to_update))

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        pass


# Ignore type because the method from_dict is defined dynamically.
migration_metadata_foo = ChangesetMetadata.from_dict(  # type: ignore
    {
        "description": "Update some field in the 'foo' collection",
        "supports_downgrade": True,
        "skip_on_project_import": False,
        "new_collections": [],
        "updated_collections": ["foo"],
        "deprecated_collections": [],
        "affects_binary_data": False,
    }
)

# Ignore type because the method from_dict is defined dynamically.
migration_metadata_bar = ChangesetMetadata.from_dict(  # type: ignore
    {
        "description": "Update some field in the 'bar' collection",
        "supports_downgrade": True,
        "skip_on_project_import": False,
        "new_collections": [],
        "updated_collections": ["bar"],
        "deprecated_collections": [],
        "affects_binary_data": False,
    }
)


@pytest.mark.ProjectIEMsComponent
class TestDataMigrationUseCase:
    def test_upgrade_project_to_current_version(self, request, fxt_session_ctx) -> None:
        # Arrange
        project_id = ID()
        import_version = DataVersion("1.0")
        current_version = DataVersion("2.0")
        intermedia_versions = ("1.5", "2.0")
        conn = MongoDBConnection()
        database = conn.client.get_database(TEST_DATABASE)
        foo_collection = database.get_collection(name=TEST_DB_COLLECTION_FOO)
        foo_doc = {
            "_id": ObjectId(),
            "project_id": project_id,
            "old_field": "foo",
        }
        foo_collection.insert_one(foo_doc)
        bar_collection = database.get_collection(name=TEST_DB_COLLECTION_BAR)
        bar_doc = {
            "_id": ObjectId(),
            "project_id": project_id,
            "old_field": "bar",
        }
        bar_collection.insert_one(bar_doc)
        request.addfinalizer(lambda: conn.client.drop_database(TEST_DATABASE))

        # Act
        with (
            patch.object(VersionManager, "find_all_minor_releases_in_range", return_value=intermedia_versions),
            patch.object(
                VersionManager,
                "get_migration_script_cls_by_version",
                side_effect=[MockedMigrationScriptFoo, MockedMigrationScriptBar],
            ),
            patch.object(
                VersionManager,
                "get_changeset_metadata_by_version",
                side_effect=[migration_metadata_foo, migration_metadata_bar],
            ),
            patch.object(DataVersion, "get_current", return_value=current_version),
        ):
            DataMigrationUseCase.upgrade_project_to_current_version(project_id=project_id, version=import_version)

        # Assert
        assert foo_collection.find_one({"_id": foo_doc["_id"]}) == {
            "_id": foo_doc["_id"],
            "project_id": project_id,
            "new_field": "foo",
        }
        assert bar_collection.find_one({"_id": bar_doc["_id"]}) == {
            "_id": bar_doc["_id"],
            "project_id": project_id,
            "new_field": "bar",
        }

    def test_upgrade_project_to_current_version_failed(self, fxt_session_ctx):
        # Arrange
        project_id = ObjectId()
        import_version = DataVersion("1.0")

        # Act & Assert
        with (
            pytest.raises(ProjectUpgradeFailedException),
            patch.object(VersionManager, "find_all_minor_releases_in_range", return_value=["1.0"]),
            patch.object(VersionManager, "get_changeset_metadata_by_version", side_effect=ValueError),
        ):
            DataMigrationUseCase.upgrade_project_to_current_version(project_id=project_id, version=import_version)

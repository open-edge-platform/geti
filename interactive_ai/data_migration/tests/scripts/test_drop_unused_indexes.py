# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import mongomock
from pymongo import DESCENDING, IndexModel, MongoClient

from migration.scripts.drop_unused_indexes import DropUnusedIndexesMigration


class TestDropUnusedIndexesMigration:
    def test_remove_index_from_annotation_scene(self) -> None:
        # Arrange
        mock_db = mongomock.MongoClient().db
        for collection_name in DropUnusedIndexesMigration.DATASET_BASED_REPOS:
            collection = mock_db.get_collection(collection_name)
            new_indexes = [
                IndexModel([("organization_id", DESCENDING), ("location", DESCENDING)]),
                IndexModel([("dataset_id", DESCENDING)]),
            ]
            collection.create_indexes(new_indexes)

        for collection_name in DropUnusedIndexesMigration.DATASET_STORAGE_BASED_REPOS:
            collection = mock_db.get_collection(collection_name)
            new_indexes = [
                IndexModel([("organization_id", DESCENDING), ("location", DESCENDING)]),
                IndexModel([("dataset_storage_id", DESCENDING)]),
            ]
            collection.create_indexes(new_indexes)

        for collection_name in DropUnusedIndexesMigration.MODEL_STORAGE_BASED_REPO:
            collection = mock_db.get_collection(collection_name)
            new_indexes = [
                IndexModel([("organization_id", DESCENDING), ("location", DESCENDING)]),
                IndexModel([("model_storage_id", DESCENDING)]),
            ]
            collection.create_indexes(new_indexes)

        for collection_name in DropUnusedIndexesMigration.PROJECT_BASED_REPOS:
            collection = mock_db.get_collection(collection_name)
            new_indexes = [
                IndexModel([("organization_id", DESCENDING), ("location", DESCENDING)]),
                IndexModel([("project_id", DESCENDING)]),
            ]
            collection.create_indexes(new_indexes)

        for collection_name in DropUnusedIndexesMigration.SESSION_BASED_REPO:
            collection = mock_db.get_collection(collection_name)
            new_indexes = [
                IndexModel([("organization_id", DESCENDING), ("location", DESCENDING)]),
            ]
            collection.create_indexes(new_indexes)

        collection = mock_db.get_collection("model")
        new_indexes = [IndexModel([("model_status", DESCENDING)]), IndexModel([("optimization_type", DESCENDING)])]
        collection.create_indexes(new_indexes)

        collection = mock_db.get_collection("training_revision_filter")
        new_indexes = [
            IndexModel([("media_identifier.media_id", DESCENDING)]),
            IndexModel([("media_identifier.type", DESCENDING)]),
            IndexModel([("subset", DESCENDING)]),
            IndexModel([("label_ids", DESCENDING)]),
            IndexModel([("name", DESCENDING)]),
            IndexModel([("upload_date", DESCENDING)]),
        ]
        collection.create_indexes(new_indexes)

        with patch.object(MongoClient, "get_database", return_value=mock_db):
            DropUnusedIndexesMigration.upgrade_non_project_data()

        for collection_name in (
            DropUnusedIndexesMigration.DATASET_BASED_REPOS
            + DropUnusedIndexesMigration.DATASET_STORAGE_BASED_REPOS
            + DropUnusedIndexesMigration.MODEL_STORAGE_BASED_REPO
            + DropUnusedIndexesMigration.PROJECT_BASED_REPOS
            + DropUnusedIndexesMigration.SESSION_BASED_REPO
        ):
            collection = mock_db.get_collection(collection_name)
            assert collection.index_information() == {}

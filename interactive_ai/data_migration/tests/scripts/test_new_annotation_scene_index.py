# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import mongomock
from pymongo import ASCENDING, DESCENDING, IndexModel, MongoClient

from migration.scripts.new_annotation_scene_index import NewAnnotationSceneIndexMigration


class TestRemoveEmptyAnnotationScene:
    def test_remove_index_from_annotation_scene(self) -> None:
        # Arrange
        mock_db = mongomock.MongoClient().db
        annotation_scene_collection = mock_db.get_collection("annotation_scene")
        new_indexes = [
            IndexModel([("media_identifier", DESCENDING)]),
            IndexModel([("media_identifier.media_id", DESCENDING)]),
            IndexModel([("model_ids", DESCENDING)]),
            IndexModel([("kind", DESCENDING)]),
            IndexModel(
                [
                    ("dataset_storage_id", DESCENDING),
                    ("kind", DESCENDING),
                    ("media_identifier", ASCENDING),
                    ("_id", DESCENDING),
                ]
            ),
        ]
        annotation_scene_collection.create_indexes(new_indexes)

        with patch.object(MongoClient, "get_database", return_value=mock_db):
            NewAnnotationSceneIndexMigration.upgrade_non_project_data()

        assert annotation_scene_collection.index_information() == {}

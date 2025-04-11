# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

import logging
from collections.abc import Mapping
from typing import Any

from pymongo.database import Database
from pymongo.errors import OperationFailure

from migration.utils import IMigrationScript, MongoDBConnection

logger = logging.getLogger(__name__)


class DropUnusedIndexesMigration(IMigrationScript):
    DATASET_BASED_REPOS = [
        "training_revision_filter",
        "dataset_item",
    ]
    DATASET_STORAGE_BASED_REPOS = [
        "annotation_scene",
        "annotation_scene_state",
        "compiled_dataset_shard",
        "dataset",
        "dataset_storage_filter_data",
        "image",
        "media_score",
        "metadata_item",
        "pipeline_dataset_entity",
        "suspended_annotation_scenes",
        "video",
        "video_annotation_range",
    ]
    MODEL_STORAGE_BASED_REPO = [
        "model",
    ]
    PROJECT_BASED_REPOS = [
        "active_model_state",
        "annotation_template",
        "configurable_parameters",
        "dataset_storage",
        "evaluation_result",
        "label_schema",
        "model_storage",
        "task_node",
        "vps_reference_feature",
    ]
    SESSION_BASED_REPO = [
        "project",
        "auto_train_activation",
        "file_metadata",
        "job",
        "upload_operation",
        "ui_settings",
    ]

    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        pass

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        pass

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        """
        Remove old ...BasedRepo indexes with organization and localization and a non-compound project, dataset_storage,
        etc.

        We introduced new compound indexes that perform better.
        """
        db = MongoDBConnection().geti_db
        for collection_name in DropUnusedIndexesMigration.DATASET_BASED_REPOS:
            DropUnusedIndexesMigration._drop_indexes(
                db=db,
                collection_name=collection_name,
                indexes=["dataset_id_-1", "organization_id_-1_location_-1"],
            )
        for collection_name in DropUnusedIndexesMigration.DATASET_STORAGE_BASED_REPOS:
            DropUnusedIndexesMigration._drop_indexes(
                db=db,
                collection_name=collection_name,
                indexes=["dataset_storage_id_-1", "organization_id_-1_location_-1"],
            )
        for collection_name in DropUnusedIndexesMigration.MODEL_STORAGE_BASED_REPO:
            DropUnusedIndexesMigration._drop_indexes(
                db=db,
                collection_name=collection_name,
                indexes=["model_storage_id_-1", "organization_id_-1_location_-1"],
            )
        for collection_name in DropUnusedIndexesMigration.PROJECT_BASED_REPOS:
            DropUnusedIndexesMigration._drop_indexes(
                db=db,
                collection_name=collection_name,
                indexes=["project_id_-1", "organization_id_-1_location_-1"],
            )
        for collection_name in DropUnusedIndexesMigration.SESSION_BASED_REPO:
            DropUnusedIndexesMigration._drop_indexes(
                db=db,
                collection_name=collection_name,
                indexes=["organization_id_-1_location_-1"],
            )

        DropUnusedIndexesMigration._drop_indexes(
            db=db,
            collection_name="model",
            indexes=["model_status_-1", "optimization_type_-1"],
        )
        DropUnusedIndexesMigration._drop_indexes(
            db=db,
            collection_name="training_revision_filter",
            indexes=[
                "media_identifier.media_id_-1",
                "media_identifier.type_-1",
                "subset_-1",
                "label_ids_-1",
                "name_-1",
                "upload_date_-1",
            ],
        )

    @staticmethod
    def _drop_indexes(db: Database[Mapping[str, Any]], collection_name: str, indexes: list[str]) -> None:
        collection = db.get_collection(collection_name)
        for index_name in indexes:
            try:
                collection.drop_index(index_name)
                logger.info("Dropped index on %s collection: %s", collection_name, index_name)
            except OperationFailure:
                logger.warning(
                    "Could not drop index with name %s on %s collection: presumably it was dropped before.",
                    index_name,
                    collection_name,
                )

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        """No action required, indexes are automatically recreated by the repos"""

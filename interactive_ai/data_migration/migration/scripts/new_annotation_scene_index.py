# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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

from pymongo.errors import OperationFailure

from migration.utils import IMigrationScript, MongoDBConnection

logger = logging.getLogger(__name__)


class NewAnnotationSceneIndexMigration(IMigrationScript):
    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        pass

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """No action necessary because an extra field in the project doc does not hinder the backwards mapper"""

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        """
        Remove old and now redundant index

        Old index either has a better alternative index now, or was never used to begin with
        """
        db = MongoDBConnection().geti_db
        annotation_scene_collection = db.get_collection("annotation_scene")
        for index_name in [
            "media_identifier_-1",
            "media_identifier.media_id_-1",
            "kind_-1",
            "model_ids_-1",
            "dataset_storage_id_-1_kind_-1_media_identifier_1__id_-1",
        ]:
            try:
                annotation_scene_collection.drop_index(index_name)
                logger.info("Dropped index on annotation_scene collection: %s", index_name)
            except OperationFailure:
                logger.warning(
                    "Could not drop index with name %s on annotation_scene collection: "
                    "presumably it was dropped before.",
                    index_name,
                )

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        """No action required, indexes are automatically recreated by the repos"""

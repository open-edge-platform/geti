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

import pymongo.errors

from migration.utils import IMigrationScript, MongoDBConnection

logger = logging.getLogger(__name__)


AUTO_TRAIN_POLICY = "auto_train_policy"


class RemoveAutoTrainPolicyMigration(IMigrationScript):
    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        pass

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        pass

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        db = MongoDBConnection().geti_db
        ret = db.drop_collection(AUTO_TRAIN_POLICY)
        if ret["ok"]:
            logger.info(f"Dropped collection '{AUTO_TRAIN_POLICY}'")
        else:
            logger.warning(f"Collection to drop not found: '{AUTO_TRAIN_POLICY}'")

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        db = MongoDBConnection().geti_db
        try:
            # Note: indexes will be recreated dynamically when the collection is accessed
            db.create_collection(AUTO_TRAIN_POLICY)
        except pymongo.errors.CollectionInvalid:
            logger.warning(f"Attempted to recreate already existing collection: '{AUTO_TRAIN_POLICY}'")

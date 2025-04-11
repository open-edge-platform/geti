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
from uuid import UUID

from bson import ObjectId

from migration.utils import IMigrationScript, MongoDBConnection

TRAIN_VALIDATION_REMIXING_NAME = "train_validation_remixing"
TRAIN_VALIDATION_REMIXING_DOC = {
    "value": False,
    "default_value": False,
    "description": (
        "Turn on this setting to reshuffle training and validation subsets every training round. This "
        "strategy could improve the performance of the model on the testing subset, especially when there "
        "is new data added in between training rounds."
    ),
    "header": "Remix training and validation sets",
    "warning": None,
    "editable": True,
    "visible_in_ui": True,
    "affects_outcome_of": "NONE",
    "ui_rules": {"operator": "AND", "action": "DISABLE_EDITING", "type": "UI_RULES", "rules": []},
    "type": "BOOLEAN",
    "auto_hpo_state": "not_possible",
    "auto_hpo_value": None,
}

logger = logging.getLogger(__name__)


class SetTrainValidationRemixingConfigParamsMigration(IMigrationScript):
    """
    This script updates "configurable_parameters" documents relative to component "SUBSET_MANAGER" by adding
    new field 'data.train_validation_remixing' if it does not already exist.
    The new parameters is set to default value.
    """

    @classmethod
    def upgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        db = MongoDBConnection().geti_db
        config_params_collection = db.get_collection("configurable_parameters")
        res = config_params_collection.update_many(
            {
                "organization_id": UUID(organization_id),
                "workspace_id": UUID(workspace_id),
                "project_id": ObjectId(project_id),
                "entity_identifier.component": "SUBSET_MANAGER",
                f"data.{TRAIN_VALIDATION_REMIXING_NAME}": {"$exists": False},
            },
            {
                "$set": {
                    f"data.{TRAIN_VALIDATION_REMIXING_NAME}": TRAIN_VALIDATION_REMIXING_DOC,
                }
            },
        )
        logger.info(f"Updated {res.modified_count} configurable_parameters documents in project '{project_id}'")

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        # no action necessary: the presence of the new field does not cause incompatibilities with previous versions
        pass

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        pass

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        pass

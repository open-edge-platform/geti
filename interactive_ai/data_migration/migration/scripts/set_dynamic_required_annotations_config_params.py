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

USE_DYNAMIC_REQUIRED_ANNOTATIONS_FIELD_NAME = "use_dynamic_required_annotations"
REQ_NUM_IMAGES_DYNAMIC_FIELD_NAME = "required_images_auto_training_dynamic"


USE_DYNAMIC_REQUIRED_ANNOTATIONS_DOC = {
    "value": True,
    "default_value": True,
    "description": "Only applicable if auto-training is on. Set this parameter on to let the system dynamically "
    "compute the number of required annotations between training rounds based on model "
    "performance and training dataset size.",
    "header": "Dynamic required annotations",
    "warning": None,
    "editable": True,
    "visible_in_ui": True,
    "affects_outcome_of": "NONE",
    "ui_rules": {
        "operator": "AND",
        "action": "DISABLE_EDITING",
        "type": "UI_RULES",
        "rules": [],
    },
    "type": "BOOLEAN",
    "auto_hpo_state": "not_possible",
    "auto_hpo_value": None,
}

REQ_NUM_IMAGES_ADAPTIVE_DOC = {
    "value": 12,
    "default_value": 12,
    "description": "An optimal minimum number of images required for auto-training, "
    "calculated based on model performance and dataset size",
    "header": "Dynamic minimum number of images required for auto-training",
    "warning": None,
    "editable": False,
    "visible_in_ui": False,
    "affects_outcome_of": "NONE",
    "ui_rules": {
        "operator": "AND",
        "action": "DISABLE_EDITING",
        "type": "UI_RULES",
        "rules": [],
    },
    "type": "INTEGER",
    "auto_hpo_state": "not_possible",
    "auto_hpo_value": None,
    "min_value": 3,
    "max_value": 10000,
}

logger = logging.getLogger(__name__)


class SetDynamicRequiredAnnotationsConfigParamsMigration(IMigrationScript):
    """
    Script to update "configurable_parameters" documents by adding new fields 'use_dynamic_required_annotations' and
    'required_images_auto_training_dynamic' to the DATASET_COUNTER component, if they do not already exist.
    They are set to the default values.

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
                "entity_identifier.component": "DATASET_COUNTER",
                f"data.{USE_DYNAMIC_REQUIRED_ANNOTATIONS_FIELD_NAME}": {"$exists": False},
            },
            {
                "$set": {
                    f"data.{USE_DYNAMIC_REQUIRED_ANNOTATIONS_FIELD_NAME}": USE_DYNAMIC_REQUIRED_ANNOTATIONS_DOC,
                    f"data.{REQ_NUM_IMAGES_DYNAMIC_FIELD_NAME}": REQ_NUM_IMAGES_ADAPTIVE_DOC,
                }
            },
        )
        logger.info(
            f"Updated '{USE_DYNAMIC_REQUIRED_ANNOTATIONS_FIELD_NAME}' and '{REQ_NUM_IMAGES_DYNAMIC_FIELD_NAME}' "
            f"'configurable_parameters' fields of 'DATASET_COUNTER' component in project '{project_id}'."
            f" Total modified count: {res.modified_count}"
        )

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

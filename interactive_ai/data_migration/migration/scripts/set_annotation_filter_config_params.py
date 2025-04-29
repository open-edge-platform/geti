# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from uuid import UUID

from bson import ObjectId

from migration.utils import IMigrationScript, MongoDBConnection

MIN_ANNOTATION_SIZE_FIELD_NAME = "minimum_annotation_size"
MAX_NUM_ANNOTATIONS_FIELD_NAME = "maximum_number_of_annotations"
MIN_ANNOTATION_SIZE_DEFAULT_DOC = {
    "value": -1,
    "default_value": -1,
    "description": (
        "Minimum size of a shape in pixels. Any shape smaller than this will be ignored during training. "
        "Setting this to -1 disables the setting."
    ),
    "header": "Minimum annotation size",
    "warning": None,
    "editable": True,
    "visible_in_ui": True,
    "affects_outcome_of": "NONE",
    "ui_rules": {"operator": "AND", "action": "DISABLE_EDITING", "type": "UI_RULES", "rules": []},
    "type": "INTEGER",
    "auto_hpo_state": "not_possible",
    "auto_hpo_value": None,
    "min_value": -1,
    "max_value": 1000000,
}
MAX_NUM_ANNOTATIONS_DEFAULT_DOC = {
    "value": -1,
    "default_value": -1,
    "description": (
        "The maximum number of shapes that can be in an annotation. "
        "Any annotations with more shapes than this number will be ignored during training. "
        "Setting this to -1 disables the setting."
    ),
    "header": "Maximum number of shapes per annotation",
    "warning": None,
    "editable": True,
    "visible_in_ui": True,
    "affects_outcome_of": "NONE",
    "ui_rules": {"operator": "AND", "action": "DISABLE_EDITING", "type": "UI_RULES", "rules": []},
    "type": "INTEGER",
    "auto_hpo_state": "not_possible",
    "auto_hpo_value": None,
    "min_value": -1,
    "max_value": 10000,
}

logger = logging.getLogger(__name__)


class SetAnnotationFilterConfigParamsMigration(IMigrationScript):
    """
    This script updates "configurable_parameters" documents relative to component "PIPELINE_DATASET_MANAGER" by adding
    new fields 'data.minimum_annotation_size' and 'data.maximum_number_of_annotations' if they do not already exist.
    The two new parameters are set to default values.
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
                "entity_identifier.component": "PIPELINE_DATASET_MANAGER",
                f"data.{MIN_ANNOTATION_SIZE_FIELD_NAME}": {"$exists": False},
            },
            {
                "$set": {
                    f"data.{MIN_ANNOTATION_SIZE_FIELD_NAME}": MIN_ANNOTATION_SIZE_DEFAULT_DOC,
                    f"data.{MAX_NUM_ANNOTATIONS_FIELD_NAME}": MAX_NUM_ANNOTATIONS_DEFAULT_DOC,
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

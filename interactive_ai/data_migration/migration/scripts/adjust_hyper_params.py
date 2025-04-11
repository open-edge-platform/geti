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

logger = logging.getLogger(__name__)


class AdjustHyperParamsMigration(IMigrationScript):
    """
    Script to update "configurable_parameters" documents. Descriptions/headers of training related fields are updated
    and the "early_stop_iteration_patience" parameter is removed.

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
                "entity_identifier.type": "HYPER_PARAMETERS",
                "data.learning_parameters.early_stop_iteration_patience": {"$exists": True},
            },
            {
                "$set": {
                    "data.learning_parameters.num_iters.header": "Number of training epochs",
                    "data.learning_parameters.num_iters.description": "Maximum number of epochs to train a model. "
                    "Increasing this value may result in longer "
                    "training, but potentially in a more robust model"
                    ". Note, if the early stopping is enabled, the "
                    "actual number of epochs may be less than this "
                    "value.",
                    "data.learning_parameters.auto_num_workers.description": "Adapt number of workers according to "
                    "current hardware status automatically.",
                },
                "$unset": {"data.learning_parameters.early_stop_iteration_patience": ""},
            },
        )
        logger.info(f"Total modified count: {res.modified_count}")

    @classmethod
    def downgrade_project(cls, organization_id: str, workspace_id: str, project_id: str) -> None:
        """Not necessary. The deleted field will fall back to a default value and the updated text can stay."""

    @classmethod
    def downgrade_non_project_data(cls) -> None:
        pass

    @classmethod
    def upgrade_non_project_data(cls) -> None:
        pass

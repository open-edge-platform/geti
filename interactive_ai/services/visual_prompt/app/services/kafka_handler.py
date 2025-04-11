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
from functools import lru_cache

from repos.reference_feature_repo import ReferenceFeatureRepo

from geti_kafka_tools import BaseKafkaHandler, KafkaRawMessage, TopicSubscription
from geti_types import ID, DatasetStorageIdentifier, ProjectIdentifier, Singleton
from sc_sdk.algorithms.visual_prompting import VISUAL_PROMPTING_MODEL_TEMPLATE_ID
from sc_sdk.entities.label_schema import LabelSchema, LabelSchemaView, NullLabelSchema
from sc_sdk.entities.model import NullModel
from sc_sdk.entities.model_template import TaskType
from sc_sdk.repos import (
    DatasetRepo,
    EvaluationResultRepo,
    LabelSchemaRepo,
    ModelRepo,
    ModelStorageRepo,
    ProjectRepo,
    TaskNodeRepo,
)
from sc_sdk.session.session_propagation import setup_session_kafka

logger = logging.getLogger(__name__)


class VPSKafkaHandler(BaseKafkaHandler, metaclass=Singleton):
    """KafkaHandler for project-ie-related workflows without a well-defined use case"""

    def __init__(self) -> None:
        super().__init__(group_id="vps_consumer")

    @property
    def topics_subscriptions(self) -> list[TopicSubscription]:
        return [
            TopicSubscription(topic="project_updates", callback=self.on_project_updated),
            TopicSubscription(topic="project_deletions", callback=self.on_project_deleted),
        ]

    @staticmethod
    @setup_session_kafka
    def on_project_updated(raw_message: KafkaRawMessage) -> None:
        """
        When a project is updated, we need to check if any labels were deleted and delete the corresponding
        reference features to ensure that VPS does not return predictions for the deleted label during inference.
        """
        value: dict = raw_message.value
        project_identifier = ProjectIdentifier(
            workspace_id=ID(value["workspace_id"]),
            project_id=ID(value["project_id"]),
        )
        task_ids = TaskNodeRepo(project_identifier).get_trainable_task_ids()
        latest_label_schema_per_task = {
            task_id: VPSKafkaHandler._get_latest_label_schema_for_task(project_identifier, task_node_id=task_id)
            for task_id in task_ids
        }

        # Since ModelAPI uses an index-based representation for labels, deleting labels can cause indexing conflicts.
        # Therefore, it's better to delete all reference features and re-learn them from scratch.
        model_storage_repo = ModelStorageRepo(project_identifier)
        model_storages = model_storage_repo.get_all(
            extra_filter={"model_template_id": VISUAL_PROMPTING_MODEL_TEMPLATE_ID}
        )
        for model_storage in model_storages:
            if model_storage.model_template.task_type is not TaskType.VISUAL_PROMPTING:
                logger.warning(
                    "Skipping model storage `%s` as it is not a visual prompting model storage", model_storage.id_
                )
                continue

            latest_label_schema = latest_label_schema_per_task[model_storage.task_node_id]
            model_repo = ModelRepo(model_storage.identifier)
            sam_model = model_repo.get_one()
            if not isinstance(sam_model, NullModel):
                is_label_schema_in_sync = VPSKafkaHandler._compare_labels_sync_status(
                    project_identifier=project_identifier,
                    label_schema_1=latest_label_schema,
                    label_schema_id_2=sam_model.label_schema_id,
                )
                if not is_label_schema_in_sync:
                    project_repo = ProjectRepo()
                    project = project_repo.get_by_id(project_identifier.project_id)
                    train_dataset_storage_identifier = DatasetStorageIdentifier(
                        workspace_id=project_identifier.workspace_id,
                        project_id=project_identifier.project_id,
                        dataset_storage_id=project.training_dataset_storage_id,
                    )
                    ref_feat_repo = ReferenceFeatureRepo(project_identifier)
                    eval_result_repo = EvaluationResultRepo(project_identifier)
                    dataset_repo = DatasetRepo(train_dataset_storage_identifier)
                    ref_feat_repo.delete_all_by_task_id(task_id=model_storage.task_node_id)
                    eval_result_repo.delete_all_by_model_id(sam_model.id_)
                    dataset_repo.delete_by_id(sam_model.train_dataset_id)
                    model_repo.delete_all()
                    model_storage_repo.delete_by_id(model_storage.id_)
                    logger.info(
                        "Removed all reference features and visual prompting model for task ID %s in project ID %s"
                        " due to label schema mismatch.",
                        model_storage.task_node_id,
                        project_identifier.project_id,
                    )

    @staticmethod
    @setup_session_kafka
    def on_project_deleted(raw_message: KafkaRawMessage) -> None:
        """
        When a project is deleted, delete all reference features
        """
        value: dict = raw_message.value
        project_identifier = ProjectIdentifier(
            workspace_id=ID(value["workspace_id"]),
            project_id=ID(value["project_id"]),
        )
        ref_feat_repo = ReferenceFeatureRepo(project_identifier)
        ref_feat_repo.delete_all()
        logger.info("Removed all reference features for deleted project ID %s", project_identifier.project_id)

    @staticmethod
    @lru_cache(maxsize=8)
    def _compare_labels_sync_status(
        project_identifier: ProjectIdentifier,
        label_schema_1: LabelSchema,
        label_schema_id_2: ID,
    ) -> bool:
        """
        Checks if two LabelSchemas are in sync.

        Objects are in sync if their IDs match, or their label IDs match.
        Sync is not dependent on label attributes such as color or hotkey.

        :param project_identifier: Identifier of the project containing the LabelSchemas
        :param label_schema_1: the first LabelSchema
        :param label_schema_id_2: ID of the second LabelSchema
        :return: True if objects are in sync, False otherwise
        """
        if label_schema_1.id_ == label_schema_id_2:  # fast path for identity
            return True

        repo = LabelSchemaRepo(project_identifier)
        label_schema_2 = repo.get_by_id(label_schema_id_2)
        label_groups_1 = label_schema_1.get_groups(include_empty=True)
        label_groups_2 = label_schema_2.get_groups(include_empty=True)

        if len(label_groups_1) != len(label_groups_2):  # fast path for groups added/removed
            return False

        # General case: verify that the label groups and their labels match
        group_to_labels_1 = {group.name: {label.id_ for label in group.labels} for group in label_groups_1}
        group_to_labels_2 = {group.name: {label.id_ for label in group.labels} for group in label_groups_2}
        return group_to_labels_1 == group_to_labels_2

    @staticmethod
    def _get_latest_label_schema_for_task(project_identifier: ProjectIdentifier, task_node_id: ID) -> LabelSchemaView:
        """
        Get the latest LabelSchemaView for a given task node.

        The schema is loaded from the repo.

        :param project_identifier: Identifier of the project relative to the label schema
        :param task_node_id: ID of the task linked with the label schema view to retrieve
        :raises: RuntimeError if no schema view is found in the repo for the task
        :return: LabelSchemaView object
        """
        latest_schema_view = LabelSchemaRepo(project_identifier).get_latest_view_by_task(task_node_id=task_node_id)
        if isinstance(latest_schema_view, NullLabelSchema):
            raise RuntimeError(
                f"Could not find LabelSchemaView for task with ID {task_node_id} of project `{project_identifier}`",
            )
        return latest_schema_view

# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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


"""
This module contains the MissingAnnotationsHelper, a helper class to obtain the missing annotations for a task.
"""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from communication.exceptions import LabelNotFoundException
from coordination.dataset_manager.dataset_counter_config import (
    AnomalyDatasetCounterConfig,
    ClassificationDatasetCounterConfig,
    DatasetCounterConfig,
    KeypointDetectionCounterConfig,
)
from entities.dataset_item_count import DatasetItemCount, LabelData, NullDatasetItemCount
from service.label_schema_service import LabelSchemaService
from storage.repos import DatasetItemCountRepo

from geti_types import ID, DatasetStorageIdentifier, ProjectIdentifier
from sc_sdk.configuration.elements.component_parameters import ComponentParameters, ComponentType
from sc_sdk.entities.model_template import TaskType
from sc_sdk.entities.task_node import TaskNode
from sc_sdk.repos import ConfigurableParametersRepo

if TYPE_CHECKING:
    from sc_sdk.configuration.elements.configurable_parameters import ConfigurableParameters

REQUIRED_ANOMALOUS_IMAGES_FIRST_TRAINING = 3
REQUIRED_ANNOTATIONS_MANUAL_TRAINING = 3

logger = logging.getLogger(__name__)


@dataclass
class MissingAnnotations:
    """
    A dataclass used to store information about the missing annotations for a task.

    total_missing_annotations_auto_training: Number of total missing annotations for auto-training for the task
    total_missing_annotations_manual_training: Number of total missing annotations for manual training for the task
    missing_annotations_per_label: Number of missing annotations per label for the task
    task_label_data: LabelData dataclass that stores label information for the task
    n_new_annotations: Number of annotations added for the task since the last training round
    """

    total_missing_annotations_auto_training: int
    total_missing_annotations_manual_training: int
    missing_annotations_per_label: dict[ID, int]
    task_label_data: list[LabelData]
    n_new_annotations: int


class MissingAnnotationsHelper:
    @staticmethod
    def get_missing_annotations_for_task(
        dataset_storage_identifier: DatasetStorageIdentifier,
        task_node: TaskNode,
    ) -> MissingAnnotations:
        """
        Obtain the number of missing annotations for a task. This is done by comparing the required annotations
        (which are in the dataset counter configuration) with the count stored in the DatasetItemCount.
        The missing annotations are counted differently depending on whether the task is an anomaly task.

        :param dataset_storage_identifier: Identifier of the training dataset storage for the project
        :param task_node: TaskNode to fetch missing annotations for
        :return: MissingAnnotations object that describes the missing annotations before training can be started.
        """
        config_type: type[ConfigurableParameters]
        if task_node.task_properties.is_anomaly:
            config_type = AnomalyDatasetCounterConfig
        elif task_node.task_properties.task_type == TaskType.CLASSIFICATION:
            config_type = ClassificationDatasetCounterConfig
        elif task_node.task_properties.task_type == TaskType.KEYPOINT_DETECTION:
            config_type = KeypointDetectionCounterConfig
        else:
            config_type = DatasetCounterConfig

        project_identifier = ProjectIdentifier(
            workspace_id=dataset_storage_identifier.workspace_id,
            project_id=dataset_storage_identifier.project_id,
        )
        config_param_repo = ConfigurableParametersRepo(project_identifier)
        config = config_param_repo.get_or_create_component_parameters(
            data_instance_of=config_type,
            component=ComponentType.DATASET_COUNTER,
            task_id=task_node.id_,
        )
        dataset_item_count_repo = DatasetItemCountRepo(dataset_storage_identifier)
        dataset_item_count = dataset_item_count_repo.get_by_id(id_=task_node.id_)
        if isinstance(dataset_item_count, NullDatasetItemCount):
            # If the dataset item count is not ready yet, create an ephemeral empty dataset count. This dataset count
            # should not be saved, to avoid race conditions - the dataset counter is responsible for maintaining the
            # correct count.
            task_labels = LabelSchemaService.get_latest_labels_for_task(
                project_identifier=project_identifier,
                task_node_id=task_node.id_,
                include_empty=False,
            )
            dataset_item_count = DatasetItemCount(
                task_node_id=task_node.id_,
                task_label_data=[LabelData.from_label(label) for label in task_labels],
                n_dataset_items=0,
                n_items_per_label={label.id_: 0 for label in task_labels},
                unassigned_dataset_items=[],
            )
            logger.warning(
                "User requested project status information, but there was no dataset item count present in "
                "the database."
            )

        if task_node.task_properties.is_anomaly:
            required_annotations = MissingAnnotationsHelper._get_missing_annotations_anomaly_task(
                dataset_item_count=dataset_item_count,
                config=config,
            )
        else:
            required_annotations = MissingAnnotationsHelper._get_missing_annotations_non_anomaly_task(
                dataset_item_count=dataset_item_count,
                config=config,
            )
        return required_annotations

    @staticmethod
    def _get_missing_annotations_non_anomaly_task(
        dataset_item_count: DatasetItemCount,
        config: ComponentParameters,
    ) -> MissingAnnotations:
        """
        Compute the missing annotations for a non-anomaly task.

        If there is a label constraint, compare the number of required images with the number of items for every
        label and add those to the missing_annotations_per_label

        The total required number is the maximum of the following values:
        - The difference between the required number for initial training and the actual number of dataset items
        - If there is a label constraint, the sum of all the items that are missing for all the labels to start
        initial training
        - If we are checking for auto-training, the difference between the number of new items and the number of items
        required for auto-retraining

        :param dataset_item_count: Current dataset item count
        :param config: Configuration for the dataset counter
        :return: MissingAnnotations object that describes the missing annotations before training can be started.
        """
        # If there are assigned dataset items, that means we are retraining
        retraining = dataset_item_count.n_dataset_items > len(dataset_item_count.unassigned_dataset_items)

        required_images = config.required_images_auto_training

        # Create a missing_annotations_per_label, that will be used to enforce the label constraint if it is enabled
        missing_annotations_per_label: dict[ID, int] = {}
        if config.label_constraint_first_training and not retraining:
            for label_id, n_items in dataset_item_count.n_items_per_label.items():
                n_missing_for_label = max(required_images - n_items, 0)
                if n_missing_for_label > 0:
                    # only add item to dict if label is missing annotations
                    missing_annotations_per_label[label_id] = n_missing_for_label

        required_images_auto_training = config.required_images_auto_training
        use_dynamic_required_annotations = getattr(config, "use_dynamic_required_annotations", True)

        if use_dynamic_required_annotations:
            dynamic_num_images = config.required_images_auto_training_dynamic
            # The dynamic number of annotations is valid only if it is higher than the default threshold
            if dynamic_num_images is not None and dynamic_num_images > required_images_auto_training:
                required_images_auto_training = dynamic_num_images

        if retraining:
            # For auto-retraining, check that the number of new annotations is higher than the required number
            missing_annotations_auto_training = max(
                required_images_auto_training - len(dataset_item_count.unassigned_dataset_items),
                0,
            )

        else:
            # If not re-training, dynamic number of annotations is not used
            missing_annotations_auto_training = max(
                sum(missing_annotations_per_label.values()),
                config.required_images_auto_training - dataset_item_count.n_dataset_items,
                0,
            )

        # Manual training requires a minimum of 3 dataset items, regardless of
        # whether these are old or new
        missing_annotations_manual_training = max(
            REQUIRED_ANNOTATIONS_MANUAL_TRAINING - dataset_item_count.n_dataset_items,
            0,
        )

        return MissingAnnotations(
            total_missing_annotations_auto_training=missing_annotations_auto_training,
            total_missing_annotations_manual_training=missing_annotations_manual_training,
            missing_annotations_per_label=missing_annotations_per_label,
            task_label_data=dataset_item_count.task_label_data,
            n_new_annotations=len(dataset_item_count.unassigned_dataset_items),
        )

    @staticmethod
    def _get_missing_annotations_anomaly_task(
        dataset_item_count: DatasetItemCount,
        config: ComponentParameters,
    ) -> MissingAnnotations:
        """
        Compute the missing annotations for an anomaly task.
        For anomaly tasks, the required number of anomalous annotations for first training are pre-set.

        :param dataset_item_count: Current dataset item count
        :param config: Configuration for the dataset counter
        :return: MissingAnnotations object that describes the missing annotations before training can be started.
        """
        required_total_annotations = config.required_images_auto_training
        required_anomalous_annotations = REQUIRED_ANOMALOUS_IMAGES_FIRST_TRAINING

        normal_label = next(
            (label for label in dataset_item_count.task_label_data if not label.is_anomalous),
            None,
        )
        anomalous_label = next(
            (label for label in dataset_item_count.task_label_data if label.is_anomalous),
            None,
        )
        if normal_label is None or anomalous_label is None:
            raise LabelNotFoundException(
                message=f"Failed to find both a normal and an anomalous label for anomaly task with "
                f"ID {dataset_item_count.id_}."
            )
        missing_annotations_normal_label = max(
            required_total_annotations
            - required_anomalous_annotations
            - dataset_item_count.n_items_per_label[normal_label.id_],
            0,
        )
        missing_annotations_anomalous_label = max(
            required_anomalous_annotations - dataset_item_count.n_items_per_label[anomalous_label.id_],
            0,
        )
        missing_annotations_per_label = {
            normal_label.id_: missing_annotations_normal_label,
            anomalous_label.id_: missing_annotations_anomalous_label,
        }
        missing_annotations_manual_training = sum(missing_annotations_per_label.values())
        if dataset_item_count.n_dataset_items > len(dataset_item_count.unassigned_dataset_items):
            missing_annotations_auto_training = max(
                sum(missing_annotations_per_label.values()),
                required_total_annotations - len(dataset_item_count.unassigned_dataset_items),
            )
        else:
            missing_annotations_auto_training = sum(missing_annotations_per_label.values())
        return MissingAnnotations(
            total_missing_annotations_auto_training=missing_annotations_auto_training,
            total_missing_annotations_manual_training=missing_annotations_manual_training,
            missing_annotations_per_label=missing_annotations_per_label,
            task_label_data=dataset_item_count.task_label_data,
            n_new_annotations=len(dataset_item_count.unassigned_dataset_items),
        )

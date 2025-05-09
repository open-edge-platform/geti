# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines commands to create task train dataset"""

import logging

from geti_telemetry_tools import unified_tracing
from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.datasets import Dataset, NullDataset
from iai_core.entities.project import Project
from iai_core.entities.task_node import TaskNode
from iai_core.repos.dataset_entity_repo import PipelineDatasetRepo
from jobs_common.commands.create_dataset_command import CreateDatasetCommand
from jobs_common.exceptions import DatasetCreationFailedException
from jobs_common.utils.dataset_helpers import DatasetHelpers

logger = logging.getLogger(__name__)


class CreateTaskTrainDatasetCommand(CreateDatasetCommand):
    """
    Command to create a train dataset for a task

    :param project: project containing dataset storage
    :param dataset_storage: dataset storage containing media and annotations
    :param task_node: Task containing the command
    :param max_training_dataset_size: maximum training dataset size
    :param reshuffle_subsets: Whether to reassign/shuffle all the items to subsets including Test set from scratch
    """

    def __init__(
        self,
        project: Project,
        dataset_storage: DatasetStorage,
        task_node: TaskNode,
        max_training_dataset_size: int | None = None,
        reshuffle_subsets: bool = False,
    ) -> None:
        super().__init__(project, dataset_storage)
        self.task_node = task_node
        self.dataset: Dataset = NullDataset()
        self.max_training_dataset_size = max_training_dataset_size
        self.reshuffle_subsets = reshuffle_subsets

    @unified_tracing
    def execute(self) -> None:
        """
        Create the dataset.

        :raises DatasetCreationCommandFailedException: if the dataset cannot be created
        """
        logger.info(
            "Creating the training dataset for task %s (ID %s)",
            self.task_node.title,
            self.task_node.id_,
        )
        try:
            pipeline_dataset_entity = PipelineDatasetRepo.get_or_create(self.dataset_storage.identifier)
            task_dataset_entity = pipeline_dataset_entity.task_datasets[self.task_node.id_]
            self.dataset = DatasetHelpers.construct_and_save_train_dataset_for_task(
                task_dataset_entity=task_dataset_entity,
                project_id=self.project.id_,
                task_node=self.task_node,
                dataset_storage=self.dataset_storage,
                max_training_dataset_size=self.max_training_dataset_size,
                reshuffle_subsets=self.reshuffle_subsets,
            )
        except Exception as exc:
            logger.exception(
                "Could not create the training dataset for task `%s`",
                self.task_node.title,
            )
            raise DatasetCreationFailedException from exc

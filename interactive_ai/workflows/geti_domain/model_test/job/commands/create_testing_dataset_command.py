# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines commands to create datasets"""

import logging

from geti_types import ID
from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.datasets import Dataset, NullDataset
from iai_core.entities.project import Project
from iai_core.repos import DatasetRepo
from jobs_common.commands.create_dataset_command import CreateDatasetCommand
from jobs_common.exceptions import DatasetCreationFailedException
from jobs_common.utils.annotation_filter import AnnotationFilter
from jobs_common.utils.dataset_helpers import DatasetHelpers

logger = logging.getLogger(__name__)


class CreateTaskTestingDatasetCommand(CreateDatasetCommand):
    """
    Create a testing dataset from all annotated media in dataset storage for specific task node

    :param project: project containing dataset storage
    :param dataset_storage: dataset storage containing media and annotations
    :param task_node_id: ID of the task node for which to create the dataset
    """

    def __init__(
        self,
        project: Project,
        dataset_storage: DatasetStorage,
        task_node_id: ID,
        min_annotation_size: int | None = None,
        max_number_of_annotations: int | None = None,
    ) -> None:
        super().__init__(project, dataset_storage)
        self.task_node_id = task_node_id
        self.dataset: Dataset = NullDataset()
        self.min_annotation_size = min_annotation_size
        self.max_number_of_annotations = max_number_of_annotations

    def execute(self) -> None:
        try:
            create_new_annotations = self.max_number_of_annotations is not None or self.min_annotation_size is not None

            self.dataset = DatasetHelpers.construct_testing_dataset(
                project=self.project,
                dataset_storage=self.dataset_storage,
                task_node_id=self.task_node_id,
                create_new_annotations=create_new_annotations,
            )

            AnnotationFilter.apply_annotation_filters(
                dataset=self.dataset,
                max_number_of_annotations=self.max_number_of_annotations,
                min_annotation_size=self.min_annotation_size,
            )
            dataset_repo = DatasetRepo(self.dataset_storage.identifier)
            dataset_repo.save_deep(self.dataset)
        except Exception as exc:
            logger.exception(
                "Could not create an evaluation dataset from dataset storage '%s' for task node '%s' ",
                self.dataset_storage.id_,
                self.task_node_id,
            )
            raise DatasetCreationFailedException from exc

    def get_message(self) -> str:
        return "Constructing test dataset"

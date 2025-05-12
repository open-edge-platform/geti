# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the interface of commands to compute performance metrics."""

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING

from iai_core.entities.datasets import Dataset
from iai_core.entities.model_test_result import ModelTestResult
from iai_core.entities.project import Project
from iai_core.repos import MediaScoreRepo, ModelTestResultRepo
from jobs_common.commands.interfaces.command import ICommand
from jobs_common.exceptions import CommandInitializationFailedException

if TYPE_CHECKING:
    from iai_core.entities.label_schema import LabelSchema

logger = logging.getLogger(__name__)


class ComputePerformanceICommand(ICommand):
    """
    Interface for a compute performance command
    """

    def __init__(self, project: Project, model_test_result: ModelTestResult) -> None:
        super().__init__()
        self.project = project
        self.model_test_result = model_test_result
        self.dataset_storage = self.model_test_result.get_dataset_storages()[0]
        (
            self.ground_truth_dataset,
            self.prediction_dataset,
        ) = self.load_and_sort_gt_and_pred_datasets()
        self.model = self.model_test_result.get_model()
        self.task_label_schema = self.model.get_label_schema()
        self.project_label_schema: LabelSchema = self.task_label_schema.parent_schema  # type: ignore
        self.label_ids_without_empty = self.task_label_schema.get_label_ids(False)
        self.label_ids_with_empty = self.task_label_schema.get_label_ids(True)
        self.empty_label_ids = set(self.label_ids_with_empty) - set(self.label_ids_without_empty)
        self.model_test_result_repo: ModelTestResultRepo = ModelTestResultRepo(project.identifier)
        self.media_score_repo = MediaScoreRepo(self.dataset_storage.identifier)

    def load_and_sort_gt_and_pred_datasets(self) -> tuple[Dataset, Dataset]:
        """
        Load the ground truth and prediction datasets and sort their items by media ID.
        :return: ground truth Dataset, prediction Dataset
        """
        gt_dataset = self.model_test_result.ground_truth_dataset
        pred_dataset = self.model_test_result.prediction_dataset

        if len(gt_dataset) == 0:
            raise CommandInitializationFailedException("Ground truth dataset contains no items.")
        if len(gt_dataset) != len(pred_dataset):
            raise CommandInitializationFailedException(
                "Ground truth dataset and prediction dataset have different lengths."
            )

        # Sort
        gt_dataset.sort_items()
        pred_dataset.sort_items()

        return gt_dataset, pred_dataset

    @abstractmethod
    def execute(self) -> None:
        """
        Compute the performance
        """

    def get_message(self) -> str:
        """
        :return: message about performance computation
        """
        return "Computing performance"

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the PerformanceMetric entities"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum, auto

from geti_types import MediaIdentifierEntity
from iai_core.entities.datasets import Dataset
from iai_core.entities.label_schema import LabelSchema
from iai_core.entities.metrics import Performance, ScoreMetric

from jobs_common.utils.progress_helper import noop_progress_callback


class PerformanceMetric(ABC):
    """
    Abstract base class representing a model's performance metric over a given dataset.

    Concrete classes implementing this interface should provide specific performance metrics and methods
    for computing them based on an EvaluationResult.

    :param ground_truth_dataset: dataset with ground truth annotations
    :param prediction_dataset: dataset with predictions from model inference
    :param label_schema: label schema of the model used for inference
    :param progress_callback: callback function to update progress
    """

    def __init__(
        self,
        ground_truth_dataset: Dataset,
        prediction_dataset: Dataset,
        label_schema: LabelSchema,
        progress_callback: Callable[[float, str], None] = noop_progress_callback,
        progress_total_steps: int | None = None,
    ):
        self._label_schema = label_schema
        self._gt_dataset = ground_truth_dataset
        self._prediction_dataset = prediction_dataset
        self.progress_callback = progress_callback
        self.progress = 0
        self.progress_total_steps = (
            progress_total_steps if progress_total_steps is not None else len(ground_truth_dataset)
        )

    @property
    def label_schema(self) -> LabelSchema:
        """Returns the label schema of the evaluated model"""
        return self._label_schema

    @property
    def gt_dataset(self) -> Dataset:
        """Returns the ground truth dataset from the evaluation result"""
        return self._gt_dataset

    @property
    def prediction_dataset(self) -> Dataset:
        """Returns the prediction dataset from the evaluation result"""
        return self._prediction_dataset

    @abstractmethod
    def get_performance(self) -> Performance:
        """
        Retrieves the performance metric for the model.

        :return: A Performance object representing the performance.
        """
        raise NotImplementedError

    @abstractmethod
    def get_per_media_scores(self) -> dict[MediaIdentifierEntity, list[ScoreMetric]]:
        """
        Retrieves scores calculated for each media item in the dataset. Includes:
            - the overall score
            - the per-label score related to the media

        This method is useful for creating MediaScores entities.

        :return: a dictionary mapping a media identifier to its ScoreMetric.
        """
        raise NotImplementedError

    @abstractmethod
    def get_per_label_scores(self) -> tuple[ScoreMetric, ...]:
        """
        Retrieves scores calculated for each label in the dataset label schema.

        This method is useful for creating ModelTestResult entities

        :return: sequence of ScoreMetric entities with score value and label ID
        """
        raise NotImplementedError

    def update_progress(self) -> None:
        """
        Updates the progress of the evaluation process.

        This method should be called periodically during the evaluation process
        to update the progress of the evaluation process.
        """
        self.progress = min(self.progress + 1, self.progress_total_steps)
        self.progress_callback(self.progress / self.progress_total_steps, "Computing metrics")


class MetricAverageMethod(Enum):
    """Defines the metrics averaging method."""

    MICRO = auto()
    MACRO = auto()

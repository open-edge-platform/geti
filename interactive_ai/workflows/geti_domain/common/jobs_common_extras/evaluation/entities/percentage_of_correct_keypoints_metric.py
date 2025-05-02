# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging
from collections import defaultdict

import numpy as np
from geti_types import MediaIdentifierEntity
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.datasets import Dataset
from iai_core.entities.label import Label
from iai_core.entities.label_schema import LabelSchema
from iai_core.entities.metrics import (
    BarChartInfo,
    BarMetricsGroup,
    ColorPalette,
    MetricsGroup,
    Performance,
    ScoreMetric,
    TextChartInfo,
    TextMetricsGroup,
    VisualizationType,
)
from iai_core.entities.shapes import Keypoint

from .performance_metric import PerformanceMetric

logger = logging.getLogger(__name__)

DEFAULT_RELATIVE_DISTANCE_THRESHOLD = 0.2


class PercentageCorrectKeypointsMetric(PerformanceMetric):
    """
    This class is responsible for providing the Percentage of Correct Keypoints (PCK) metric which is used in the
    Keypoint Detection task.

    The PCK metric calculates the percentage of keypoints that fall within a specified threshold distance, often
    normalized by some reference length, such as the size of the bounding box or the torso length. It is defined as:
    PCK = <Number of correctly detected keypoints> / <Total number of keypoints> * 100

    Here correctly detected keypoints are those whose distance from the corresponding keypoint is less than or equal
    to a predefined threshold. This is typically chosen based on the task at hand, such as PCK@0.5, where the distance
    threshold is 50% of the object size (commonly the bounding box size or a major body part length in pose estimation)

    :param ground_truth_dataset: dataset with ground truth annotations
    :param prediction_dataset: dataset with predictions from model inference
    :param label_schema: label schema of the model used for inference
    :param relative_distance_threshold: Distance threshold between predicted and ground truth keypoints, between 0 and 1
    """

    metric_name = "Percentage of Correct Keypoints"

    def __init__(
        self,
        ground_truth_dataset: Dataset,
        prediction_dataset: Dataset,
        label_schema: LabelSchema,
        relative_distance_threshold: float = DEFAULT_RELATIVE_DISTANCE_THRESHOLD,
    ):
        super().__init__(
            ground_truth_dataset=ground_truth_dataset,
            prediction_dataset=prediction_dataset,
            label_schema=label_schema,
        )

        if len(self.prediction_dataset) == 0 or len(self.gt_dataset) == 0:
            raise ValueError("Cannot compute the PCK of empty datasets.")

        self.relative_distance_threshold = relative_distance_threshold
        logger.debug("Using distance threshold: %s", self.relative_distance_threshold)

        self.ground_truth_keypoints_per_item = self.__get_keypoints_from_dataset_as_list(self.gt_dataset)
        self.prediction_keypoints_per_item = self.__get_keypoints_from_dataset_as_list(self.prediction_dataset)
        self.labels = self.label_schema.get_labels(include_empty=True)

        self._pck_values, self._accuracy_per_label, total_tp, total_gt = self.calculate_metrics()
        self._average_pck = total_tp / total_gt if total_gt > 0 else 0

        self._pck_value = ScoreMetric(name=self.metric_name, value=self._average_pck)
        self._score_metric_per_label: dict[Label, ScoreMetric] = {}
        for label in self.labels:
            self._score_metric_per_label[label] = ScoreMetric(
                name=label.name,
                value=self._accuracy_per_label[label.id_],
                label_id=label.id_,
            )

        self._pck_value_per_media: dict[MediaIdentifierEntity, list[ScoreMetric]] = {}
        for idx, gt_item in enumerate(self.gt_dataset):
            media_identifier = gt_item.media_identifier
            self._pck_value_per_media[media_identifier] = [
                ScoreMetric(name=self.metric_name, value=self._pck_values[idx])
            ]

    @property
    def pck_value(self) -> ScoreMetric:
        """Returns the average PCK value as ScoreMetric."""
        return self._pck_value

    @property
    def acc_value_per_label(self) -> dict[Label, ScoreMetric]:
        """Returns the accuracy value per label as a dictionary."""
        return self._score_metric_per_label

    def get_performance(self) -> Performance:
        """
        Retrieves the performance metric for the model.

        :return: A Performance object representing both the average PCK, and the accuracy per label.
        """

        dashboard_metrics: list[MetricsGroup] = [
            TextMetricsGroup(
                metrics=[self.pck_value],
                visualization_info=TextChartInfo(
                    name="Average Percentage of Correct Keypoints",
                ),
            ),
            BarMetricsGroup(
                metrics=list(self.acc_value_per_label.values()),
                visualization_info=BarChartInfo(
                    name="Accuracy per label",
                    palette=ColorPalette.LABEL,
                    visualization_type=VisualizationType.RADIAL_BAR,
                ),
            ),
        ]

        return Performance(score=self.pck_value, dashboard_metrics=dashboard_metrics)

    def get_per_label_scores(self) -> tuple[ScoreMetric, ...]:
        """
        Retrieves scores calculated for each label in the dataset label schema.

        This method is useful for creating ModelTestResult entities

        :return: sequence of ScoreMetric entities with score value and label ID
        """
        return tuple(self._score_metric_per_label.values())

    def get_per_media_scores(self) -> dict[MediaIdentifierEntity, list[ScoreMetric]]:
        """
        Retrieves scores calculated for each media item in the dataset. Includes:
            - the pck score for that item

        This method is useful for creating MediaScores entities.

        :return: a dictionary mapping a media identifier to its ScoreMetric.
        """
        return self._pck_value_per_media

    @staticmethod
    def __get_keypoints_from_dataset_as_list(
        dataset: Dataset | list[DatasetItem],
    ) -> list[list[tuple[float, float, str, bool]]]:
        """
        Retrieves the keypoints from the dataset as a list.

        :param dataset: dataset with keypoints or list of DatasetItems
        :return: list of keypoints for each image in the dataset
        """
        keypoints_per_item = []
        dataset_items = (item for item in dataset) if isinstance(dataset, Dataset) else dataset
        for item in dataset_items:
            keypoints: list[tuple[float, float, str, bool]] = []
            for annotation in item.get_annotations():
                if isinstance(annotation.shape, Keypoint):
                    label = annotation.get_labels()[0]  # always contains a list with one label
                    keypoints.append(
                        (
                            annotation.shape.x,
                            annotation.shape.y,
                            label.id_,
                            annotation.shape.is_visible,
                        )
                    )
                else:
                    raise ValueError(f"Unexpected shape of type {annotation.shape.type}")
            keypoints_per_item.append(keypoints)
        return keypoints_per_item

    def calculate_metrics(self) -> tuple[list[float], dict[str, float], int, int]:
        """
        Calculates the PCK and accuracy per label for the entire dataset.

        :return:
        - pck_values: list of PCK values for each item in the dataset
        - accuracy_per_label: dictionary with the accuracy per label
        - total_true_positives: total number of correctly predicted keypoints
        - total_ground_truth: total number of ground truth keypoints
        """
        pck_values = []
        total_keypoints_per_label: defaultdict[str, int] = defaultdict(int)
        correct_predictions_per_label: defaultdict[str, int] = defaultdict(int)

        for gt_keypoints, pred_keypoints in zip(
            self.ground_truth_keypoints_per_item, self.prediction_keypoints_per_item
        ):
            total_keypoints = [label for _, _, label, is_visible in gt_keypoints if is_visible]
            correct_keypoints = self.compute_correct_keypoints_for_item(
                gt_keypoints,
                pred_keypoints,
            )
            pck_values.append(len(correct_keypoints) / len(total_keypoints))

            for label in total_keypoints:
                total_keypoints_per_label[label] += 1
                if label in correct_keypoints:
                    correct_predictions_per_label[label] += 1

        if not pck_values:
            return [], {}, 0, 0
        accuracy_per_label = {
            label: correct_predictions_per_label[label] / total_keypoints_per_label[label]
            for label in total_keypoints_per_label
        }
        total_true_positives = sum(correct_predictions_per_label.values())
        total_ground_truth = sum(total_keypoints_per_label.values())
        return pck_values, accuracy_per_label, total_true_positives, total_ground_truth

    def compute_correct_keypoints_for_item(
        self,
        gt_keypoints: list[tuple[float, float, str, bool]],
        pred_keypoints: list[tuple[float, float, str, bool]],
    ) -> list[str]:
        """
        Computes correctly predicted keypoints for a given dataset item.
         If a keypoint is not visible in the ground truth, it is not considered in the calculation.

        :param gt_keypoints: list of ground truth keypoints
            a keypoint: [x1: float, y1: float, label: str, is_visible: bool]
        :param pred_keypoints: list of predicted keypoints
            a keypoint: [x1: float, y1: float, label: str, is_visible: bool]
        :return: list of correct keypoints
        """

        if not gt_keypoints or not pred_keypoints:
            return []

        gt_keypoints_dict = {label: (x, y) for x, y, label, is_visible in gt_keypoints if is_visible}
        pred_keypoints_dict = {label: (x, y) for x, y, label, _ in pred_keypoints}
        threshold = self._compute_threshold(gt_keypoints)

        correct_keypoints = []
        for class_, gt_keypoint in gt_keypoints_dict.items():
            pred_keypoint = pred_keypoints_dict.get(class_)
            if pred_keypoint:
                distance = np.sqrt((gt_keypoint[0] - pred_keypoint[0]) ** 2 + (gt_keypoint[1] - pred_keypoint[1]) ** 2)
                if distance <= threshold:
                    correct_keypoints.append(class_)

        return correct_keypoints

    def _compute_threshold(self, gt_keypoints: list[tuple[float, float, str, bool]]) -> float:
        """
        Computes the relative distance threshold which is used to determine if a keypoint is correctly predicted.
        The distance threshold is always relative to the diagonal of the bounding box of the ground truth keypoints.

        :param gt_keypoints: list of ground truth keypoints
        :return: threshold
        """
        x_coordinates, y_coordinates, _, _ = zip(*[kp for kp in gt_keypoints if kp[3]])
        x_min, x_max = min(x_coordinates), max(x_coordinates)
        y_min, y_max = min(y_coordinates), max(y_coordinates)
        diagonal = np.sqrt((x_max - x_min) ** 2 + (y_max - y_min) ** 2)
        return diagonal * self.relative_distance_threshold

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from sc_sdk.entities.evaluation_result import EvaluationResult
from sc_sdk.entities.model_template import TaskType

from jobs_common_extras.evaluation.entities.accuracy_metric import AccuracyMetric
from jobs_common_extras.evaluation.entities.dice_metric import DiceMetric
from jobs_common_extras.evaluation.entities.f_measure_metric import FMeasureMetric
from jobs_common_extras.evaluation.entities.percentage_of_correct_keypoints_metric import (
    PercentageCorrectKeypointsMetric,
)
from jobs_common_extras.evaluation.entities.performance_metric import MetricAverageMethod, PerformanceMetric


class MetricsHelper:
    @staticmethod
    def compute_metric_by_task_type(
        evaluation_result: EvaluationResult,
        task_type: TaskType,
        relative_distance_threshold: float | None = None,
    ) -> PerformanceMetric:
        """
        Computes and returns the appropriate performance metric based on the given task type.

        :param evaluation_result: evaluation result with the predictions.
        :param task_type: the task type for which the metric is computed.
        :param relative_distance_threshold: the relative distance threshold to be used for keypoint detection tasks.
        :return: the appropriate performance metric for the specified task type.
        """
        ground_truth_dataset = evaluation_result.ground_truth_dataset
        prediction_dataset = evaluation_result.prediction_dataset
        label_schema = evaluation_result.get_model().get_label_schema()
        if task_type in [TaskType.CLASSIFICATION, TaskType.ANOMALY_CLASSIFICATION]:
            return AccuracyMetric(
                ground_truth_dataset=ground_truth_dataset,
                prediction_dataset=prediction_dataset,
                label_schema=label_schema,
            )
        if task_type in [TaskType.DETECTION, TaskType.ROTATED_DETECTION]:
            return FMeasureMetric(
                ground_truth_dataset=ground_truth_dataset,
                prediction_dataset=prediction_dataset,
                label_schema=label_schema,
            )
        if task_type in [TaskType.SEGMENTATION, TaskType.INSTANCE_SEGMENTATION]:
            return DiceMetric(
                ground_truth_dataset=ground_truth_dataset,
                prediction_dataset=prediction_dataset,
                label_schema=label_schema,
                average=MetricAverageMethod.MICRO,
            )
        if task_type in [TaskType.KEYPOINT_DETECTION]:
            return PercentageCorrectKeypointsMetric(
                ground_truth_dataset=ground_truth_dataset,
                prediction_dataset=prediction_dataset,
                label_schema=label_schema,
                relative_distance_threshold=relative_distance_threshold,  # type: ignore
            )
        raise ValueError(f"Cannot determine metrics for task type '{task_type}'.")

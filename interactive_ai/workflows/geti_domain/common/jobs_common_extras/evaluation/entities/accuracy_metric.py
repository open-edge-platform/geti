# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging
from collections import defaultdict
from collections.abc import Callable

import numpy as np
from geti_types import ID, MediaIdentifierEntity
from iai_core.entities.datasets import Dataset
from iai_core.entities.label import Label
from iai_core.entities.label_schema import LabelGroup, LabelGroupType, LabelSchema
from iai_core.entities.metrics import (
    BarChartInfo,
    BarMetricsGroup,
    ColorPalette,
    MatrixChartInfo,
    MatrixMetric,
    MatrixMetricsGroup,
    MetricsGroup,
    Performance,
    ScoreMetric,
)
from sklearn.metrics import confusion_matrix as sklearn_confusion_matrix

from jobs_common.utils.progress_helper import noop_progress_callback
from jobs_common_extras.evaluation.utils.accuracy_counter import AccuracyCounters

from .performance_metric import PerformanceMetric

logger = logging.getLogger(__name__)


CountersPerMediaT = defaultdict[MediaIdentifierEntity, AccuracyCounters]
CountersPerLabelT = defaultdict[ID, AccuracyCounters]
CountersPerMediaPerLabelT = defaultdict[MediaIdentifierEntity, defaultdict[ID, AccuracyCounters]]


class AccuracyMetric(PerformanceMetric):
    """
    This class is responsible for providing Accuracy measures; mainly for Classification problems.
    The calculation both supports multi label and binary label predictions.

    The exact definition of 'accuracy' depends on the type of problem; in general,
    it matches the one found in papers and popular frameworks.
      - Multi-class classification (all labels are exclusive):
        accuracy = true / (true + false)
        Here 'true' denotes a correctly classified sample, 'false' a wrong one.
      - Multi-label classification (non-exclusive labels):
        we adopt the so-called 'example based accuracy'
        accuracy = |(pred <intersection> gt)| / |(pred <union> gt)|
        where 'pred' and 'gt' are the sets of predicted and ground truth labels,
        respectively.
      - Hybrid multi-class multi-label classification (some exclusive groups):
        for labels in exclusive groups (2+ labels), the multi-class formula is used;
        conversely, non-exclusive labels follow the multi-label definition.
      - Hierarchical classification: for accuracy purposes, the hierarchy is flattened
        and each label is considered individually as in the hybrid case.

    Per-label accuracy is also defined for the empty label; however, this label is
    ignored when computing the per-media and per-dataset aggregated accuracy.

    :param ground_truth_dataset: dataset with ground truth annotations
    :param prediction_dataset: dataset with predictions from model inference
    :param label_schema: label schema of the model used for inference
    :param progress_callback: callback function to update progress
    """

    metric_name = "Accuracy"

    def __init__(
        self,
        ground_truth_dataset: Dataset,
        prediction_dataset: Dataset,
        label_schema: LabelSchema,
        progress_callback: Callable[[float, str], None] = noop_progress_callback,
    ):
        super().__init__(
            ground_truth_dataset=ground_truth_dataset,
            prediction_dataset=prediction_dataset,
            label_schema=label_schema,
            progress_callback=progress_callback,
            progress_total_steps=len(ground_truth_dataset) * 3,  # loops over all media 3 times
        )
        self.task_labels = self.label_schema.get_labels(include_empty=True)
        self.exclusivity_by_label_id = self._determine_labels_exclusivity()

        # Get the raw counters per media, label and dataset
        self.media_label_counters = self._compute_raw_counters_per_media_per_label()
        self.media_counters = self._compute_raw_counters_per_media(self.media_label_counters)
        self.label_counters = self._compute_raw_counters_per_label(self.media_label_counters)
        # Note: due to how empty labels and false negatives are handled, the per-dataset
        # accuracy must be obtained by aggregation from the per-media ones;
        # it would be wrong to derive it by aggregating the per-label accuracies.
        dataset_counters = sum(self.media_counters.values(), start=AccuracyCounters())

        self.accuracy = ScoreMetric(value=dataset_counters.accuracy, name=self.metric_name)

    def get_performance(self) -> Performance:
        """Returns the performance with accuracy and confusion metrics."""
        dashboard_metrics: list[MetricsGroup] = []

        true_label_idx, predicted_label_idx = self._compute_per_label_indices()
        confusion_matrices: list[MatrixMetric] = self._compute_unnormalized_confusion_matrices(
            true_label_idx=true_label_idx, predicted_label_idx=predicted_label_idx
        )
        # Use normalized matrix for UI
        for matrix in confusion_matrices:
            matrix.normalize()

        confusion_matrix_info = MatrixChartInfo(
            name="Confusion matrix",
            header="confusion",
            row_header="Predicted label",
            column_header="True label",
        )
        dashboard_metrics.append(
            MatrixMetricsGroup(metrics=confusion_matrices, visualization_info=confusion_matrix_info)
        )
        #  Compute precision and recall MetricGroups and append them to the dashboard metrics
        dashboard_metrics.append(self.precision_metrics_group())
        dashboard_metrics.append(self.recall_metrics_group())
        return Performance(score=self.accuracy, dashboard_metrics=dashboard_metrics)

    def get_per_media_scores(self) -> dict[MediaIdentifierEntity, list[ScoreMetric]]:
        per_media_scores = defaultdict(list)
        for media_identifier in self.media_counters:
            media_acc_score = ScoreMetric(
                name=AccuracyMetric.metric_name,
                value=self.media_counters[media_identifier].accuracy,
            )
            media_per_label_accuracy = [
                ScoreMetric(
                    name=self.metric_name,
                    value=self.media_label_counters[media_identifier][label.id_].accuracy,
                    label_id=label.id_,
                )
                for label in self.task_labels
                if self.media_label_counters[media_identifier][label.id_].num_total > 0
            ]
            per_media_scores[media_identifier].append(media_acc_score)
            per_media_scores[media_identifier].extend(media_per_label_accuracy)
        return per_media_scores

    def get_per_label_scores(self) -> tuple[ScoreMetric, ...]:
        return tuple(
            ScoreMetric(
                name=self.metric_name,
                value=self.label_counters[label.id_].accuracy,
                label_id=label.id_,
            )
            for label in self.task_labels
        )

    @staticmethod
    def _get_labels_from_confusion_matrix(confusion_matrix: MatrixMetric) -> list:
        """Return list of str labels from a MatrixMetric"""
        labels = confusion_matrix.row_labels
        if labels is None:
            # If no labels are given, just number the classes by index
            if confusion_matrix.matrix_values is not None:
                label_range = confusion_matrix.matrix_values.shape[0]
            else:
                label_range = 0
            return list(np.arange(label_range))
        return labels

    def precision_metrics_group(self) -> MetricsGroup:
        """
        Computes the precision per class and returns them as ScoreMetrics in a MetricsGroup.
        Precision is defined as the number of true positives divided by the sum of true positives and false positives.

        :return: BarMetricsGroup with the per class precision.
        """
        per_class_precision = [
            ScoreMetric(name=label.name, value=self.label_counters[label.id_].precision)
            for label in self.task_labels
            if not label.is_empty
        ]
        return BarMetricsGroup(
            metrics=per_class_precision,
            visualization_info=BarChartInfo(
                name="Precision per class",
                palette=ColorPalette.LABEL,
            ),
        )

    def recall_metrics_group(self) -> MetricsGroup:
        """
        Computes the recall per class based on a confusion matrix and returns them as ScoreMetrics in a MetricsGroup.
        Recall is defined as the number of true positives divided by the sum of true positives and false negatives.

        :return: BarMetricsGroup with the per class recall
        """
        per_class_recall = [
            ScoreMetric(name=label.name, value=self.label_counters[label.id_].recall)
            for label in self.task_labels
            if not label.is_empty
        ]
        return BarMetricsGroup(
            metrics=per_class_recall,
            visualization_info=BarChartInfo(
                name="Recall per class",
                palette=ColorPalette.LABEL,
            ),
        )

    def _determine_labels_exclusivity(self) -> dict[ID, bool]:
        """
        For each label, determine if it is 'exclusive' (i.e., it belongs to a group
        with 2+ labels) or not.

        :return: Dict mapping each label ID to a bool indicating if it is exclusive
        """
        exclusivity_by_label_id: dict[ID, bool] = {}
        for group in self.label_schema.get_groups(include_empty=True):
            is_multiclass_group = group.group_type == LabelGroupType.EXCLUSIVE and not group.is_single_label()
            for label in group.labels:
                exclusivity_by_label_id[label.id_] = is_multiclass_group
        return exclusivity_by_label_id

    def _compute_raw_counters_per_media_per_label(self) -> CountersPerMediaPerLabelT:
        media_label_counters: CountersPerMediaPerLabelT = defaultdict(lambda: defaultdict(AccuracyCounters))
        # Compare the predictions with the respective ground truths at media-label level
        for gt_item, pred_item in zip(self._gt_dataset, self._prediction_dataset):
            media_identifier = gt_item.media_identifier
            # Note: gt_label_ids and pred_label_ids may contain labels from other tasks
            # too, but it's not a problem as long as we iterate over the task labels
            gt_label_ids = set(gt_item.get_roi_label_ids(include_empty=True))
            pred_label_ids = set(pred_item.get_roi_label_ids(include_empty=True))
            for label in self.task_labels:  # include empty in per-label acc
                found_in_gt = label.id_ in gt_label_ids
                found_in_pred = label.id_ in pred_label_ids
                if found_in_gt and found_in_pred:  # true positive
                    # For multiclass, this means correct prediction
                    media_label_counters[media_identifier][label.id_].tp += 1
                elif not found_in_gt and found_in_pred:  # false positive
                    # For multiclass, this means wrong prediction
                    media_label_counters[media_identifier][label.id_].fp += 1
                elif found_in_gt and not found_in_pred:  # false negative
                    # Note: for multiclass, false negatives only used for per-label
                    # statistics; they are ignored for media/dataset aggregated metrics,
                    # as only the predicted label matters there
                    media_label_counters[media_identifier][label.id_].fn += 1
                else:  # true negative
                    # Ignore regardless of the label exclusivity
                    continue
            self.update_progress()
        return media_label_counters

    def _compute_raw_counters_per_media(self, media_label_counters: CountersPerMediaPerLabelT) -> CountersPerMediaT:
        media_counters: CountersPerMediaT = defaultdict(AccuracyCounters)
        for media_identifier in media_label_counters:
            for label in self.task_labels:
                if label.is_empty:  # skip empty in per-media acc
                    continue
                label_counter = media_label_counters[media_identifier][label.id_]
                if self.exclusivity_by_label_id[label.id_]:  # multiclass label
                    # Note: for exclusive labels, false negatives are ignored in the
                    # per-media metric: they are filter out with `positives`.
                    media_counters[media_identifier] += label_counter.positives
                else:  # multilabel label
                    media_counters[media_identifier] += label_counter
            self.update_progress()
        return media_counters

    def _compute_raw_counters_per_label(self, media_label_counters: CountersPerMediaPerLabelT) -> CountersPerLabelT:
        label_counters: CountersPerLabelT = defaultdict(AccuracyCounters)
        for media_identifier in media_label_counters:
            for label in self.task_labels:  # include empty in per-label acc
                label_counter = media_label_counters[media_identifier][label.id_]
                label_counters[label.id_] += label_counter
            self.update_progress()
        return label_counters

    def _compute_per_label_indices(self) -> tuple[list[set[int]], list[set[int]]]:
        """
        Returns the label indices lists for ground truth and prediction datasets in a tuple.

        :return: tuple containing two lists. The first list contains the ground truth label indices,
            and the second contains the prediction label indices.
        """
        true_label_idx = []
        predicted_label_idx = []

        if len(self.gt_dataset) != len(self.prediction_dataset):
            raise ValueError(
                f"The ground truth dataset and the prediction dataset must have the same length "
                f"({len(self.gt_dataset)} != {len(self.prediction_dataset)})."
            )
        # Iterate over each dataset item, and collect the labels for this item (pred and gt)
        task_labels_idx = {label.id_: idx for idx, label in enumerate(self.task_labels)}
        task_label_ids = {label.id_ for label in self.task_labels}
        for gt_item, pred_item in zip(self.gt_dataset, self.prediction_dataset):
            true_label_idx.append({task_labels_idx[label_id] for label_id in gt_item.get_roi_label_ids(task_label_ids)})
            predicted_label_idx.append(
                {task_labels_idx[label_id] for label_id in pred_item.get_roi_label_ids(task_label_ids)}
            )

        return true_label_idx, predicted_label_idx

    def _compute_unnormalized_confusion_matrices(
        self, true_label_idx: list[set[int]], predicted_label_idx: list[set[int]]
    ) -> list[MatrixMetric]:
        """
        Computes an (unnormalized) confusion matrix for every label group.

        :param true_label_idx: list contains the ground truth label indices
        :param predicted_label_idx: list contains the prediction label indices
        :return: the computed unnormalized confusion matrices
        """

        if len(self.gt_dataset) == 0 or len(self.prediction_dataset) == 0:
            raise ValueError("Cannot compute the confusion matrix of an empty evaluation result.")

        unnormalized_confusion_matrices: list[MatrixMetric] = []

        # Confusion matrix computation
        for label_group in self.label_schema.get_groups():
            matrix = self._compute_unnormalized_confusion_matrix_for_label_group(
                true_label_idx, predicted_label_idx, label_group, self.task_labels
            )
            unnormalized_confusion_matrices.append(matrix)

        return unnormalized_confusion_matrices

    @staticmethod
    def _compute_unnormalized_confusion_matrix_for_label_group(
        true_label_idx: list[set[int]],
        predicted_label_idx: list[set[int]],
        label_group: LabelGroup,
        task_labels: list[Label],
    ) -> MatrixMetric:
        """
        Returns matrix metric for a certain label group.

        :param true_label_idx: list of sets of label indices for the ground truth dataset
        :param predicted_label_idx: list of sets of label indices for the prediction dataset
        :param label_group: label group to compute the confusion matrix for
        :param task_labels: list of labels for the task
        :return: confusion matrix for the label group
        """
        task_labels_idx = {label.id_: idx for idx, label in enumerate(task_labels)}
        map_task_labels_idx_to_group_idx = {
            task_labels_idx[label.id_]: i_group for i_group, label in enumerate(label_group.labels)
        }
        set_group_labels_idx = set(map_task_labels_idx_to_group_idx.keys())
        group_label_names = [task_labels[label_idx].name for label_idx in set_group_labels_idx]

        if len(group_label_names) == 1:
            # Single-class
            # we use "not" to make presence of a class to be at index 0, while the absence of it at index 1
            y_true = [int(not set_group_labels_idx.issubset(true_labels)) for true_labels in true_label_idx]
            y_pred = [int(not set_group_labels_idx.issubset(pred_labels)) for pred_labels in predicted_label_idx]
            group_label_names += [f"~ {group_label_names[0]}"]
            column_labels = group_label_names.copy()
            remove_last_row = False
        else:
            # Multiclass
            undefined_idx = len(group_label_names)  # to define missing value

            # find the intersections between GT and task labels, and Prediction and task labels
            true_intersections = [true_labels.intersection(set_group_labels_idx) for true_labels in true_label_idx]
            pred_intersections = [pred_labels.intersection(set_group_labels_idx) for pred_labels in predicted_label_idx]

            # map the intersection to 0-index value
            y_true = [
                map_task_labels_idx_to_group_idx[next(iter(true_intersection))]
                if len(true_intersection) != 0
                else undefined_idx
                for true_intersection in true_intersections
            ]
            y_pred = [
                map_task_labels_idx_to_group_idx[next(iter(pred_intersection))]
                if len(pred_intersection) != 0
                else undefined_idx
                for pred_intersection in pred_intersections
            ]

            column_labels = group_label_names.copy()
            column_labels.append("Other")
            remove_last_row = True

        matrix_data = sklearn_confusion_matrix(y_true, y_pred, labels=list(range(len(column_labels))))
        if remove_last_row:
            # matrix clean up
            matrix_data = np.delete(matrix_data, -1, 0)
            if sum(matrix_data[:, -1]) == 0:
                # if none of the GT is classified as classes from other groups, clean it up too
                matrix_data = np.delete(matrix_data, -1, 1)
                column_labels.remove(column_labels[-1])

        # Use the label group name without parent prefix
        name = label_group.name.split("___")[-1]
        # Use unnormalized matrix for statistics computation (accuracy, precision, recall)
        return MatrixMetric(
            name=name,
            matrix_values=matrix_data,
            row_labels=group_label_names,
            column_labels=column_labels,
            normalize=False,
        )

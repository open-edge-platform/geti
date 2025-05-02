# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging

import numpy as np
from geti_types import ID, MediaIdentifierEntity
from iai_core.entities.annotation import Annotation
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.datasets import Dataset
from iai_core.entities.label import Label
from iai_core.entities.label_schema import LabelSchema
from iai_core.entities.metrics import (
    BarChartInfo,
    BarMetricsGroup,
    ColorPalette,
    MetricsGroup,
    MultiScorePerformance,
    ScoreMetric,
    VisualizationType,
)
from iai_core.entities.shapes import Rectangle
from iai_core.utils.shape_factory import ShapeFactory

from jobs_common_extras.evaluation.utils.evaluation_helpers import get_iou_matrix, get_n_false_negatives

from .performance_metric import PerformanceMetric

logger = logging.getLogger(__name__)

BOX_CLASS_INDEX = 4
BOX_SCORE_INDEX = 5


class FMeasureMetric(PerformanceMetric):
    """
    Computes the f-measure (also known as F1-score).

    The f-measure is typically used in detection (localization) tasks to obtain a single number that balances precision
    and recall.

    To determine whether a predicted box matches a ground truth box an overlap measured is used based on a minimum
    intersection-over-union (IoU), by default a value of 0.5 is used.

    In addition, spurious results are eliminated by applying non-max suppression (NMS) so that two predicted boxes with
    IoU > threshold are reduced to one. This threshold can be determined automatically by setting `vary_nms_threshold`
    to True.

    :param ground_truth_dataset: dataset with ground truth annotations
    :param prediction_dataset: dataset with predictions from model inference
    :param label_schema: label schema of the model used for inference
    """

    metric_name = "F-Measure"

    def __init__(
        self,
        ground_truth_dataset: Dataset,
        prediction_dataset: Dataset,
        label_schema: LabelSchema,
    ):
        super().__init__(
            ground_truth_dataset=ground_truth_dataset,
            prediction_dataset=prediction_dataset,
            label_schema=label_schema,
        )

        if len(self.prediction_dataset) == 0 or len(self.gt_dataset) == 0:
            raise ValueError("Cannot compute the F-measure of empty an evaluation result.")

        self.labels = self.label_schema.get_labels(include_empty=True)
        empty_labels = [label.id_ for label in self.labels if label.is_empty]
        self.empty_label = empty_labels[0] if empty_labels else None
        classes = [label.id_ for label in self.labels]
        boxes_pair = _FMeasureCalculator(
            FMeasureMetric.__get_boxes_from_dataset_as_list(self.gt_dataset, self.labels),
            FMeasureMetric.__get_boxes_from_dataset_as_list(self.prediction_dataset, self.labels),
            empty_label=self.empty_label,
        )
        result = boxes_pair.evaluate_detections(classes=classes)
        self._f_measure = ScoreMetric(name=self.metric_name, value=result.f_measure)
        self._f_measure_per_label: dict[Label, ScoreMetric] = {}
        for label in self.labels:
            self._f_measure_per_label[label] = ScoreMetric(
                name=label.name,
                value=result.f_measure_per_class[label.id_],
                label_id=label.id_,
            )
        self._precision = ScoreMetric(name="Precision", value=result.precision)
        self._recall = ScoreMetric(name="Recall", value=result.recall)

    @property
    def f_measure(self) -> ScoreMetric:
        """Returns the f-measure as ScoreMetric."""
        return self._f_measure

    @property
    def f_measure_per_label(self) -> dict[Label, ScoreMetric]:
        """Returns the f-measure per label as dictionary (Label -> ScoreMetric)."""
        return self._f_measure_per_label

    def get_performance(self) -> MultiScorePerformance:
        """
        Returns the performance which consists of the F-Measure score and the dashboard metrics.

        :returns: MultiScorePerformance object containing the F-Measure scores and the dashboard metrics.
        """
        empty_label_ids = {label.id_ for label in self.label_schema.get_empty_labels()}
        dashboard_metrics: list[MetricsGroup] = []
        dashboard_metrics.append(
            BarMetricsGroup(
                metrics=[score for score in self.f_measure_per_label.values() if score.label_id not in empty_label_ids],
                visualization_info=BarChartInfo(
                    name="F-measure per label",
                    palette=ColorPalette.LABEL,
                    visualization_type=VisualizationType.RADIAL_BAR,
                ),
            )
        )
        return MultiScorePerformance(
            primary_score=self.f_measure,
            additional_scores=[self._precision, self._recall],
            dashboard_metrics=dashboard_metrics,
        )

    def get_per_media_scores(self) -> dict[MediaIdentifierEntity, list[ScoreMetric]]:
        per_media_scores = {}
        classes = {label.id_ for label in self.labels}
        for gt_item, pred_item in zip(self.gt_dataset, self.prediction_dataset):
            media_identifier = gt_item.media_identifier
            boxes_pair = _FMeasureCalculator(
                FMeasureMetric.__get_boxes_from_dataset_as_list([gt_item], self.labels),
                FMeasureMetric.__get_boxes_from_dataset_as_list([pred_item], self.labels),
                empty_label=self.empty_label,
            )
            result = boxes_pair.evaluate_detections(classes=list(classes))
            per_media_scores[media_identifier] = [ScoreMetric(name=self.metric_name, value=result.f_measure)]
            per_media_scores[media_identifier].extend(
                [
                    ScoreMetric(name=self.metric_name, value=score, label_id=label_id)
                    for label_id, score in result.f_measure_per_class.items()
                ]
            )
        return per_media_scores

    def get_per_label_scores(self) -> tuple[ScoreMetric, ...]:
        return tuple(
            ScoreMetric(
                name=self.metric_name,
                value=score_metric.value,
                label_id=score_metric.label_id,
            )
            for score_metric in self.f_measure_per_label.values()
        )

    @staticmethod
    def __get_boxes_from_dataset_as_list(
        dataset: Dataset | list[DatasetItem], labels: list[Label]
    ) -> list[list[tuple[float, float, float, float, ID, float]]]:
        """
        Return list of boxes from dataset.

        Explanation of output shape:
            a box: [x1: float, y1, x2, y2, class: str, score: float]
            boxes_per_image: [box1, box2, …]
            ground_truth_boxes_per_image: [boxes_per_image_1, boxes_per_image_2, boxes_per_image_3, …]

        :param dataset: Dataset to get boxes from. Or a list of dataset items.
        :param labels: Labels to get boxes for
        :return: list of boxes for each image in the dataset
        """
        boxes_per_image = []
        converted_types_to_box = set()
        label_ids = {label.id_ for label in labels}
        dataset_items = (item for item in dataset) if isinstance(dataset, Dataset) else dataset
        for item in dataset_items:
            boxes: list[tuple[float, float, float, float, ID, float]] = []
            roi_as_box = Annotation(ShapeFactory.shape_as_rectangle(item.roi.shape), labels=[])
            for annotation in item.annotation_scene.annotations:
                shape_as_box = ShapeFactory.shape_as_rectangle(annotation.shape)
                box = shape_as_box.normalize_wrt_roi_shape(roi_as_box.shape)
                n_boxes_before = len(boxes)
                boxes.extend(
                    [
                        (box.x1, box.y1, box.x2, box.y2, label.id_, label.probability)
                        for label in annotation.get_labels(include_empty=True)
                        if label.id_ in label_ids
                    ]
                )
                if not isinstance(annotation.shape, Rectangle) and len(boxes) > n_boxes_before:
                    converted_types_to_box.add(annotation.shape.__class__.__name__)
            boxes_per_image.append(boxes)
        if len(converted_types_to_box) > 0:
            logger.warning(
                f"The shapes of types {tuple(converted_types_to_box)} have been converted to their "
                f"full enclosing Box representation in order to compute the f-measure"
            )

        return boxes_per_image


class _Metrics:
    """
    This class collects the metrics related to detection.

    :param f_measure (float): F-measure of the model.
    :param precision (float): Precision of the model.
    :param recall (float): Recall of the model.
    """

    def __init__(self, f_measure: float, precision: float, recall: float):
        self.f_measure = f_measure
        self.precision = precision
        self.recall = recall


class _ResultCounters:
    """This class collects the number of prediction, TP and FN.

    :param n_false_negatives (int): Number of false negatives.
    :param n_true (int): Number of true positives.
    :param n_predictions (int): Number of predictions.
    """

    def __init__(self, n_false_negatives: int, n_true: int, n_predicted: int):
        self.n_false_negatives = n_false_negatives
        self.n_true = n_true
        self.n_predicted = n_predicted

    def calculate_f_measure(self) -> _Metrics:
        """
        Calculates and returns precision, recall, and f-measure.

        :return: _Metrics object with Precision, recall, and f-measure.
        """
        n_true_positives = self.n_true - self.n_false_negatives

        if self.n_predicted == 0:
            precision = 1.0
            recall = 0.0
        elif self.n_true == 0:
            precision = 0.0
            recall = 1.0
        else:
            precision = n_true_positives / self.n_predicted
            recall = n_true_positives / self.n_true

        f_measure = float((2 * precision * recall) / (precision + recall + np.finfo(float).eps))
        return _Metrics(f_measure, precision, recall)


class _OverallResults:
    """
    This class collects the overall results that is computed by the F-measure performance provider.

    :param f_measure_per_class: f-measure per class.
    :param f_measure: f-measure.
    :param precision: precision.
    :param recall: recall.
    """

    def __init__(
        self,
        f_measure_per_class: dict[ID, float],
        f_measure: float,
        precision: float,
        recall: float,
    ):
        self.f_measure_per_class = f_measure_per_class
        self.f_measure = f_measure
        self.precision = precision
        self.recall = recall


class _FMeasureCalculator:
    """
    This class contains the functions to calculate FMeasure.

    :param ground_truth_boxes_per_image: list containing:
        a box: [x1: float, y1, x2, y2, class: str, score: float]
        boxes_per_image: [box1, box2, …]
        ground_truth_boxes_per_image: [boxes_per_image_1, boxes_per_image_2, boxes_per_image_3, …]
    :param prediction_boxes_per_image: list containing:
        a box: [x1: float, y1, x2, y2, class: str, score: float]
        boxes_per_image: [box1, box2, …]
        predicted_boxes_per_image: [boxes_per_image_1, boxes_per_image_2, boxes_per_image_3, …]
    :param empty_label: (Optional) used to skip accounting for empty labels when aggregating results.
    """

    def __init__(
        self,
        ground_truth_boxes_per_image: list[list[tuple[float, float, float, float, ID, float]]],
        prediction_boxes_per_image: list[list[tuple[float, float, float, float, ID, float]]],
        empty_label: str | None = None,
    ):
        self.ground_truth_boxes_per_image = ground_truth_boxes_per_image
        self.prediction_boxes_per_image = prediction_boxes_per_image
        self.empty_label = empty_label

    def evaluate_detections(
        self,
        classes: list[ID],
        iou_threshold: float = 0.5,
    ) -> _OverallResults:
        """
        Evaluates detections by computing the f-measure.

        :param classes: Names of classes to be evaluated.
        :param iou_threshold: IOU threshold. Defaults to 0.5.
        :return: _OverallResults object with the result statistics (e.g F-measure).
        """

        f_measure_per_class = {}

        # F-measure with no optimization
        result, all_classes_result = self.evaluate_classes(
            classes=classes.copy(),
            iou_threshold=iou_threshold,
        )
        f_measure = all_classes_result.f_measure
        precision = all_classes_result.precision
        recall = all_classes_result.recall
        for class_name in classes:
            f_measure_per_class[class_name] = result[class_name].f_measure

        return _OverallResults(
            f_measure_per_class=f_measure_per_class,
            f_measure=f_measure,
            precision=precision,
            recall=recall,
        )

    def evaluate_classes(self, classes: list[ID], iou_threshold: float) -> tuple[dict[ID, _Metrics], _Metrics]:
        """
        Returns dict of f_measure, precision and recall for each class.

        :param classes: list of classes to be evaluated.
        :param iou_threshold: IoU threshold to use for false negatives.
        :return: The metrics (e.g. F-measure) for each class.
        """
        result: dict[ID, _Metrics] = {}

        all_classes_counters = _ResultCounters(0, 0, 0)

        for class_name in classes:
            metrics, counters = self.get_f_measure_for_class(
                class_name=class_name,
                iou_threshold=iou_threshold,
            )
            result[class_name] = metrics

            #  Note: for the empty label we also compute a per-class score, but it is not
            #  used when aggregating per-media and per-dataset.
            if self.empty_label and class_name == self.empty_label:
                continue
            all_classes_counters.n_false_negatives += counters.n_false_negatives
            all_classes_counters.n_true += counters.n_true
            all_classes_counters.n_predicted += counters.n_predicted

        # for all classes
        all_classes_result = all_classes_counters.calculate_f_measure()
        logger.debug(
            "F-measure for all classes (n_true=%s, n_false_negative=%s, n_predicted=%s): %s",
            all_classes_counters.n_true,
            all_classes_counters.n_false_negatives,
            all_classes_counters.n_predicted,
            all_classes_result.f_measure,
        )
        return result, all_classes_result

    def get_f_measure_for_class(self, class_name: ID, iou_threshold: float) -> tuple[_Metrics, _ResultCounters]:
        """
        Get f_measure for specific class and iou threshold.

        In order to reduce the number of redundant iterations and allow for cleaner, more general code later on,
        all boxes are filtered at this stage by class.

        :param class_name: Name of the class for which the F measure is computed
        :param iou_threshold: IoU threshold
        :return: a structure containing the statistics (e.g. f_measure) and a structure containing the intermediated
            counters used to derive the stats (e.g. num. false positives)
        """
        class_ground_truth_boxes_per_image = self.__filter_class(self.ground_truth_boxes_per_image, class_name)
        class_predicted_boxes_per_image = self.__filter_class(self.prediction_boxes_per_image, class_name)
        if len(class_ground_truth_boxes_per_image) > 0:
            boxes_pair_per_class = _FMeasureCalculator(
                ground_truth_boxes_per_image=class_ground_truth_boxes_per_image,
                prediction_boxes_per_image=class_predicted_boxes_per_image,
                empty_label=self.empty_label,
            )
            result_counters = boxes_pair_per_class.get_counters(iou_threshold=iou_threshold)
            result_metrics = result_counters.calculate_f_measure()
            results = (result_metrics, result_counters)
        else:
            logger.warning("No ground truth images supplied for f-measure calculation.")
            # [f_measure, precision, recall, n_false_negatives, n_true, n_predicted]
            results = (_Metrics(0.0, 0.0, 0.0), _ResultCounters(0, 0, 0))
        return results

    @staticmethod
    def __filter_class(
        boxes_per_image: list[list[tuple[float, float, float, float, ID, float]]],
        class_name: ID,
    ) -> list[list[tuple[float, float, float, float, ID, float]]]:
        """
        Filters boxes to only keep members of one class.

        :param boxes_per_image: list of boxes per image, contains:
            - a box: [x1: float, y1, x2, y2, class: str, score: float]
            - boxes_per_image: [box1, box2, …]
        :param class_name: Name of the class for which the boxes are filtered
        :return: a list of lists of boxes
        """
        filtered_boxes_per_image = []
        for boxes in boxes_per_image:
            filtered_boxes = []
            for box in boxes:
                # TODO boxes tuple should be refactored to dataclass. This way we can access box.class
                if box[BOX_CLASS_INDEX].lower() == class_name.lower():  # type: ignore[union-attr]
                    filtered_boxes.append(box)
            filtered_boxes_per_image.append(filtered_boxes)
        return filtered_boxes_per_image

    def get_counters(self, iou_threshold: float) -> _ResultCounters:
        """
        Return counts of true positives, false positives and false negatives for a given iou threshold.

        For each image (the loop), compute the number of false negatives, the number of predicted boxes, and the number
        of ground truth boxes, then add each value to its corresponding counter

        :param iou_threshold: IoU threshold
        :return: Structure containing the number of false negatives, true positives and predictions.
        """
        n_false_negatives = 0
        n_true = 0
        n_predicted = 0
        for ground_truth_boxes, predicted_boxes in zip(
            self.ground_truth_boxes_per_image, self.prediction_boxes_per_image
        ):
            n_true += len(ground_truth_boxes)
            n_predicted += len(predicted_boxes)
            if len(predicted_boxes) > 0:
                if len(ground_truth_boxes) > 0:
                    iou_matrix = get_iou_matrix(ground_truth_boxes, predicted_boxes)
                    n_false_negatives += get_n_false_negatives(iou_matrix, iou_threshold)
            else:
                n_false_negatives += len(ground_truth_boxes)
        return _ResultCounters(n_false_negatives, n_true, n_predicted)

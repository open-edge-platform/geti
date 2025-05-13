# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from collections import defaultdict

import numpy as np
from geti_types import MediaIdentifierEntity
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
)

from jobs_common_extras.evaluation.utils.segmentation_utils import mask_from_dataset_item

from .performance_metric import MetricAverageMethod, PerformanceMetric

CounterPerLabel = defaultdict[Label | None, int]
CounterPerMediaPerLabel = defaultdict[MediaIdentifierEntity, CounterPerLabel]


class DiceMetric(PerformanceMetric):
    """
    Computes the average Dice coefficient overall and for individual labels.

    See https://en.wikipedia.org/wiki/S%C3%B8rensen%E2%80%93Dice_coefficient for background information.

    To compute the Dice coefficient the shapes in the dataset items of the prediction and ground truth
    dataset are first converted to masks.

    Dice is computed by computing the intersection and union computed over the whole dataset, instead of
    computing intersection and union for individual images and then averaging.

    :param ground_truth_dataset: dataset with ground truth annotations
    :param prediction_dataset: dataset with predictions from model inference
    :param label_schema: label schema of the model used for inference
    :param average: can be:
        - MICRO: every pixel has the same weight, regardless of label
        - MACRO: compute score per label, return the average of the per-label scores
    """

    metric_name = "Dice"

    def __init__(
        self,
        ground_truth_dataset: Dataset,
        prediction_dataset: Dataset,
        label_schema: LabelSchema,
        average: MetricAverageMethod = MetricAverageMethod.MACRO,
    ):
        super().__init__(
            ground_truth_dataset=ground_truth_dataset,
            prediction_dataset=prediction_dataset,
            label_schema=label_schema,
        )
        self.average = average
        self._media_identifiers = [item.media_identifier for item in self.gt_dataset]
        self.__compute_dice_averaged_over_pixels()

    @property
    def overall_dice(self) -> ScoreMetric:
        """Returns the dice average as ScoreMetric."""
        return self._overall_dice

    @property
    def dice_per_label(self) -> dict[Label, ScoreMetric]:
        """Returns a dictionary mapping the label to its corresponding dice score (as ScoreMetric)."""
        return self._dice_per_label

    def get_performance(self) -> Performance:
        """Returns the performance of the evaluation_result."""
        score = self.overall_dice
        dashboard_metrics: list[MetricsGroup] | None = None
        per_label_scores = self.get_per_label_scores()
        if len(per_label_scores) > 0:
            dashboard_metrics = [
                BarMetricsGroup(
                    metrics=per_label_scores,
                    visualization_info=BarChartInfo(
                        name="Dice Average Per Label",
                        palette=ColorPalette.LABEL,
                    ),
                )
            ]
        return Performance(score=score, dashboard_metrics=dashboard_metrics)

    def get_per_media_scores(self) -> dict[MediaIdentifierEntity, list[ScoreMetric]]:
        per_media_scores = {}
        for media in self._media_identifiers:
            overall_score, per_label_score = self.compute_dice_using_intersection_and_cardinality(
                all_intersection=self._per_media_intersections[media],
                all_cardinality=self._per_media_cardinalities[media],
                average=MetricAverageMethod.MICRO,
            )
            overall_score.name = self.metric_name
            label_scores = [
                ScoreMetric(name=self.metric_name, value=score.value, label_id=score.label_id)
                for score in per_label_score.values()
            ]
            per_media_scores[media] = [overall_score, *label_scores]
        return per_media_scores

    def get_per_label_scores(self) -> tuple[ScoreMetric, ...]:
        return tuple(self.dice_per_label.values())

    def __compute_dice_averaged_over_pixels(self) -> None:
        """
        Computes the diced averaged over pixels.

        :return: tuple of the overall dice and the dice averaged over pixels for each label
        """
        if len(self.prediction_dataset) == 0:
            raise ValueError("Cannot compute the DICE score of an empty evaluation result.")

        if len(self.gt_dataset) != len(self.prediction_dataset):
            raise ValueError(
                f"The ground truth dataset and the prediction dataset must have the same length "
                f"({len(self.gt_dataset)} != {len(self.prediction_dataset)})."
            )

        evaluation_result_label_ids = self.prediction_dataset.get_label_ids() | self.gt_dataset.get_label_ids()
        labels = sorted(
            label
            for label in self.label_schema.get_labels(include_empty=False)
            if label.id_ in evaluation_result_label_ids
        )
        hard_predictions = []
        hard_references = []
        for prediction_item, reference_item in zip(list(self.prediction_dataset), list(self.gt_dataset)):
            hard_predictions.append(mask_from_dataset_item(prediction_item, labels))
            hard_references.append(mask_from_dataset_item(reference_item, labels))

        (
            all_intersection,
            all_cardinality,
            self._per_media_intersections,
            self._per_media_cardinalities,
        ) = self.get_intersections_and_cardinalities(hard_references, hard_predictions, labels, self._media_identifiers)

        self._overall_dice, self._dice_per_label = self.compute_dice_using_intersection_and_cardinality(
            all_intersection=all_intersection,
            all_cardinality=all_cardinality,
            average=self.average,
        )

    @classmethod
    def compute_dice_using_intersection_and_cardinality(
        cls,
        all_intersection: dict[Label | None, int],
        all_cardinality: dict[Label | None, int],
        average: MetricAverageMethod,
    ) -> tuple[ScoreMetric, dict[Label, ScoreMetric]]:
        """
        Computes dice score using intersection and cardinality dictionaries.

        Both dictionaries must contain the same set of keys.
        Dice score is computed by: 2 * intersection / cardinality

        :param average: Averaging method to use
        :param all_intersection: collection of intersections per label
        :param all_cardinality: collection of cardinality per label
        :return: tuple containing the overall DICE score, and per label DICE score
        :raises KeyError: if the keys in intersection and cardinality do not match
        :raises KeyError: if the key `None` is not present in either all_intersection or all_cardinality
        :raises ValueError: if the intersection for a certain key is larger than its corresponding cardinality
        """
        dice_per_label: dict[Label, ScoreMetric] = {}

        for label, intersection in all_intersection.items():
            cardinality = all_cardinality[label]
            dice_score = cls.__compute_single_dice_score_using_intersection_and_cardinality(intersection, cardinality)

            # If label is None, then the dice score corresponds to the overall dice score
            # rather than a per-label dice score.
            # This score is calculated last because it can depend on the values in dice_per_label
            if label is not None:
                dice_per_label[label] = ScoreMetric(value=dice_score, name=label.name, label_id=label.id_)

        # Set overall_dice to 0 in case the score cannot be computed
        overall_dice = ScoreMetric(value=0.0, name=cls.metric_name)
        if len(dice_per_label) == 0:  # dataset consists of background pixels only
            pass  # Use the default value of 0
        elif average == MetricAverageMethod.MICRO:
            overall_cardinality = all_cardinality[None]
            overall_intersection = all_intersection[None]
            dice_score = cls.__compute_single_dice_score_using_intersection_and_cardinality(
                overall_intersection, overall_cardinality
            )
            overall_dice = ScoreMetric(value=dice_score, name=cls.metric_name)
        elif average == MetricAverageMethod.MACRO:
            scores = [item.value for item in dice_per_label.values()]
            macro_average_score = sum(scores) / len(scores)
            overall_dice = ScoreMetric(value=macro_average_score, name=cls.metric_name)

        return overall_dice, dice_per_label

    @staticmethod
    def get_intersections_and_cardinalities(
        references: list[np.ndarray],
        predictions: list[np.ndarray],
        labels: list[Label],
        media_identifiers: list[MediaIdentifierEntity],
    ) -> tuple[
        CounterPerLabel,
        CounterPerLabel,
        CounterPerMediaPerLabel,
        CounterPerMediaPerLabel,
    ]:
        """
        Returns all intersections and cardinalities between reference masks and prediction masks.

        Intersections and cardinalities are each returned in a dictionary mapping each label to its corresponding
        number of intersection/cardinality pixels

        :param references: reference masks,s one mask per image
        :param predictions: prediction masks, one mask per image
        :param labels: labels in input masks
        :returns: (all_intersections, all_cardinalities, intersections_per_media, cardinalities_per_media)
        """
        all_intersections = CounterPerLabel(int)
        all_cardinalities = CounterPerLabel(int)
        intersections_per_media = CounterPerMediaPerLabel(CounterPerLabel)
        cardinalities_per_media = CounterPerMediaPerLabel(CounterPerLabel)
        inters = []

        for reference, prediction, media_identifier in zip(references, predictions, media_identifiers):
            intersection = np.where(reference == prediction, reference, 0)
            all_intersections[None] += np.count_nonzero(intersection)
            all_cardinalities[None] += np.count_nonzero(reference) + np.count_nonzero(prediction)

            inters.append(
                (
                    np.count_nonzero(intersection),
                    np.count_nonzero(reference) + np.count_nonzero(prediction),
                )
            )

            per_label_intersections = CounterPerLabel()
            per_label_cardinalities = CounterPerLabel()
            per_label_intersections[None] = np.count_nonzero(intersection)
            per_label_cardinalities[None] = np.count_nonzero(reference) + np.count_nonzero(prediction)
            for i, label in enumerate(labels):
                label_num = i + 1
                _label_intersection = np.count_nonzero(intersection == label_num)
                all_intersections[label] += _label_intersection
                reference_area = np.count_nonzero(reference == label_num)
                prediction_area = np.count_nonzero(prediction == label_num)
                _label_cardinality = reference_area + prediction_area
                all_cardinalities[label] += _label_cardinality

                per_label_intersections[label] = _label_intersection
                per_label_cardinalities[label] = _label_cardinality

            intersections_per_media[media_identifier] = per_label_intersections
            cardinalities_per_media[media_identifier] = per_label_cardinalities

        return (
            all_intersections,
            all_cardinalities,
            intersections_per_media,
            cardinalities_per_media,
        )

    @staticmethod
    def __compute_single_dice_score_using_intersection_and_cardinality(intersection: int, cardinality: int) -> float:
        """
        Computes a single dice score using intersection and cardinality.

        Dice score is computed by: 2 * intersection / cardinality

        :return: dice score using intersection and cardinality
        :raises ValueError: if intersection is larger than cardinality
        """
        if intersection > cardinality:
            raise ValueError("intersection cannot be larger than cardinality")
        if cardinality == 0 and intersection == 0:
            dice_score = 0.0
        else:
            dice_score = float(2 * intersection / cardinality)
        return dice_score

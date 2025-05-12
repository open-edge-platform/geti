# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence

from geti_types import ID, MediaIdentifierEntity
from iai_core.entities.annotation import AnnotationScene
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.datasets import Dataset
from iai_core.entities.label_schema import LabelSchema
from iai_core.entities.metrics import (
    AnomalyLocalizationPerformance,
    BarChartInfo,
    ColorPalette,
    CountMetric,
    MetricsGroup,
    Performance,
    ScoreMetric,
    VisualizationType,
)
from iai_core.entities.shapes import Rectangle

from jobs_common.utils.progress_helper import noop_progress_callback

from .accuracy_metric import AccuracyMetric
from .dice_metric import DiceMetric
from .f_measure_metric import FMeasureMetric
from .performance_metric import MetricAverageMethod, PerformanceMetric

logger = logging.getLogger(__name__)


class AnomalyMetric(PerformanceMetric, ABC):
    """
    AnomalyLocalizationPerformance object for anomaly segmentation and anomaly detection tasks.

    Depending on the subclass, the `get_performance` method returns an AnomalyLocalizationPerformance object with the
    pixel- or bbox-level metric as the primary score. The global (image-level) performance metric is included as an
    additional metric.

    :param ground_truth_dataset: dataset with ground truth annotations
    :param prediction_dataset: dataset with predictions from model inference
    :param label_schema: label schema of the model used for inference
    :param use_local_metric: if True, the local metric is used to calculate per-media and per-label scores
    :param progress_callback: callback function to update progress
    """

    def __init__(
        self,
        ground_truth_dataset: Dataset,
        prediction_dataset: Dataset,
        label_schema: LabelSchema,
        use_local_metric: bool = False,
        progress_callback: Callable[[float, str], None] = noop_progress_callback,
    ):
        super().__init__(
            ground_truth_dataset=ground_truth_dataset,
            prediction_dataset=prediction_dataset,
            label_schema=label_schema,
            progress_callback=progress_callback,
        )
        self.local_metric: PerformanceMetric | None = None
        self.local_score: ScoreMetric | None = None
        self.dashboard_metrics: list[MetricsGroup] = []
        self.use_local_metric = use_local_metric

        global_gt_dataset = AnomalyMetric.get_global_subset(ground_truth_dataset)
        global_pred_dataset = AnomalyMetric.get_global_subset(prediction_dataset)

        self.label_map = {label.id_: label for label in label_schema.get_labels(include_empty=True)}
        local_items_indices = self._locally_annotated_indices(dataset=ground_truth_dataset, label_schema=label_schema)
        self.local_gt_dataset = self.get_local_subset(ground_truth_dataset, local_indices=local_items_indices)
        self.local_pred_dataset = self.get_local_subset(prediction_dataset, local_indices=local_items_indices)

        self.global_metric = AccuracyMetric(
            ground_truth_dataset=global_gt_dataset,
            prediction_dataset=global_pred_dataset,
            label_schema=self.label_schema,
            progress_callback=progress_callback,
        )
        global_performance = self.global_metric.get_performance()
        self.global_score = global_performance.score
        self.dashboard_metrics += global_performance.dashboard_metrics
        # Update metrics to label's name
        label_scores = list(self.global_metric.get_per_label_scores())
        for score in label_scores:
            if score.label_id is not None:
                label = self.label_schema.get_label_by_id(score.label_id)
                if label is not None:
                    score.name = label.name
        self.dashboard_metrics.append(
            MetricsGroup(
                metrics=label_scores,
                visualization_info=BarChartInfo(
                    name="Accuracy per class",
                    palette=ColorPalette.LABEL,
                    visualization_type=VisualizationType.RADIAL_BAR,
                ),
            ),
        )

        if use_local_metric and self.contains_anomalous_images(self.local_gt_dataset):
            self.local_metric = self._get_local_metric()
            local_performance = self.local_metric.get_performance()
            self.local_score = local_performance.score
            self.dashboard_metrics += self._get_local_dashboard_metrics(
                global_count=len(global_gt_dataset),
                local_count=len(self.local_gt_dataset),
                local_score=self.local_score,
            )
            logger.info("Using local metric (score: %s)", self.local_score)

    @staticmethod
    def _get_local_dashboard_metrics(
        global_count: int, local_count: int, local_score: ScoreMetric
    ) -> list[MetricsGroup]:
        return [
            MetricsGroup(
                metrics=[
                    CountMetric(name="Global (image) subset", value=global_count),
                    CountMetric(name="Local (object) subset", value=local_count),
                ],
                visualization_info=BarChartInfo(name="Global vs local subset split"),
            ),
            MetricsGroup(
                metrics=[ScoreMetric(name="Anomalous", value=local_score.score)],
                visualization_info=BarChartInfo(
                    name=f"{local_score.name} on local subset",
                    palette=ColorPalette.LABEL,
                    visualization_type=VisualizationType.RADIAL_BAR,
                ),
            ),
        ]

    @abstractmethod
    def _get_local_metric(self) -> PerformanceMetric:
        raise NotImplementedError

    def get_performance(self) -> Performance:
        """Return the performance object for the evaluation_result."""
        return AnomalyLocalizationPerformance(
            global_score=self.global_score,
            local_score=self.local_score,
            dashboard_metrics=self.dashboard_metrics,
            use_local_score_as_primary=self.use_local_metric,
        )

    def get_per_media_scores(self) -> dict[MediaIdentifierEntity, list[ScoreMetric]]:
        """
        Retrieves scores calculated for each media item in the dataset. Includes:
            - the overall score
            - the per-label score related to the media

        This method is useful for creating MediaScores entities.
        If 'use_local_metric' is True, the local metric is used to calculate the scores.

        :return: a dictionary mapping a media identifier to its ScoreMetric.
        """
        if self.use_local_metric:
            return self.local_metric.get_per_media_scores() if self.local_metric else {}
        return self.global_metric.get_per_media_scores()

    def get_per_label_scores(self) -> tuple[ScoreMetric, ...]:
        """
        Retrieves scores calculated for each label in the dataset.

        This method is useful for creating ModelTestResult entities.
        If 'use_local_metric' is True, the local metric is used to calculate the scores.

        :return: sequence of ScoreMetric entities with score value and label ID
        """
        if self.use_local_metric:
            return self.local_metric.get_per_label_scores() if self.local_metric else ()
        return self.global_metric.get_per_label_scores()

    def contains_anomalous_images(self, dataset: Dataset) -> bool:
        """
        Check if a dataset contains any items with the anomalous label.

        :param dataset: Dataset to check for anomalous items.
        :return: True if the dataset contains anomalous items, False otherwise.
        """
        return any(
            any(self.label_map[label_id].is_anomalous for label_id in item.get_shapes_label_ids()) for item in dataset
        )

    @staticmethod
    def get_global_subset(dataset: Dataset) -> Dataset:
        """
        Extract a subset that contains only the global annotations.

        :param dataset: Dataset from which we want to extract the globally annotated subset.
        :return: Output dataset with only global annotations
        """
        global_items = []
        for item in dataset:
            global_annotations = [
                annotation for annotation in item.get_annotations() if Rectangle.is_full_box(annotation.shape)
            ]
            global_items.append(
                DatasetItem(
                    id_=item.id_,
                    media=item.media,
                    annotation_scene=AnnotationScene(
                        kind=item.annotation_scene.kind,
                        media_identifier=item.media_identifier,
                        media_height=item.media.height,
                        media_width=item.media.width,
                        id_=item.annotation_scene.id_,
                        annotations=global_annotations,
                    ),
                    roi=item.roi,
                    metadata=item.get_metadata(),
                    subset=item.subset,
                    ignored_label_ids=item.ignored_label_ids,
                )
            )
        return Dataset(
            id=ID(),
            items=global_items,
            purpose=dataset.purpose,
            label_schema_id=dataset.label_schema_id,
        )

    @staticmethod
    def get_local_subset(dataset: Dataset, local_indices: Sequence[int]) -> Dataset:
        """
        Extract a subset that contains only those dataset items that have local annotations.

        :param dataset: Dataset from which we want to extract the locally annotated subset.
        :param local_indices: indices of items with local annotations to keep in the dataset
        :return: Output dataset with only local annotations
        """
        local_items = []
        for i in local_indices:
            item = dataset[i]
            local_annotations = [
                annotation for annotation in item.get_annotations() if not Rectangle.is_full_box(annotation.shape)
            ]
            local_items.append(
                DatasetItem(
                    id_=item.id_,
                    media=item.media,
                    annotation_scene=AnnotationScene(
                        kind=item.annotation_scene.kind,
                        media_identifier=item.media_identifier,
                        media_height=item.media.height,
                        media_width=item.media.width,
                        id_=item.annotation_scene.id_,
                        annotations=local_annotations,
                    ),
                    metadata=item.get_metadata(),
                    subset=item.subset,
                    roi=item.roi,
                    ignored_label_ids=item.ignored_label_ids,
                )
            )
        return Dataset(
            id=ID(),
            items=local_items,
            purpose=dataset.purpose,
            label_schema_id=dataset.label_schema_id,
        )

    @staticmethod
    def _locally_annotated_indices(dataset: Dataset, label_schema: LabelSchema) -> list[int]:
        """
        Get indices of items with local annotations in the dataset.

        :param dataset: Dataset to get indices from
        :param label_schema: LabelSchema of the project
        :return: Indices of items with local annotations
        """
        label_is_anomalous_map = {
            label.id_: label.is_anomalous for label in label_schema.get_labels(include_empty=True)
        }
        local_idx = []
        for idx, item in enumerate(dataset):
            local_annotations = [
                annotation for annotation in item.get_annotations() if not Rectangle.is_full_box(annotation.shape)
            ]
            if not local_annotations or not any(
                label_is_anomalous_map[label_id] for label_id in item.get_shapes_label_ids()
            ):
                continue
            local_idx.append(idx)
        return local_idx


class AnomalySegmentationScores(AnomalyMetric):
    """Performance provider for anomaly segmentation tasks."""

    def _get_local_metric(self) -> PerformanceMetric:
        return DiceMetric(
            ground_truth_dataset=self.local_gt_dataset,
            prediction_dataset=self.local_pred_dataset,
            label_schema=self.label_schema,
            average=MetricAverageMethod.MICRO,
        )


class AnomalyDetectionScores(AnomalyMetric):
    """Performance provider for anomaly detection tasks."""

    def _get_local_metric(self) -> PerformanceMetric:
        return FMeasureMetric(
            ground_truth_dataset=self.local_gt_dataset,
            prediction_dataset=self.local_pred_dataset,
            label_schema=self.label_schema,
        )

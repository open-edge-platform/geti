# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from collections.abc import Sequence
from typing import Any

import numpy as np

from communication.constants import MAX_OBJECT_SIZES_PER_LABEL
from communication.exceptions import EvaluationResultNotFoundException, TaskNotFoundException
from service.label_schema_service import LabelSchemaService

from geti_telemetry_tools import unified_tracing
from geti_types import ID, DatasetStorageIdentifier, ProjectIdentifier
from iai_core.entities.annotation import AnnotationScene
from iai_core.entities.annotation_scene_state import AnnotationState
from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.datasets import Dataset
from iai_core.entities.evaluation_result import EvaluationPurpose, EvaluationResult, NullEvaluationResult
from iai_core.entities.label import Domain
from iai_core.entities.label_schema import LabelSchemaView
from iai_core.entities.metrics import (
    BarChartInfo,
    BarMetricsGroup,
    CountMetric,
    DateMetric,
    DurationMetric,
    MetricsGroup,
    NullPerformance,
    Performance,
    TextChartInfo,
    TextMetricsGroup,
)
from iai_core.entities.model import Model, NullModel
from iai_core.entities.project import Project
from iai_core.entities.subset import Subset
from iai_core.repos import (
    AnnotationSceneRepo,
    AnnotationSceneStateRepo,
    DatasetRepo,
    EvaluationResultRepo,
    ImageRepo,
    ModelRepo,
    ProjectRepo,
    VideoRepo,
)

logger = logging.getLogger(__name__)


class StatisticsItem:
    """
    This represents one section of the statistics. This contains a collection of MetricsGroup.
    For example, a project can contain two deep learning tasks.
    The statistics of this project will contain five statistics items:
    - the overall summary of the project,
    - for each task:
        - data summary (annotations for the task)
        - model summary (performance, training duration, etc.)
    """

    name: str
    charts: list[MetricsGroup[Any, Any]]

    def __init__(self, name: str, charts: list[MetricsGroup[Any, Any]]) -> None:
        self.name = name
        self.charts = charts


class StatisticsUseCase:
    # Gradient criteria of object sizes for tall and wide
    ASPECT_RATIO_THRESHOLD_TALL = 10
    ASPECT_RATIO_THRESHOLD_WIDE = 0.1

    @staticmethod
    @unified_tracing
    def get_model_statistics(
        model: Model, project_identifier: ProjectIdentifier, name: str | None = None
    ) -> StatisticsItem:
        """
        Retrieves the model statistics (in one statistics item), this includes:
        - model's created date and training job duration
        - model's score and curves (if any)
        - evaluation result score and additional metrics (from validation and test subsets)
        - amount of train/val/test items in the training dataset
        :param model: Model for which to get the statistics
        :param project_identifier: Identifier of the project that the evaluation result belong to
        :param name: the "header" for the statistics item
        :return: model statistics as a StatisticItem object
        """
        if isinstance(model, NullModel):
            raise ValueError("Cannot compute statistics of null model")

        if name is None:
            name = model.model_storage.name
        model_repo = ModelRepo(model.model_storage_identifier)
        equivalent_model_ids = model_repo.get_all_equivalent_model_ids(model)
        val_result = EvaluationResultRepo(project_identifier).get_latest_by_model_ids(
            equivalent_model_ids=equivalent_model_ids,
            purpose=EvaluationPurpose.VALIDATION,
        )
        test_result = EvaluationResultRepo(project_identifier).get_latest_by_model_ids(
            equivalent_model_ids=equivalent_model_ids, purpose=EvaluationPurpose.TEST
        )
        output = StatisticsItem(name, charts=[])
        output.charts.extend(
            StatisticsUseCase.get_metrics_groups_from_model_evaluation_results(
                validation_result=val_result, test_result=test_result
            )
        )
        # The training statistics are linked to the base model used for training
        base_model = model.get_base_model()

        output.charts.extend(base_model.performance.dashboard_metrics)
        created_date_metrics = TextMetricsGroup(
            visualization_info=TextChartInfo(name="Training date"),
            metrics=[DateMetric(name="Training date", value=base_model.creation_date)],
        )

        output.charts.insert(0, created_date_metrics)
        training_job_duration = max(base_model.training_job_duration, 0)
        training_job_duration_metrics = TextMetricsGroup(
            visualization_info=TextChartInfo(name="Training job duration"),
            metrics=[DurationMetric.from_seconds(name="Training job duration", seconds=training_job_duration)],
        )

        output.charts.insert(1, training_job_duration_metrics)

        training_duration_metrics = TextMetricsGroup(
            visualization_info=TextChartInfo(name="Training duration"),
            metrics=[DurationMetric.from_seconds(name="Training duration", seconds=base_model.training_duration)],
        )
        output.charts.insert(2, training_duration_metrics)

        train_dataset_id = base_model.train_dataset_id
        if isinstance(train_dataset_id, ID):
            project = ProjectRepo().get_by_id(project_identifier.project_id)
            dataset_storage = project.get_training_dataset_storage()
            dataset_repo = DatasetRepo(dataset_storage.identifier)
            subsets_count = dataset_repo.count_per_subset(train_dataset_id)
            train_len = subsets_count.get(Subset.TRAINING.name, 0)
            val_len = subsets_count.get(Subset.VALIDATION.name, 0)
            test_len = subsets_count.get(Subset.TESTING.name, 0)
            dataset_split_metrics = BarMetricsGroup(
                visualization_info=BarChartInfo(name="Dataset split"),
                metrics=[
                    CountMetric(name="Training", value=train_len),
                    CountMetric(name="Validation", value=val_len),
                    CountMetric(name="Test", value=test_len),
                ],
            )
            output.charts.insert(3, dataset_split_metrics)

        return output

    @staticmethod
    @unified_tracing
    def get_metrics_groups_from_model_evaluation_results(
        validation_result: EvaluationResult, test_result: EvaluationResult
    ) -> list[MetricsGroup]:
        """
        Gets metrics groups from evaluation results generated by the model:
        - measurement metric (stored in performance.score)
        - additional metrics stored in the evaluation result (performance.dashboard_metrics)

        If include_test_subset is True, the measurement metric will be shown as a
        doughnut chart with two data points: one from validation and one from test.
        :param validation_result: evaluation for "VALIDATION" purposes
        :param test_result: evaluation for "TEST" purposes
        :return: List of MetricsGroup
        """
        output: list[MetricsGroup] = []

        # buffer for all dashboard metrics from test evaluation result
        buffer_test: list[MetricsGroup] = []
        # buffer for all dashboard metrics from validation evaluation result
        buffer_val: list[MetricsGroup] = []

        if (
            not isinstance(validation_result, NullEvaluationResult)
            and not isinstance(test_result, NullEvaluationResult)
            and validation_result.performance is not None
            and test_result.performance is not None
        ):
            measure_name = validation_result.performance.score.name.capitalize()
            test_score = test_result.performance.score
            test_score.name = "test"
            val_score = validation_result.performance.score
            val_score.name = "validation"

            visual_info = BarChartInfo(
                name=measure_name,
            )
            output.append(BarMetricsGroup([val_score, test_score], visual_info))

            # add test dashboard metrics
            for metric in test_result.performance.dashboard_metrics:
                metric.visualization_info.name += " (test)"
                buffer_val.append(metric)

        output.extend(buffer_val)
        output.extend(buffer_test)

        return output

    @staticmethod
    @unified_tracing
    def get_dataset_storage_statistics_for_task(project: Project, dataset_storage: DatasetStorage, task_id: ID) -> dict:
        """
        Retrieves the dataset storage statistics on a task level, this includes:
        - Amount of images/videos and amount of annotations
        - Amount of annotations and structures per label
        - Latest model score if model is not a NullModel

        :param project: Project to get stats for
        :param dataset_storage: DatasetStorage to get stats for
        :param task_id: If a task_id is passed only add stats for this task_id
        :return: Dictionary with statistics
        """
        statistics = StatisticsUseCase.get_data_stats_for_dataset_storage(
            project=project, dataset_storage=dataset_storage, task_id=task_id
        )
        statistics["objects_per_label"] = []
        statistics["images_and_frames_per_label"] = []
        statistics["object_size_distribution_per_label"] = []
        task_node = project.get_trainable_task_node_by_id(task_id=task_id)
        if not task_node:
            raise TaskNotFoundException(task_id=task_id)
        task_node_label_schema = LabelSchemaService.get_latest_label_schema_for_task(
            project_identifier=project.identifier,
            task_node_id=task_node.id_,
        )
        (
            objects_per_labels,
            media_per_label,
            object_size_distribution_per_label,
        ) = StatisticsUseCase.get_annotation_stats_for_task(
            task_node_label_schema=task_node_label_schema,
            dataset_storage_identifier=dataset_storage.identifier,
        )
        statistics["objects_per_label"].extend(objects_per_labels)
        statistics["images_and_frames_per_label"].extend(media_per_label)
        statistics["object_size_distribution_per_label"].extend(object_size_distribution_per_label)

        return statistics

    @staticmethod
    @unified_tracing
    def get_dataset_statistics(dataset_storage: DatasetStorage, dataset: Dataset) -> dict:
        """
        Retrieves statistics on a dataset level. This includes the sizes of the subset
        and amount of media that is in the dataset.

        :param dataset_storage: DatasetStorage to get stats for
        :param dataset: Dataset to fetch the statistics for
        :return: Dictionary with statistics
        """
        dataset_repo = DatasetRepo(dataset_storage.identifier)
        dataset_counts = dataset_repo.count_per_media_type(dataset_id=dataset.id_)
        subsets_count = dataset_repo.count_per_subset(dataset_id=dataset.id_)
        training = subsets_count.get(Subset.TRAINING.name, 0)
        validation = subsets_count.get(Subset.VALIDATION.name, 0)
        testing = subsets_count.get(Subset.TESTING.name, 0)
        return {
            "id": dataset.id_,
            "subset_info": {
                "training": training,
                "testing": testing,
                "validation": validation,
            },
            "dataset_info": {
                "videos": dataset_counts["n_videos"],
                "frames": dataset_counts["n_frames"],
                "images": dataset_counts["n_images"],
            },
            "creation_time": str(dataset.creation_date),
        }

    @staticmethod
    @unified_tracing
    def get_dataset_storage_statistics(project: Project, dataset_storage: DatasetStorage) -> dict:
        """
        Retrieves the dataset statistics overview, this includes:
        - Amount of images/videos and amount of annotations
        - Amount of annotations and structures per label
        - Latest model score if model is not a NullModel

        :param project: Project to get stats for
        :param dataset_storage: DatasetStorage to get the stats for
        :return: Dictionary with statistics
        """
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
        )
        statistics: dict = {
            "tasks": [],
            "overview": StatisticsUseCase.get_data_stats_for_dataset_storage(
                project=project, dataset_storage=dataset_storage
            ),
        }
        for task_node in project.tasks:
            if task_node.task_properties.is_trainable:
                task_dict: dict[str, Any] = {
                    "task_id": str(task_node.id_),
                    "objects_per_label": [],
                    "object_size_distribution_per_label": [],
                }
                task_node_label_schema = LabelSchemaService.get_latest_label_schema_for_task(
                    project_identifier=project.identifier,
                    task_node_id=task_node.id_,
                )
                (
                    objects_per_labels,
                    _,
                    object_size_distribution_per_label,
                ) = StatisticsUseCase.get_annotation_stats_for_task(
                    task_node_label_schema=task_node_label_schema,
                    dataset_storage_identifier=dataset_storage.identifier,
                )
                task_dict["objects_per_label"] = objects_per_labels
                task_dict["object_size_distribution_per_label"] = object_size_distribution_per_label

                annotation_stats = StatisticsUseCase.get_data_stats_for_task(
                    task_id=task_node.id_,
                    dataset_storage_identifier=dataset_storage_identifier,
                )
                statistics["tasks"].append({**task_dict, **annotation_stats})

        return statistics

    @staticmethod
    @unified_tracing
    def compute_object_size_statistics(obj_sizes: Sequence[tuple[int, int]]) -> dict:
        """
        Computes the object size statistics, this includes:
        - Distribution of object sizes
        - Amount of objects for the categories like balanced, wide, tall and near-mean

        :param obj_sizes: all of the object sizes, which consist of [x, y]
        :return stat: array, which contains object size statistics
        """

        def compute_object_imbalanced_stats(aspect_ratio_threshold_tall, aspect_ratio_threshold_wide):  # noqa: ANN001
            object_ratio = np.transpose(obj_sizes)[1] / np.transpose(obj_sizes)[0]
            n_objects_tall = len(object_ratio[object_ratio >= aspect_ratio_threshold_tall])
            n_objects_wide = len(object_ratio[object_ratio <= aspect_ratio_threshold_wide])
            return n_objects_tall, n_objects_wide

        if len(obj_sizes) > 0:
            cluster_center = (np.around(np.mean(obj_sizes, axis=0))).astype(np.int32)
            cluster_width_height = (np.around(np.std(obj_sizes, axis=0) * 2)).astype(np.int32)
            mean_aspect_ratio = cluster_center[1] / cluster_center[0]
            aspect_ratio_threshold_tall = np.around(
                mean_aspect_ratio * StatisticsUseCase.ASPECT_RATIO_THRESHOLD_TALL, 2
            )
            aspect_ratio_threshold_wide = np.around(
                mean_aspect_ratio * StatisticsUseCase.ASPECT_RATIO_THRESHOLD_WIDE, 2
            )
            n_objects_tall, n_objects_wide = compute_object_imbalanced_stats(
                aspect_ratio_threshold_tall, aspect_ratio_threshold_wide
            )
            n_objects_balanced = len(obj_sizes) - (n_objects_tall + n_objects_wide)

        object_distribution_from_aspect_ratio = {
            "tall": 0 if len(obj_sizes) == 0 else n_objects_tall,
            "balanced": 0 if len(obj_sizes) == 0 else n_objects_balanced,
            "wide": 0 if len(obj_sizes) == 0 else n_objects_wide,
        }

        return {
            "size_distribution": obj_sizes,
            "cluster_center": [] if len(obj_sizes) == 0 else cluster_center.tolist(),
            "cluster_width_height": [] if len(obj_sizes) == 0 else cluster_width_height.tolist(),
            "aspect_ratio_threshold_tall": None if len(obj_sizes) == 0 else aspect_ratio_threshold_tall,
            "aspect_ratio_threshold_wide": None if len(obj_sizes) == 0 else aspect_ratio_threshold_wide,
            "object_distribution_from_aspect_ratio": object_distribution_from_aspect_ratio,
        }

    @staticmethod
    @unified_tracing
    def get_annotation_stats_for_task(
        task_node_label_schema: LabelSchemaView,
        dataset_storage_identifier: DatasetStorageIdentifier,
        include_empty: bool = True,
    ) -> tuple[list[dict], list[dict], list[dict]]:
        """
        Returns the label-wise statistics for annotations that are related to a task (intersecting labels):
        - number of annotations including certain labels
        - number of shapes that have certain labels

        :param task_node_label_schema: label schema of the task
        :param dataset_storage_identifier: identifier of the dataset storage of interest
        :param include_empty: whether to include the empty label in the stats
        """
        labels = task_node_label_schema.get_labels(include_empty=include_empty)
        ann_scene_repo = AnnotationSceneRepo(dataset_storage_identifier)
        label_ids = [label.id_ for label in labels]
        (
            obj_sizes_per_label,
            label_count_per_annotation,
            label_count_per_shape,
        ) = ann_scene_repo.get_annotation_count_and_object_sizes(
            label_ids=label_ids, max_object_sizes_per_label=MAX_OBJECT_SIZES_PER_LABEL
        )

        computed_size_distribution_per_label = {
            label_id: StatisticsUseCase.compute_object_size_statistics(obj_sizes_per_label.get(label_id, ()))
            for label_id in label_ids
        }

        objects_per_label = []
        images_and_frames_per_label = []
        object_size_distribution_per_label = []

        for label in labels:
            count_per_shape = label_count_per_shape.get(label.id_, 0)
            count_per_annotation = label_count_per_annotation.get(label.id_, 0)
            object_size_distribution = computed_size_distribution_per_label[label.id_]

            objects_per_label.append(
                {
                    "id": label.id_,
                    "name": label.name,
                    "color": label.color.hex_str,
                    "value": count_per_shape,
                }
            )
            images_and_frames_per_label.append(
                {
                    "id": label.id_,
                    "name": label.name,
                    "color": label.color.hex_str,
                    "value": count_per_annotation,
                }
            )
            if label.domain != Domain.KEYPOINT_DETECTION:
                object_size_distribution_per_label.append(
                    {
                        "id": label.id_,
                        "name": label.name,
                        "color": label.color.hex_str,
                        **object_size_distribution,
                    }
                )

        return (
            objects_per_label,
            images_and_frames_per_label,
            object_size_distribution_per_label,
        )

    @staticmethod
    @unified_tracing
    def get_data_stats_for_dataset_storage(
        project: Project, dataset_storage: DatasetStorage, task_id: ID | None = None
    ) -> dict:
        """
        Compute statistics regarding the media items in the project. If the project is a
        mutli-task project then a task_id must be given.

        A video is considered annotated if it has at least one annotated frame.

        :param project: Project for which to get the data stats
        :param dataset_storage: DatasetStorage containing the annotations
        :param task_id: The id of the task for which the statistics should be taken from
        :return: Dictionary of statistics:
            - "images": number of media of type image
            - "videos": number of media of type video
            - "annotated_images": number of images with annotations
            - "annotated_videos": number of videos with annotations
            - "annotated_frames": number of video frames with annotations
        """
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=project.workspace_id,
            project_id=project.id_,
            dataset_storage_id=dataset_storage.id_,
        )
        if task_id is None:
            task_id = project.get_trainable_task_nodes()[0].id_
        n_all_images = ImageRepo(dataset_storage.identifier).count()
        n_all_videos = VideoRepo(dataset_storage.identifier).count()

        task_stats = StatisticsUseCase.get_data_stats_for_task(
            task_id=task_id,
            dataset_storage_identifier=dataset_storage_identifier,
        )

        return {
            "images": n_all_images,
            "videos": n_all_videos,
            **task_stats,
        }

    @staticmethod
    @unified_tracing
    def get_data_stats_for_task(task_id: ID, dataset_storage_identifier: DatasetStorageIdentifier) -> dict:
        """
        Retrieves the amount of annotated media items for the given task.

        :param task_id: ID of the task for which to get the statistics
        :param dataset_storage_identifier: Identifier of the dataset storage containing
            the media to get statistics for.
        """
        annotation_states = [
            AnnotationState.ANNOTATED,
            AnnotationState.PARTIALLY_ANNOTATED,
        ]
        repo = AnnotationSceneStateRepo(dataset_storage_identifier)
        n_annotated_images = repo.count_images_state_for_task(annotation_states=annotation_states, task_id=task_id)
        n_annotated_frames = repo.count_video_frames_state_for_task(
            annotation_states=annotation_states, task_id=task_id
        )
        n_annotated_videos = repo.count_videos_state_for_task(annotation_states=annotation_states, task_id=task_id)
        return {
            "annotated_images": n_annotated_images,
            "annotated_videos": n_annotated_videos,
            "annotated_frames": n_annotated_frames,
        }

    @staticmethod
    @unified_tracing
    def get_model_stats(project: Project, model: Model) -> list[StatisticsItem]:
        """
        Retrieves the statistics for the passed model and returns list of statistics items.
        If the evaluation result is not generated yet, raise an exception.

        :param project: Project the task that the model was trained for belongs to
        :param model: Model to get the statistics for
        :raises: EvaluationResultNotFoundException when there is no evaluation result is found for the model.
        :return: List with one StatisticsItem that contains the statistics for the model.
        """
        statistics_items = []
        model_repo = ModelRepo(model.model_storage_identifier)
        equivalent_model_ids = model_repo.get_all_equivalent_model_ids(model)
        evaluation_result = EvaluationResultRepo(project.identifier).get_latest_by_model_ids(
            equivalent_model_ids=equivalent_model_ids,
            purpose=EvaluationPurpose.VALIDATION,
        )
        if not evaluation_result.has_score_metric():
            raise EvaluationResultNotFoundException(
                f"No evaluation result was found for the requested model. Most likely, "
                f"this means that the evaluation result is still being generated. "
                f"Model ID: `{model.id_}`."
            )
        model_stats = StatisticsUseCase.get_model_statistics(model=model, project_identifier=project.identifier)
        statistics_items.append(model_stats)
        return statistics_items

    @staticmethod
    @unified_tracing
    def get_model_performance(model: Model, project_identifier: ProjectIdentifier) -> Performance:
        """
        This function will attempt to retrieve the equivalent model performance from the
        test evaluation results. The equivalent model originates from the same base framework
        model, hence it shares the same evaluation result.
        If there is no performance yet or the model is a NullModel,
        this method will return a NullPerformance.

        :param model: the model for which to get the score
        :param project_identifier: the identifier of the project containing the statistics
        :return: model score from test evaluation results
        """
        if isinstance(model, NullModel):
            return NullPerformance()

        model_repo = ModelRepo(model.model_storage_identifier)
        equivalent_model_ids = model_repo.get_all_equivalent_model_ids(model)

        return EvaluationResultRepo(project_identifier).get_performance_by_model_ids(
            equivalent_model_ids, purpose=EvaluationPurpose.TEST
        )


@unified_tracing
def count_label_occurrence_shape_level(
    annotation_scenes: list[AnnotationScene], include_empty: bool = False
) -> tuple[dict[ID, set], dict[ID, int]]:
    """
    Returns the label occurrence per shape, and per annotation level.
    This function iterates over all shapes just once. (O(n))
    Returns two dictionaries:

    1. per_annotation : a dict with label id -> set(annotation_ids)
    2. per shape: a dict with label id -> int of occurrence

    :param annotation_scenes: annotation scenes to use for making the statistics on
    :param include_empty: set to True to include empty label in the count
    :return: tuple of two dicts
    """
    per_annotation: dict[ID, set] = {}
    per_shape: dict[ID, int] = {}

    for annotation_scene in annotation_scenes:
        for annotation in annotation_scene.annotations:
            for label in annotation.get_labels(include_empty):
                per_shape[label.id_] = per_shape.get(label.id_, 0) + 1
                if label.id_ not in per_annotation:
                    per_annotation[label.id_] = set()
                per_annotation.get(label.id_, set()).add(annotation_scene.id_)

    return per_annotation, per_shape

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines Flyte task to infer and evaluate a model on multiple datasets"""

import logging
from collections.abc import Callable, Sequence
from os import getenv

from geti_telemetry_tools import unified_tracing
from geti_types import DatasetStorageIdentifier, ProjectIdentifier
from iai_core.entities.evaluation_result import EvaluationResult
from iai_core.entities.media_score import MediaScore
from iai_core.entities.metrics import AnomalyLocalizationPerformance, MultiScorePerformance
from iai_core.entities.model import Model
from iai_core.entities.model_template import TaskType
from iai_core.entities.model_test_result import ModelTestResult, TestState
from iai_core.entities.task_node import TaskNode
from iai_core.repos import EvaluationResultRepo, MediaScoreRepo, ModelTestResultRepo
from kubernetes.client import V1ResourceRequirements, V1Toleration

from jobs_common.tasks.primary_container_task import get_flyte_pod_spec
from jobs_common.utils.progress_helper import create_bounded_progress_callback, noop_progress_callback
from jobs_common_extras.evaluation.entities.batch_inference_dataset import BatchInferenceDataset
from jobs_common_extras.evaluation.services.batch_inference import BatchInference
from jobs_common_extras.evaluation.utils.metrics_helper import MetricsHelper

logger = logging.getLogger(__name__)

__all__ = [
    "INFER_AND_EVALUATE_TASK_POD_SPEC",
    "evaluate_and_save_results",
    "infer_and_evaluate",
]

BATCH_INFERENCE_NUM_ASYNC_REQUESTS = 4

WORKLOAD_NODE_SELECTOR_KEY = getenv("WORKLOAD_NODE_SELECTOR_KEY")
WORKLOAD_NODE_SELECTOR_VALUE = getenv("WORKLOAD_NODE_SELECTOR_VALUE")

INFER_AND_EVALUATE_TASK_POD_SPEC = get_flyte_pod_spec(
    resources=V1ResourceRequirements(
        limits={"cpu": "100", "memory": "25Gi", "ephemeral-storage": "100Gi"},
        requests={"cpu": "2", "memory": "4Gi", "ephemeral-storage": "2Gi"},
    ),
    node_selector=(
        {WORKLOAD_NODE_SELECTOR_KEY: WORKLOAD_NODE_SELECTOR_VALUE}
        if (WORKLOAD_NODE_SELECTOR_KEY and WORKLOAD_NODE_SELECTOR_VALUE)
        else None
    ),
    tolerations=(
        [
            V1Toleration(
                effect="NoSchedule",
                key=WORKLOAD_NODE_SELECTOR_KEY,
                operator="Equal",
                value=WORKLOAD_NODE_SELECTOR_VALUE,
            )
        ]
        if (WORKLOAD_NODE_SELECTOR_KEY and WORKLOAD_NODE_SELECTOR_VALUE)
        else None
    ),
)


@unified_tracing
def infer_and_evaluate(
    project_identifier: ProjectIdentifier,
    task_node: TaskNode,
    model: Model,
    batch_inference_datasets: Sequence[BatchInferenceDataset],
    progress_callback: Callable[[float, str], None] = noop_progress_callback,
    progress_message: str = "Inferring and evaluating model",
) -> list[EvaluationResult]:
    """
    Runs the evaluation pipeline on a sequence of datasets.

    :param project_identifier: project containing the model and datasets
    :param task_node: task node to which the model belong to
    :param model: model used for inference
    :param batch_inference_datasets: list of BatchInferenceDataset for which to run inference and evaluation
    :param progress_callback: callback function to update progress
    :param progress_message: string message to use when updating the progress
    :return: updated evaluation results with the computed metrics
    """
    # 1. Run batch inference
    inference_progress_callback = create_bounded_progress_callback(progress_callback, start=0, end=50)
    batch_inference = BatchInference(
        project_identifier=project_identifier,
        task_node=task_node,
        model=model,
        batch_inference_datasets=batch_inference_datasets,
        progress_callback=inference_progress_callback,
        progress_message=progress_message,
        max_async_requests=BATCH_INFERENCE_NUM_ASYNC_REQUESTS,
    )
    batch_inference.run(use_async=True)

    # 2. Compute and save evaluation metrics
    evaluation_progress_callback = create_bounded_progress_callback(progress_callback, start=50, end=100)
    evaluation_results = [ds.evaluation_result for ds in batch_inference_datasets if ds.evaluation_result is not None]
    return evaluate_and_save_results(
        project_identifier=project_identifier,
        evaluation_results=evaluation_results,
        task_type=task_node.task_properties.task_type,
        progress_message=progress_message,
        progress_callback=evaluation_progress_callback,
    )


@unified_tracing
def evaluate_and_save_results(
    project_identifier: ProjectIdentifier,
    evaluation_results: list[EvaluationResult] | list[ModelTestResult],
    task_type: TaskType,
    progress_callback: Callable[[float, str], None],
    progress_message: str,
    relative_distance_threshold: float | None = None,
) -> list[EvaluationResult] | list[ModelTestResult]:
    """
    Computes evaluation metrics.

    :param project_identifier: project containing the model and datasets
    :param evaluation_results: evaluation results with ground truth and prediction dataset
    :param task_type: the type of task for which the metric is computed
    :param progress_callback: callback function to update progress
    :param progress_message: string message to use when updating the progress
    :param relative_distance_threshold: the relative distance threshold to be used for keypoint detection tasks.
    :return: updated evaluation results with the computed metrics
    """
    for i, evaluation_result in enumerate(evaluation_results, 1):
        if isinstance(evaluation_result, ModelTestResult):
            _compute_and_save_model_test(
                project_identifier=project_identifier,
                model_test_result=evaluation_result,
                task_type=task_type,
                relative_distance_threshold=relative_distance_threshold,
            )
        else:
            _compute_and_save_evaluation(
                project_identifier=project_identifier,
                evaluation_result=evaluation_result,
                task_type=task_type,
            )
        progress_callback(i / len(evaluation_results) * 100, progress_message)
    return evaluation_results


@unified_tracing
def _compute_and_save_evaluation(
    project_identifier: ProjectIdentifier,
    evaluation_result: EvaluationResult,
    task_type: TaskType,
) -> None:
    """
    Computes the evaluation metric for the given evaluation result and saves it.

    :param project_identifier: the identifier of the project
    :param evaluation_result: the evaluation result to compute the metric for
    :param task_type: the type of task for which the metric is computed
    """
    metric = MetricsHelper.compute_metric_by_task_type(
        evaluation_result=evaluation_result,
        task_type=task_type,
    )
    evaluation_result.performance = metric.get_performance()
    EvaluationResultRepo(project_identifier).save(evaluation_result)
    logger.info("Saved performance for evaluation result with ID '%s'", evaluation_result.id_)


@unified_tracing
def _compute_and_save_model_test(
    project_identifier: ProjectIdentifier,
    model_test_result: ModelTestResult,
    task_type: TaskType,
    relative_distance_threshold: float | None = None,
) -> None:
    """
    Computes the model test metric for the given model test result and saves it.

    :param project_identifier: the identifier of the project
    :param model_test_result: the model test result to compute the metric for
    :param task_type: the type of task for which the metric is computed
    :param relative_distance_threshold: the relative distance threshold to be used for keypoint detection tasks.
    """
    model_test_result.state = TestState.EVALUATING
    metric = MetricsHelper.compute_metric_by_task_type(
        evaluation_result=model_test_result,
        task_type=task_type,
        relative_distance_threshold=relative_distance_threshold,
    )
    metric_performance = metric.get_performance()
    if not isinstance(metric_performance, MultiScorePerformance):
        model_test_result.performance = MultiScorePerformance(
            primary_score=metric_performance.score,
            dashboard_metrics=metric_performance.dashboard_metrics,
        )
    elif isinstance(metric_performance, AnomalyLocalizationPerformance):
        model_test_result.performance = metric_performance.as_multi_score_performance()
    else:
        model_test_result.performance = metric_performance

    dataset_storage_identifier = DatasetStorageIdentifier(
        workspace_id=project_identifier.workspace_id,
        project_id=project_identifier.project_id,
        dataset_storage_id=model_test_result.dataset_storage_id,
    )
    media_score_repo = MediaScoreRepo(dataset_storage_identifier)
    annotation_scene_per_media = {
        ds_item.media_identifier: ds_item.annotation_scene for ds_item in model_test_result.ground_truth_dataset
    }
    for media_identifier, scores in metric.get_per_media_scores().items():
        annotation_scene = annotation_scene_per_media.get(media_identifier)
        media_score = MediaScore(
            id_=MediaScoreRepo.generate_id(),
            model_test_result_id=model_test_result.id_,
            media_identifier=media_identifier,
            scores=set(scores),
            annotated_label_ids=annotation_scene.get_label_ids(include_empty=True) if annotation_scene else None,
        )
        media_score_repo.save(media_score)
    for score_metric in metric.get_per_label_scores():
        model_test_result.append_score(score_metric)

    ModelTestResultRepo(project_identifier).save(model_test_result)
    logger.info("Saved scores for model test result with ID '%s'", model_test_result.id_)

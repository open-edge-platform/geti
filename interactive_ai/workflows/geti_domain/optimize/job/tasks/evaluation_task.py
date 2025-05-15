# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
Optimized model evaluation task
"""

from typing import Optional

from geti_types import ID
from iai_core.entities.annotation import AnnotationSceneKind
from iai_core.entities.datasets import DatasetPurpose
from iai_core.entities.evaluation_result import EvaluationPurpose
from iai_core.entities.model import Model, ModelStatus
from iai_core.entities.project import Project
from iai_core.entities.subset import Subset
from iai_core.entities.task_node import TaskNode
from iai_core.repos import DatasetStorageRepo, ModelRepo, ModelStorageRepo, ProjectRepo
from iai_core.utils.dataset_helper import DatasetHelper
from iai_core.utils.time_utils import now
from jobs_common.exceptions import CommandInternalError
from jobs_common.tasks import flyte_multi_container_task as task
from jobs_common.tasks.utils.logging import init_logger
from jobs_common.tasks.utils.progress import task_progress
from jobs_common.tasks.utils.secrets import SECRETS, env_vars
from jobs_common.tasks.utils.telemetry import task_telemetry
from jobs_common.utils.annotation_filter import AnnotationFilter
from jobs_common_extras.evaluation.entities.batch_inference_dataset import BatchInferenceDataset
from jobs_common_extras.evaluation.tasks.infer_and_evaluate import INFER_AND_EVALUATE_TASK_POD_SPEC, infer_and_evaluate

from job.models import OptimizationTrainerContext
from job.tasks.helpers import finalize_optimize


@task(
    pod_spec=INFER_AND_EVALUATE_TASK_POD_SPEC,
    secret_requests=SECRETS,
)
@env_vars
@init_logger(package_name=__name__)
@task_telemetry
@task_progress(
    start_message="Starting model evaluation",
    finish_message="Model evaluated",
    failure_message="Model evaluation failed",
)
def evaluate_optimized_model_pot(
    trainer_ctx: OptimizationTrainerContext,
    dataset_storage_id: str,
    model_id: str,
    keep_mlflow_artifacts: bool = False,
    min_annotation_size: Optional[int] = None,  # noqa: UP007
    max_number_of_annotations: Optional[int] = None,  # noqa: UP007
) -> None:
    """
    Runs a POT optimized model evaluation task

    :param trainer_ctx: Data class defining data used for optimization and providing helpers to get
        frequently used objects
    :param dataset_storage_id: dataset storage ID
    :param model_id: base model ID
    :param min_annotation_size: Minimum size of an annotation in pixels. Any annotation smaller than this will be
    ignored
    :param max_number_of_annotations: Maximum number of annotation allowed in one annotation scene. If exceeded, the
    annotation scene will be ignored
    :param keep_mlflow_artifacts: If true, do not remove the artifacts in mlflow bucket even if training succeeds.
        It would be useful for debugging.
    """
    finalize_optimize(
        trainer_ctx=trainer_ctx,
        keep_mlflow_artifacts=keep_mlflow_artifacts,
    )

    _evaluate_optimized_model(
        project_id=trainer_ctx.project_id,
        dataset_storage_id=dataset_storage_id,
        model_storage_id=trainer_ctx.model_storage_id,
        model_id=model_id,
        optimized_model_id=trainer_ctx.model_to_optimize_id,
        min_annotation_size=min_annotation_size,
        max_number_of_annotations=max_number_of_annotations,
    )


def _evaluate_optimized_model(
    project_id: str,
    dataset_storage_id: str,
    model_storage_id: str,
    model_id: str,
    optimized_model_id: str,
    min_annotation_size: int | None = None,
    max_number_of_annotations: int | None = None,
) -> None:
    """
    Runs an optimized model evaluation task

    :param project_id: project ID
    :param dataset_storage_id: dataset storage ID
    :param model_storage_id: model storage ID
    :param model_id: base model ID
    :param optimized_model_id: optimized model ID
    :param min_annotation_size: Minimum size of an annotation in pixels. Any annotation smaller than this will be
    ignored
    :param max_number_of_annotations: Maximum number of annotation allowed in one annotation scene. If exceeded, the
    annotation scene will be ignored
    """
    project = ProjectRepo().get_by_id(ID(project_id))
    model_storage = ModelStorageRepo(project.identifier).get_by_id(ID(model_storage_id))
    dataset_storage = DatasetStorageRepo(project.identifier).get_by_id(ID(dataset_storage_id))
    model_repo = ModelRepo(model_storage.identifier)
    model = model_repo.get_by_id(ID(model_id))
    model_to_optimize = model_repo.get_by_id(ID(optimized_model_id))

    # Update optimized model duration
    training_duration = (now() - model.creation_date).total_seconds()
    model_repo.update_training_duration(model=model_to_optimize, training_duration=training_duration)

    # Evaluate the optimized model on the testing subset
    testing_dataset = model.get_train_dataset().get_subset(Subset.TESTING)
    filtered_testing_dataset = AnnotationFilter.apply_annotation_filters(
        dataset=testing_dataset,
        max_number_of_annotations=max_number_of_annotations,
        min_annotation_size=min_annotation_size,
    )

    task_node = _find_task_node_for_model(model=model, project=project)

    input_dataset = DatasetHelper.create_dataset_with_filtered_annotations_up_to_task(
        input_dataset=filtered_testing_dataset,
        task_node=task_node,
        project=project,
        dataset_storage=dataset_storage,
        annotation_scene_kind=AnnotationSceneKind.INTERMEDIATE,
        save_to_db=False,
    )

    infer_and_evaluate(
        project_identifier=project.identifier,
        task_node=task_node,
        model=model_to_optimize,
        batch_inference_datasets=[
            BatchInferenceDataset(
                dataset_storage=dataset_storage,
                input_dataset=input_dataset,
                annotated_dataset=filtered_testing_dataset,
                output_dataset_purpose=DatasetPurpose.EVALUATION,
                evaluation_purpose=EvaluationPurpose.TEST,
            )
        ],
    )

    if model_to_optimize.model_status == ModelStatus.TRAINED_NO_STATS:
        model_repo.update_model_status(model=model_to_optimize, model_status=ModelStatus.SUCCESS)


def _find_task_node_for_model(model: Model, project: Project) -> TaskNode:
    """
    This function tries to find a TaskNode for the model in the job by
    comparing model storages. If a TaskNode can not be found a
    CommandInternalError is raised
    """
    for task_node in project.get_trainable_task_nodes():
        if task_node.id_ == model.model_storage.task_node_id:
            return task_node
    raise CommandInternalError(f"Could not find a TaskNode for the passed model with ID {model.id_}")

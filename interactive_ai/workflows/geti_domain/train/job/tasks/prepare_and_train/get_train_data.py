# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Get training data task
"""

import logging
from typing import TYPE_CHECKING

from geti_telemetry_tools import unified_tracing
from geti_types import ID
from iai_core.entities.model import Model
from iai_core.repos import ConfigurableParametersRepo, LabelSchemaRepo, ModelStorageRepo, ProjectRepo
from iai_core.services import ModelService
from jobs_common.jobs.helpers import select_input_model

from job.utils.train_workflow_data import TrainWorkflowData

if TYPE_CHECKING:
    from iai_core.configuration.elements.hyper_parameters import HyperParameters

logger = logging.getLogger(__name__)


@unified_tracing
def get_train_data(  # noqa: PLR0913
    project_id: str,
    task_id: str,
    model_storage_id: str,
    from_scratch: bool,
    should_activate_model: bool,
    infer_on_pipeline: bool,
    hyper_parameters_id: str,
    min_annotation_size: int | None = None,
    max_number_of_annotations: int | None = None,
    reshuffle_subsets: bool = False,
    hyperparameters: dict[str, str] | None = None,
) -> TrainWorkflowData:
    """
    Create and return a TrainWorkflowData object containing data needed for training

    :param project_id: Project ID
    :param task_id: Task ID
    :param model_storage_id: ID of model storage to train model in, use active model if empty string
    :param from_scratch: Whether to train the task from scratch.
    :param should_activate_model: Whether to activate model after training
    :param infer_on_pipeline: Whether to infer on pipeline
    :param hyper_parameters_id: ID of the hyper-parameters configuration to use for this job.
        If empty string, it defaults to the current configuration of the model storage.
    :param min_annotation_size: Minimum size of an annotation in pixels. Any annotation smaller than this will be
        ignored during training
    :param max_number_of_annotations: Maximum number of annotation allowed in one annotation scene. If exceeded, the
        annotation scene will be ignored during training.
    :param reshuffle_subsets: Whether to reassign/shuffle all the items to subsets including Test set from scratch
    :param hyperparameters: Dictionary of model hyperparameters
    :return: TrainWorkflowData object containing the data needed for training
    """
    # Validate task is in project
    project = ProjectRepo().get_by_id(ID(project_id))
    task_node = project.get_trainable_task_node_by_id(task_id=ID(task_id))
    if task_node is None:
        raise Exception(f"Task node {task_id} not found in project {project_id}")
    label_schema = LabelSchemaRepo(project.identifier).get_latest_view_by_task(task_node_id=task_node.id_)
    if not model_storage_id:
        model_storage = ModelService.get_active_model_storage(
            project_identifier=project.identifier, task_node_id=task_node.id_
        )
    else:
        model_storage = ModelStorageRepo(project.identifier).get_by_id(ID(model_storage_id))

    if not hyper_parameters_id:
        config_repo = ConfigurableParametersRepo(project.identifier)
        hyper_parameters: HyperParameters = config_repo.get_or_create_hyper_parameters(model_storage=model_storage)
        hyper_parameters_id = str(hyper_parameters.id_)

    active_model = ModelService.get_inference_active_model(
        project_identifier=project.identifier,
        task_node_id=task_node.id_,
    )

    input_model = select_input_model(
        model_storage=model_storage,
        from_scratch=from_scratch,
        current_task_label_schema_id=label_schema.id_,
    )

    if input_model is None:
        from_scratch = True

    input_model_id = str(input_model.id_) if isinstance(input_model, Model) else None

    return TrainWorkflowData(
        workspace_id=project.workspace_id,
        project_id=project_id,
        task_id=task_id,
        label_schema_id=str(label_schema.id_),
        model_storage_id=str(model_storage.id_),
        hyperparameters_id=hyper_parameters_id,
        from_scratch=from_scratch,
        should_activate_model=should_activate_model,
        infer_on_pipeline=infer_on_pipeline,
        active_model_id=str(active_model.id_),
        input_model_id=input_model_id,
        compiled_dataset_shards_id=None,
        min_annotation_size=min_annotation_size,
        max_number_of_annotations=max_number_of_annotations,
        reshuffle_subsets=reshuffle_subsets,
        hyperparameters=hyperparameters,
    )

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Publish kafka message for model activation module
"""

import logging

import grpc
from geti_kafka_tools import publish_event
from geti_telemetry_tools import unified_tracing
from geti_types import CTX_SESSION_VAR, ID
from grpc_interfaces.model_registration.client import ModelRegistrationClient
from iai_core.entities.model import NullModel
from iai_core.entities.model_storage import ModelStorage
from iai_core.repos import ModelRepo, ModelStorageRepo, ProjectRepo
from iai_core.repos.model_repo import ModelStatusFilter
from iai_core.services import ModelService
from jobs_common.tasks.utils.progress import publish_metadata_update

from job.utils.model_registration import ModelMapper, ProjectMapper
from job.utils.train_workflow_data import TrainWorkflowData

logger = logging.getLogger(__name__)

REGISTER_BY_TASK_ID: bool = True


@unified_tracing
def activate_model_storage(model_storage: ModelStorage) -> None:
    """
    Activate model storage of trained model if it is not already the active model

    :param model_storage: Model storage for newly trained model
    """
    old_model_storage = ModelService.get_active_model_storage(
        project_identifier=model_storage.project_identifier,
        task_node_id=model_storage.task_node_id,
    )
    if model_storage.id_ != old_model_storage.id_:
        logger.info(
            "Updating active model storage to %s for task (ID %s)",
            model_storage.model_template.model_template_id,
            model_storage.task_node_id,
        )
        ModelService.activate_model_storage(model_storage=model_storage)


@unified_tracing
def post_model_acceptance(
    train_data: TrainWorkflowData,
    base_model_id: str,
    inference_model_id: str,
) -> None:
    """
    Post model acceptance operations:
        - Activate model storage
        - Publish training successful message
    :param train_data: train workflow data
    :param base_model_id: Model ID of the base model
    :param inference_model_id: Model ID of the optimized model used for inference
    """
    project, task_node = train_data.get_common_entities()

    model_storage = train_data.get_model_storage()
    activate_model_storage(model_storage=model_storage)

    publish_event(
        topic="model_activated",
        body={
            "workspace_id": str(project.workspace_id),
            "project_id": str(project.id_),
            "task_node_id": str(task_node.id_),
            "model_storage_id": str(model_storage.id_),
            "base_model_id": str(base_model_id),
            "inference_model_id": str(inference_model_id),
        },
        headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
    )

    publish_event(
        topic="training_successful",
        body={
            "workspace_id": str(project.workspace_id),
            "project_id": str(project.id_),
        },
        key=str(project.id_).encode(),
        headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
    )

    metadata = {
        "trained_model": {
            "model_storage_id": str(model_storage.id_),
            "model_id": str(base_model_id),
            "model_activated": True,
        }
    }
    publish_metadata_update(metadata=metadata)


@unified_tracing
def register_models(
    project_id: ID,
    model_id: ID,
    optimized_model_id: ID,
    model_storage_id: ID,
    task_id: ID,
) -> None:
    """
    Registers the trained model using the model registration service. If necessary, a pipeline is also registered.
    """
    geti_project = ProjectRepo().get_by_id(project_id)
    project = ProjectMapper.forward(geti_project)
    model_storage = ModelStorageRepo(project_identifier=geti_project.identifier).get_by_id(model_storage_id)

    geti_model = ModelRepo(model_storage.identifier).get_by_id(model_id)
    session = CTX_SESSION_VAR.get()
    model = ModelMapper.forward(
        model=geti_model,
        project_id=project_id,
        workspace_id=session.workspace_id,
        optimized_model_id=optimized_model_id,
        task_id=task_id,
        organization_id=session.organization_id,
    )
    trainable_task_ids = [node.id_ for node in geti_project.get_trainable_task_nodes()]

    try:
        model_registration_client = ModelRegistrationClient(metadata_getter=lambda: CTX_SESSION_VAR.get().as_tuple())
        # Register individual model
        if REGISTER_BY_TASK_ID and len(trainable_task_ids) == 1:
            # Single task project, register 'active' model only -> no further action needed,
            # return immediately after registration
            model_registration_client.register(
                name=f"{str(project_id)}-active",
                project=project,
                models=[model],
                override=True,
            )
            return
        if REGISTER_BY_TASK_ID and len(trainable_task_ids) > 1:
            # Task chain, register individual model by task id
            model_registration_client.register(
                name=f"{str(project_id)}-{str(task_id)}",
                project=project,
                models=[model],
                override=True,
            )
        else:
            model_registration_client.register(
                name=f"{str(project_id)}-{str(model_id)}",
                project=project,
                models=[model],
            )

        # Register new active pipeline
        #   Single model pipeline
        if len(trainable_task_ids) == 1:
            model_registration_client.register(
                name=f"{str(project_id)}-active",
                project=project,
                models=[model],
                override=True,
            )
        #   Chain model pipeline
        else:
            other_task_id = trainable_task_ids[0] if trainable_task_ids[0] != task_id else trainable_task_ids[1]
            other_tasks_model_storage = ModelService.get_active_model_storage(
                project_identifier=geti_project.identifier,
                task_node_id=other_task_id,
            )
            existing_optimized_model = ModelRepo(other_tasks_model_storage.identifier).get_latest_model_for_inference()
            existing_model = ModelRepo(other_tasks_model_storage.identifier).get_latest(
                model_status_filter=ModelStatusFilter.IMPROVED
            )
            if isinstance(existing_optimized_model, NullModel):
                if task_id == trainable_task_ids[0]:
                    # Downstream task has no model yet, we register the model for the
                    # first task as the full active pipeline
                    logger.info(
                        "The downstream model in the task chain is not trained yet, "
                        "registering the available upstream model as active pipeline."
                    )
                    model_registration_client.register(
                        name=f"{str(project_id)}-active",
                        project=project,
                        models=[model],
                        override=True,
                    )
                else:
                    # Only the downstream task has a trained model, normally this
                    # should never happen
                    logger.info("Both models in the chain are not trained yet. Skipping pipeline registration.")
                return

            existing_mapped_model = ModelMapper.forward(
                model=existing_model,
                project_id=project_id,
                workspace_id=session.workspace_id,
                optimized_model_id=existing_optimized_model.id_,
                task_id=other_task_id,
                organization_id=session.organization_id,
            )

            model_registration_client.register(
                name=f"{str(project_id)}-active",
                project=project,
                models=[existing_mapped_model, model],
                override=True,
            )
    except grpc.RpcError:
        logger.exception(f"Failed to register a model for project {project}")

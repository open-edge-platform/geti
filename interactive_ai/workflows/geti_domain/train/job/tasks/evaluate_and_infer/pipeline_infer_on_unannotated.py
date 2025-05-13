# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Pipeline Inference on unannotated dataset module
"""

import logging
from collections.abc import Callable

from geti_telemetry_tools import unified_tracing
from geti_types import ID
from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.datasets import Dataset, DatasetPurpose
from iai_core.entities.label_schema import LabelSchemaView
from iai_core.entities.model import Model, NullModel
from iai_core.entities.model_template import TaskFamily
from iai_core.entities.project import Project
from iai_core.entities.task_node import TaskNode
from iai_core.repos import DatasetRepo, LabelSchemaRepo
from iai_core.services import ModelService
from iai_core.utils.dataset_helper import DatasetHelper
from iai_core.utils.flow_control import FlowControl
from jobs_common.utils.dataset_helpers import DatasetHelpers
from jobs_common.utils.progress_helper import create_bounded_progress_callback
from jobs_common_extras.evaluation.entities.batch_inference_dataset import BatchInferenceDataset
from jobs_common_extras.evaluation.services.batch_inference import BatchInference
from jobs_common_extras.evaluation.tasks.infer_and_evaluate import BATCH_INFERENCE_NUM_ASYNC_REQUESTS

from job.utils.train_workflow_data import TrainWorkflowData

MAX_UNANNOTATED_MEDIA = 500
logger = logging.getLogger(__name__)


@unified_tracing
def pipeline_infer_on_unannotated(
    train_data: TrainWorkflowData, progress_callback: Callable[[float, str], None]
) -> None:
    """
    Infer on unannotated dataset on pipeline project
    :param train_data: train workflow data
    :param progress_callback: A callback function to report inference progress
    """
    project, _ = train_data.get_common_entities()
    if len(project.get_trainable_task_nodes()) == 1:
        logger.info("Only one trainable task for project. Skipping pipeline inference on unannotated dataset.")
        progress_callback(
            100,
            "Skipping generation of task-chain predictions because the project has only one task.",
        )
        return

    dataset_storage = project.get_training_dataset_storage()
    trainable_tasks_schemas = load_tasks_schemas(project=project)
    inference_dataset = DatasetHelpers.get_unannotated_dataset(
        project=project,
        dataset_storage=dataset_storage,
        max_dataset_size=MAX_UNANNOTATED_MEDIA,
    )
    if len(inference_dataset) == 0:
        logger.info(
            "The unannotated dataset is empty for project '%s'; Skipping pipeline inference on unannotated dataset.",
            project.id_,
        )
        progress_callback(100, "All media are already annotated, no predictions need to be generated")
        return

    # Get the model to use for inference for each task; if some task is not trained, then skip the pipeline inference
    active_model_by_task_id: dict[ID, Model] = {
        task_node.id_: ModelService.get_inference_active_model(
            project_identifier=project.identifier, task_node_id=task_node.id_
        )
        for task_node in project.get_trainable_task_nodes()
    }
    if any(isinstance(model, NullModel) for model in active_model_by_task_id.values()):
        progress_callback(
            100,
            "Skipped generating task-chain predictions because not all tasks have a trained model",
        )
        return

    dataset_repo = DatasetRepo(dataset_storage.identifier)
    for i, task_node in enumerate(project.tasks):
        if task_node.task_properties.is_trainable:
            task_progress_callback = create_bounded_progress_callback(
                progress_callback,
                start=(i / len(project.tasks)) * 100,
                end=((i + 1) / len(project.tasks)) * 100,
            )
            model = active_model_by_task_id[task_node.id_]
            inference_dataset = perform_task_inference(
                project=project,
                task_node=task_node,
                model=model,
                dataset_storage=dataset_storage,
                inference_dataset=inference_dataset,
                progress_callback=task_progress_callback,
            )
        elif task_node.task_properties.task_family is TaskFamily.FLOW_CONTROL:
            prev_node = project.tasks[i - 1]
            inference_dataset = FlowControl.flow_control(
                project=project,
                task_node=task_node,
                prev_task_node=prev_node,
                dataset=inference_dataset,
                label_schema=trainable_tasks_schemas[prev_node.id_],
            )
            if len(inference_dataset) == 0:
                logger.info(
                    "Pipeline inference for project '%s' finished prematurely because the first task did not "
                    "produce meaningful predictions (the cropped dataset is empty)",
                    project.id_,
                )
                break
            dataset_repo.save_deep(inference_dataset)
    progress_callback(100, "Finished generating task-chain predictions on unannotated media")


def perform_task_inference(
    project: Project,
    task_node: TaskNode,
    model: Model,
    dataset_storage: DatasetStorage,
    inference_dataset: Dataset,
    progress_callback: Callable[[float, str], None],
) -> Dataset:
    """
    Perform task inference on task and dataset inference
    :param project: Project including task and dataset
    :param task_node: trainable task to do inference
    :param model: model to use for performing inference
    :param dataset_storage: Dataset storage including dataset
    :param inference_dataset: Dataset to use for inference
    :param progress_callback: callback function to report inference progress
    """
    batch_inference_datasets = [
        BatchInferenceDataset(
            dataset_storage=dataset_storage,
            input_dataset=inference_dataset,
            output_dataset_purpose=DatasetPurpose.INFERENCE,
        )
    ]
    batch_inference = BatchInference(
        project_identifier=project.identifier,
        task_node=task_node,
        model=model,
        batch_inference_datasets=batch_inference_datasets,
        progress_callback=progress_callback,
        progress_message=f"Generating predictions for task '{task_node.title}' on unannotated media",
        max_async_requests=BATCH_INFERENCE_NUM_ASYNC_REQUESTS,
    )
    batch_inference.run(use_async=True)
    task_output_dataset = batch_inference.output_datasets[0]

    is_first_trainable_task = project.get_trainable_task_nodes().index(task_node) == 0

    if is_first_trainable_task:
        # Clone dataset to use the cloned dataset as input for crop and next task inference
        inference_dataset = DatasetHelper.clone_dataset(
            dataset=task_output_dataset,
            dataset_storage=dataset_storage,
            save_db=True,
        )
    else:
        inference_dataset = task_output_dataset
    return inference_dataset


def load_tasks_schemas(
    project: Project,
) -> dict[ID, LabelSchemaView]:
    """
    Load the LabelSchemaView of each trainable task node in the pipeline.

    :return: Dict mapping each task node ID to its latest label schema
    """
    output = {}
    label_schema = LabelSchemaRepo(project.identifier)
    for task_node in project.get_trainable_task_nodes():
        label_schema_view = label_schema.get_latest_view_by_task(task_node_id=task_node.id_)
        if isinstance(label_schema_view, LabelSchemaView):
            output[task_node.id_] = label_schema_view
        else:
            logger.warning("No label schema view found for task with id %s", task_node.id_)
    return output

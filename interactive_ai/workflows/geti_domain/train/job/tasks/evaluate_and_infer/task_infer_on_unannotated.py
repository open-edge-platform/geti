# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Task Inference on unannotated dataset module
"""

import logging
from collections.abc import Callable

from geti_kafka_tools import publish_event
from geti_telemetry_tools import unified_tracing
from geti_types import CTX_SESSION_VAR, ID
from iai_core.entities.datasets import DatasetPurpose
from iai_core.repos import ModelRepo
from jobs_common.utils.dataset_helpers import DatasetHelpers
from jobs_common_extras.evaluation.entities.batch_inference_dataset import BatchInferenceDataset
from jobs_common_extras.evaluation.services.batch_inference import BatchInference
from jobs_common_extras.evaluation.tasks.infer_and_evaluate import BATCH_INFERENCE_NUM_ASYNC_REQUESTS

from job.tasks.evaluate_and_infer.pipeline_infer_on_unannotated import MAX_UNANNOTATED_MEDIA
from job.utils.train_workflow_data import TrainWorkflowData

logger = logging.getLogger(__name__)


@unified_tracing
def task_infer_on_unannotated(
    train_data: TrainWorkflowData,
    training_dataset_id: str,
    train_inference_subset_id: str,
    model_id: str,
    progress_callback: Callable[[float, str], None],
) -> None:
    """
    Perform inference on unannotated data for task
    :param train_data: train workflow data
    :param training_dataset_id: id of training dataset
    :param train_inference_subset_id: dataset with train subset and inference results
    :param model_id: id of model to use for inference
    :param progress_callback: A callback function to report inference progress
    return: training dataset id
    """
    project, task_node = train_data.get_common_entities()
    model_storage = train_data.get_model_storage()

    dataset_storage = project.get_training_dataset_storage()
    model = ModelRepo(model_storage.identifier).get_by_id(ID(model_id))
    task_node == project.get_trainable_task_nodes()[0]
    is_first_task = task_node == project.get_trainable_task_nodes()[0]
    output_dataset_purpose = DatasetPurpose.INFERENCE if is_first_task else DatasetPurpose.TASK_INFERENCE

    task_unannotated_dataset = DatasetHelpers.get_unannotated_dataset_for_task(
        project=project,
        dataset_storage=dataset_storage,
        task_node=task_node,
        max_dataset_size=MAX_UNANNOTATED_MEDIA,
    )
    if len(task_unannotated_dataset) == 0:
        logger.info(
            "The unannotated dataset is empty for task '%s' of project '%s', skipping the inference",
            task_node.title,
            project.name,
        )
        progress_callback(100, "All media are already annotated, no predictions need to be generated")
        return

    batch_inference_datasets = [
        BatchInferenceDataset(
            dataset_storage=dataset_storage,
            input_dataset=task_unannotated_dataset,
            output_dataset_purpose=output_dataset_purpose,
        )
    ]
    batch_inference = BatchInference(
        project_identifier=project.identifier,
        task_node=task_node,
        model=model,
        batch_inference_datasets=batch_inference_datasets,
        progress_callback=progress_callback,
        progress_message="Generating task-level predictions on unannotated media",
        max_async_requests=BATCH_INFERENCE_NUM_ASYNC_REQUESTS,
    )
    batch_inference.run(use_async=True)
    output_datasets = batch_inference.output_datasets

    publish_event(
        topic="predictions_and_metadata_created",
        body={
            "workspace_id": train_data.workspace_id,
            "project_id": train_data.project_id,
            "dataset_storage_id": str(project.training_dataset_storage_id),
            "task_node_id": train_data.task_id,
            "model_storage_id": train_data.model_storage_id,
            "model_id": model_id,
            "annotated_dataset_id": training_dataset_id,
            "train_dataset_with_predictions_id": train_inference_subset_id,
            "unannotated_dataset_with_predictions_id": str(output_datasets[0].id_),
        },
        key=str(project.id_).encode(),
        headers_getter=lambda: CTX_SESSION_VAR.get().as_list_bytes(),
    )

    progress_callback(100, "Finished generating task-level predictions on unannotated media")

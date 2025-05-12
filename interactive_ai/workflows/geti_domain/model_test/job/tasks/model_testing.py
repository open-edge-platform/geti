# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
Model testing task
"""

import logging
from typing import Optional

from geti_types import ID
from iai_core.entities.datasets import Dataset, DatasetPurpose
from iai_core.entities.model import ModelFormat
from iai_core.entities.model_test_result import TestState
from iai_core.repos import ModelStorageRepo, ModelTestResultRepo, ProjectRepo
from iai_core.utils.dataset_helper import DatasetHelper
from jobs_common.exceptions import UnsupportedModelFormatForModelTestingException
from jobs_common.jobs.helpers.project_helpers import lock_project
from jobs_common.tasks import flyte_multi_container_task as task
from jobs_common.tasks.utils.logging import init_logger
from jobs_common.tasks.utils.progress import ProgressRange, report_progress, task_progress
from jobs_common.tasks.utils.secrets import SECRETS, env_vars
from jobs_common.tasks.utils.telemetry import task_telemetry
from jobs_common_extras.evaluation.entities.batch_inference_dataset import BatchInferenceDataset
from jobs_common_extras.evaluation.services.batch_inference import BatchInference
from jobs_common_extras.evaluation.tasks.infer_and_evaluate import (
    BATCH_INFERENCE_NUM_ASYNC_REQUESTS,
    INFER_AND_EVALUATE_TASK_POD_SPEC,
    evaluate_and_save_results,
)

from job.commands.create_testing_dataset_command import CreateTaskTestingDatasetCommand

from .utils import _get_task_node

logger = logging.getLogger(__name__)


@task(pod_spec=INFER_AND_EVALUATE_TASK_POD_SPEC, secret_requests=SECRETS)
@env_vars
@init_logger(package_name=__name__)
@task_telemetry
@task_progress(
    start_message="Starting model test",
    finish_message="Model test has completed",
    failure_message="Model test has failed",
)
def run_model_test(
    project_id: str,
    model_test_result_id: str,
    min_annotation_size: Optional[int] = None,  # noqa: UP007
    max_number_of_annotations: Optional[int] = None,  # noqa: UP007
) -> None:
    """
    Run the model testing job. Starts by creating a testing dataset, then infers on the dataset and finally evaluates
    the results

    :param project_id: ID of the project
    :param model_test_result_id: ID of the model test result
    :param min_annotation_size: Minimum size of an annotation in pixels. Any annotation smaller than this will be
     ignored during evaluation
    :param max_number_of_annotations: Maximum number of annotation allowed in one annotation scene. If exceeded, the
     annotation scene will be ignored during evaluation.
    """
    report_progress(message="Creating testing dataset", progress=0)
    gt_dataset = create_testing_dataset(
        project_id=project_id,
        model_test_result_id=model_test_result_id,
        min_annotation_size=min_annotation_size,
        max_number_of_annotations=max_number_of_annotations,
    )
    report_progress(message="Inferring on testing dataset", progress=10)
    output_dataset = infer_on_testing_dataset(
        project_id=project_id,
        model_test_result_id=model_test_result_id,
        gt_dataset=gt_dataset,
        progress_range=ProgressRange(10, 90),
    )
    report_progress(message="Evaluating results", progress=90)
    evaluate_results(
        project_id=project_id,
        model_test_result_id=model_test_result_id,
        gt_dataset=gt_dataset,
        output_dataset=output_dataset,
    )


def create_testing_dataset(  # pylint: disable=unused-argument
    project_id: str,
    model_test_result_id: str,
    min_annotation_size: int | None = None,
    max_number_of_annotations: int | None = None,
) -> Dataset:
    """
    Creates a testing dataset

    :param project_id: ID of the project
    :param model_test_result_id: ID of the model test result
    :param min_annotation_size: Minimum size of an annotation in pixels. Any annotation smaller than this will be
     ignored during evaluation
    :param max_number_of_annotations: Maximum number of annotation allowed in one annotation scene. If exceeded, the
     annotation scene will be ignored during evaluation.
    """
    # Lock the project to prevent data race conditions
    project_id_ = ID(project_id)
    lock_project(job_type="test", project_id=project_id_)

    project = ProjectRepo().get_by_id(project_id_)
    model_test_result = ModelTestResultRepo(project.identifier).get_by_id(ID(model_test_result_id))

    # Update model test result state reflect current task
    model_test_result.state = TestState.CREATING_DATASET
    ModelTestResultRepo(project.identifier).save(model_test_result)

    # Create the command and execute it
    model_storage = ModelStorageRepo(model_test_result.project_identifier).get_by_id(model_test_result.model_storage_id)
    create_dataset_command = CreateTaskTestingDatasetCommand(
        project=project,
        dataset_storage=model_test_result.get_dataset_storages()[0],
        task_node_id=model_storage.task_node_id,
        min_annotation_size=min_annotation_size,
        max_number_of_annotations=max_number_of_annotations,
    )
    create_dataset_command.execute()

    return create_dataset_command.dataset


def infer_on_testing_dataset(
    project_id: str,
    model_test_result_id: str,
    gt_dataset: Dataset,
    progress_range: ProgressRange = ProgressRange(),
) -> Dataset:
    """
    Runs batch inference on the testing  dataset

    :param project_id: ID of the project
    :param model_test_result_id: ID of the model_storage
    :param gt_dataset: Ground truth dataset
    :param progress_range: Range indicating the start and end progress for batch inference
    :return: resulting dataset
    """
    project = ProjectRepo().get_by_id(ID(project_id))
    model_test_result = ModelTestResultRepo(project.identifier).get_by_id(ID(model_test_result_id))
    dataset_storage = model_test_result.get_dataset_storages()[0]
    model_storage = ModelStorageRepo(model_test_result.project_identifier).get_by_id(model_test_result.model_storage_id)
    task_node = _get_task_node(model_storage=model_storage, project=project)
    model = model_test_result.get_model()

    if model.model_format == ModelFormat.BASE_FRAMEWORK:
        raise UnsupportedModelFormatForModelTestingException(format=model.model_format.name)

    # Update model test result state reflect current task
    model_test_result.state = TestState.INFERRING
    ModelTestResultRepo(project.identifier).save(model_test_result)

    # Remove duplicate identifiers without sorting (needed for dataset alignment between gt and pred)
    identifiers_of_media_to_infer = list(dict.fromkeys([item.media_identifier for item in gt_dataset]))
    input_dataset = DatasetHelper.create_dataset_up_to_task_from_media_identifiers(
        project=project,
        task_node=task_node,
        dataset_storage=dataset_storage,
        media_identifiers=identifiers_of_media_to_infer,
        dataset_purpose=DatasetPurpose.TASK_INFERENCE,
        save_to_db=True,
    )
    batch_inference_datasets = [
        BatchInferenceDataset(
            dataset_storage=dataset_storage,
            input_dataset=input_dataset,
            output_dataset_purpose=DatasetPurpose.TASK_INFERENCE,
        )
    ]

    batch_inference = BatchInference(
        project_identifier=project.identifier,
        task_node=task_node,
        model=model,
        batch_inference_datasets=batch_inference_datasets,
        progress_callback=report_progress,
        progress_message="Inferring on testing dataset",
        max_async_requests=BATCH_INFERENCE_NUM_ASYNC_REQUESTS,
        progress_range=progress_range,
    )
    batch_inference.run(use_async=True)
    output_dataset = batch_inference.output_datasets[0]
    return output_dataset


def evaluate_results(
    project_id: str,
    model_test_result_id: str,
    gt_dataset: Dataset,
    output_dataset: Dataset,
) -> None:
    """
    Evaluates the results of the model test

    :param project_id: ID of the project
    :param model_test_result_id: ID of the model test result
    :param gt_dataset: Ground truth dataset
    :param output_dataset: output dataset
    :return mo_model_id and optimized model id
    """
    project = ProjectRepo().get_by_id(ID(project_id))
    model_test_result = ModelTestResultRepo(project.identifier).get_by_id(ID(model_test_result_id))
    model_storage = ModelStorageRepo(model_test_result.project_identifier).get_by_id(model_test_result.model_storage_id)
    task_node = _get_task_node(model_storage=model_storage, project=project)

    # Update model test result state and datasets
    model_test_result.state = TestState.EVALUATING
    model_test_result.ground_truth_dataset_id = gt_dataset.id_
    model_test_result.prediction_dataset_id = output_dataset.id_
    model_test_result._ground_truth_dataset = gt_dataset
    model_test_result._prediction_dataset = output_dataset
    ModelTestResultRepo(project.identifier).save(model_test_result)

    evaluate_and_save_results(
        project_identifier=project.identifier,
        evaluation_results=[model_test_result],
        task_type=task_node.task_properties.task_type,
        progress_callback=report_progress,
        progress_message="Evaluating on testing dataset",
    )

    model_test_result.state = TestState.DONE
    ModelTestResultRepo(project.identifier).save(model_test_result)

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
Evaluation task module
"""

import logging
from collections.abc import Callable

from geti_telemetry_tools import unified_tracing
from geti_telemetry_tools.tracing.common import tracer
from geti_types import ID, ProjectIdentifier
from iai_core.entities.annotation import AnnotationSceneKind
from iai_core.entities.datasets import Dataset, DatasetPurpose
from iai_core.entities.evaluation_result import EvaluationPurpose
from iai_core.entities.model import Model, ModelStatus
from iai_core.entities.model_storage import ModelStorage
from iai_core.entities.subset import Subset
from iai_core.repos import DatasetRepo, ModelRepo
from iai_core.services import ModelService
from iai_core.utils.dataset_helper import DatasetHelper
from jobs_common.utils.annotation_filter import AnnotationFilter
from jobs_common_extras.evaluation.entities.batch_inference_dataset import BatchInferenceDataset
from jobs_common_extras.evaluation.tasks.infer_and_evaluate import infer_and_evaluate
from jobs_common_extras.evaluation.utils.exceptions import EmptyEvaluationDatasetException

from job.utils.model_acceptance import is_model_acceptable
from job.utils.train_workflow_data import TrainWorkflowData

logger = logging.getLogger(__name__)


@unified_tracing
def evaluate(
    train_data: TrainWorkflowData,
    dataset_id: str,
    base_model_id: str,
    mo_model_id: str,
    progress_callback: Callable[[float, str], None],
) -> tuple[bool, str]:
    """
    Runs a trained model evaluation

    :param train_data: train workflow data
    :param dataset_id: Dataset ID
    :param base_model_id: Trained model ID
    :param mo_model_id: Optimized model ID
    :param progress_callback: A callback function to report evaluation progress
    :return: Whether the new model is accepted, the id of dataset including train subset and inference results
    """
    project, task_node = train_data.get_common_entities()

    model_storage = train_data.get_model_storage()

    dataset_storage = project.get_training_dataset_storage()
    dataset_repo = DatasetRepo(dataset_storage.identifier)
    dataset = dataset_repo.get_by_id(ID(dataset_id))
    filtered_dataset = AnnotationFilter.apply_annotation_filters(
        dataset=dataset,
        max_number_of_annotations=train_data.max_number_of_annotations,
        min_annotation_size=train_data.min_annotation_size,
    )
    with tracer.start_as_current_span("get_subsets"):
        train_dataset = filtered_dataset.get_subset(Subset.TRAINING)
        if len(train_dataset) == 0:
            logger.error(
                f"Empty dataset (train subset) to generate AL metadata; either there is a bug in the save, "
                f"or all the annotations were filtered out "
                f"(max_number_of_annotations={train_data.max_number_of_annotations}, "
                f"min_annotation_size={train_data.min_annotation_size})."
            )
            raise RuntimeError("Train dataset is empty.")

        validation_dataset = filtered_dataset.get_subset(Subset.VALIDATION)
        if len(validation_dataset) == 0:
            raise EmptyEvaluationDatasetException(
                subset="validation",
                max_number_of_annotations=train_data.max_number_of_annotations,
                min_annotation_size=train_data.min_annotation_size,
            )

        testing_dataset = filtered_dataset.get_subset(Subset.TESTING)
        if len(testing_dataset) == 0:
            raise EmptyEvaluationDatasetException(
                subset="testing",
                max_number_of_annotations=train_data.max_number_of_annotations,
                min_annotation_size=train_data.min_annotation_size,
            )

    model_repo = ModelRepo(model_storage.identifier)
    base_model = model_repo.get_by_id(ID(base_model_id))
    mo_model = model_repo.get_by_id(ID(mo_model_id))
    if not base_model.has_trained_weights():
        progress_callback(100, "Model doesn't have weights, skipping.")
        return False, ""

    batch_inference_datasets = [
        # Inference on training subset to generate active learning metadata
        BatchInferenceDataset(
            dataset_storage=dataset_storage,
            input_dataset=DatasetHelper.create_dataset_with_filtered_annotations_up_to_task(
                input_dataset=train_dataset,
                task_node=task_node,
                project=project,
                dataset_storage=dataset_storage,
                annotation_scene_kind=AnnotationSceneKind.INTERMEDIATE,
                save_to_db=False,
            ),
            output_dataset_purpose=DatasetPurpose.TASK_INFERENCE,
        ),
        # Evaluation on validation subset
        BatchInferenceDataset(
            dataset_storage=dataset_storage,
            input_dataset=DatasetHelper.create_dataset_with_filtered_annotations_up_to_task(
                input_dataset=validation_dataset,
                task_node=task_node,
                project=project,
                dataset_storage=dataset_storage,
                annotation_scene_kind=AnnotationSceneKind.INTERMEDIATE,
                save_to_db=False,
            ),
            annotated_dataset=validation_dataset,
            output_dataset_purpose=DatasetPurpose.EVALUATION,
            evaluation_purpose=EvaluationPurpose.VALIDATION,
        ),
        # Evaluation on test subset
        BatchInferenceDataset(
            dataset_storage=dataset_storage,
            input_dataset=DatasetHelper.create_dataset_with_filtered_annotations_up_to_task(
                input_dataset=testing_dataset,
                task_node=task_node,
                project=project,
                dataset_storage=dataset_storage,
                annotation_scene_kind=AnnotationSceneKind.INTERMEDIATE,
                save_to_db=False,
            ),
            annotated_dataset=testing_dataset,
            output_dataset_purpose=DatasetPurpose.EVALUATION,
            evaluation_purpose=EvaluationPurpose.TEST,
        ),
    ]

    infer_and_evaluate(
        project_identifier=project.identifier,
        task_node=task_node,
        model=mo_model,
        batch_inference_datasets=batch_inference_datasets,
        progress_callback=progress_callback,
        progress_message="Evaluating the model",
    )

    progress_callback(100, "Model is evaluated, checking improvement")

    train_inference_subset_id = next(
        d.output_dataset.id_
        for d in batch_inference_datasets
        if d.output_dataset_purpose != DatasetPurpose.EVALUATION and d.output_dataset is not None
    )

    active_model = ModelRepo(model_storage.identifier).get_by_id(ID(train_data.active_model_id))
    is_model_improved = check_model_improvement(
        model_storage=model_storage,
        new_model=mo_model,
        old_model=active_model,
        project_identifier=project.identifier,
        validation_dataset=validation_dataset,
    )

    progress_callback(100, "Model is evaluated")

    return is_model_improved, str(train_inference_subset_id)


@unified_tracing
def check_model_improvement(
    model_storage: ModelStorage,
    new_model: Model,
    old_model: Model,
    project_identifier: ProjectIdentifier,
    validation_dataset: Dataset,
) -> bool:
    """
    Check if model is improved and update version and status of model and derivatives accordingly

    :param model_storage: ModelStorage containing model
    :param new_model: newly trained model
    :param old_model: old trained model
    :param project_identifier: project containing the model and validation dataset
    :param validation_dataset: Validation dataset
    :return: True if model is improved, False if not
    """
    model_repo = ModelRepo(model_storage.identifier)
    is_accepted = is_model_acceptable(
        new_model=new_model,
        old_model=old_model,
        project_identifier=project_identifier,
        validation_dataset=validation_dataset,
    )
    if is_accepted:
        logger.info("The new model (ID %s) will be accepted.", new_model.id_)
        new_model.model_status = ModelStatus.SUCCESS
        # Update model version if necessary, see method documentation for details
        latest_success_version = model_repo.get_latest_successful_version()
        new_model.version = latest_success_version + 1
    else:
        logger.info("The new model (ID %s) will NOT be accepted.", new_model.id_)
        new_model.model_status = ModelStatus.NOT_IMPROVED

    # Sync the related models' status
    base_model = new_model.get_base_model()
    models = [base_model]
    models.extend(model_repo.get_optimized_models_by_trained_revision_id(trained_revision_id=base_model.id_))

    for derived_model in models:
        derived_model.version = new_model.version
        derived_model.model_status = new_model.model_status
        ModelService.save_with_auto_archival(model=derived_model, identifier=model_storage.identifier)

    return is_accepted

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Prepare training data task
"""

import logging

from geti_types import ID
from jobs_common.exceptions import CommandDeliberateFailureException, TaskErrorMessage
from jobs_common.tasks import flyte_multi_container_task as task
from jobs_common.tasks.utils.logging import init_logger
from jobs_common.tasks.utils.progress import (
    publish_metadata_update,
    report_progress,
    report_task_step_progress,
    task_progress,
)
from jobs_common.tasks.utils.secrets import SECRETS, env_vars
from jobs_common.tasks.utils.telemetry import task_telemetry
from jobs_common_extras.evaluation.tasks.infer_and_evaluate import INFER_AND_EVALUATE_TASK_POD_SPEC
from sc_sdk.entities.model import NullModel
from sc_sdk.repos import ModelRepo

from job.tasks.evaluate_and_infer.evaluate import evaluate
from job.tasks.evaluate_and_infer.pipeline_infer_on_unannotated import pipeline_infer_on_unannotated
from job.tasks.evaluate_and_infer.post_model_acceptance import post_model_acceptance, register_models
from job.tasks.evaluate_and_infer.pre_evaluate import pre_evaluate
from job.tasks.evaluate_and_infer.task_infer_on_unannotated import task_infer_on_unannotated
from job.tasks.prepare_and_train.train_helpers import finalize_train
from job.utils.train_workflow_data import TrainWorkflowData, TrainWorkflowDataForFlyteTaskTrainer

IDX_STEP_PRE_EVALUATE = 0
IDX_STEP_EVALUATE = 1
IDX_STEP_POST_MODEL_ACCEPTANCE = 2
IDX_STEP_TASK_INFER = 3
IDX_STEP_PIPELINE_INFER = 4
STEPS_COUNT = 5

logger = logging.getLogger(__name__)


def report_pre_evaluate_progress(progress: float, message: str) -> None:
    """
    Function to report pre-evaluation progress
    """
    report_task_step_progress(
        step_index=IDX_STEP_PRE_EVALUATE, steps_count=STEPS_COUNT, step_progress=progress, step_message=message
    )


def report_evaluate_progress(progress: float, message: str) -> None:
    """
    Function to report evaluation step progress
    """
    report_task_step_progress(
        step_index=IDX_STEP_EVALUATE, steps_count=STEPS_COUNT, step_progress=progress, step_message=message
    )


def report_post_model_acceptance_progress(progress: float, message: str) -> None:
    """
    Function to report post model acceptance progress
    """
    report_task_step_progress(
        step_index=IDX_STEP_POST_MODEL_ACCEPTANCE, steps_count=STEPS_COUNT, step_progress=progress, step_message=message
    )


def report_task_infer_progress(progress: float, message: str) -> None:
    """
    Function to report task inference progress
    """
    report_task_step_progress(
        step_index=IDX_STEP_TASK_INFER, steps_count=STEPS_COUNT, step_progress=progress, step_message=message
    )


def report_pipeline_infer_progress(progress: float, message: str) -> None:
    """
    Function to report pipeline inference progress
    """
    report_task_step_progress(
        step_index=IDX_STEP_PIPELINE_INFER, steps_count=STEPS_COUNT, step_progress=progress, step_message=message
    )


def update_model_trained_metadata(train_data: TrainWorkflowData, base_model_id: str) -> None:
    """
    Update the job metadata with the model which has been trained but not activated yet.

    :param train_data: train workflow data
    :param base_model_id: Model ID of the base model
    """
    model_storage = train_data.get_model_storage()
    metadata = {
        "trained_model": {
            "model_storage_id": str(model_storage.id_),
            "model_id": str(base_model_id),
            "model_activated": False,
        }
    }
    logger.info(f"Updating metadata: {metadata}")
    publish_metadata_update(metadata=metadata)


class ModelNotImprovedException(CommandDeliberateFailureException, TaskErrorMessage):
    """
    Raised when the accuracy of the newly trained model does not represent
    an improvement with respect to the previous models.
    """

    def __init__(self, *args, **kwargs) -> None:  # noqa: ARG002
        msg = (
            "The training is finished successfully but the new model accuracy is lower than the previous "
            "model accuracy. Possible solutions: (1) add more annotated data to the dataset, (2) train "
            "from scratch, (3) use a different model architecture or (4) run optimize accuracy operation "
            "from the last trained model."
        )
        super().__init__(msg)


class EvaluationFailedException(CommandDeliberateFailureException, TaskErrorMessage):
    """
    Raised when the model evaluation step has failed.
    """

    def __init__(self, *args) -> None:  # noqa: ARG002
        msg = (
            "Training failed at evaluation stage. No model is saved from this training round. "
            "Please try again and if problem persists, contact our customer support team."
        )
        super().__init__(msg)


class InferenceFailedException(CommandDeliberateFailureException, TaskErrorMessage):
    """
    Raised when the post training inference (either task or pipeline) has failed.
    """

    def __init__(self, *args) -> None:  # noqa: ARG002
        msg = (
            "Training process failed at final inference stage. The model has been trained, evaluated and committed. "
            "No action required from your side."
        )
        super().__init__(msg)


class ModelRegistrationFailedException(CommandDeliberateFailureException, TaskErrorMessage):
    """
    Raised when the inference model registration has failed.
    """

    def __init__(self, *args) -> None:  # noqa: ARG002
        msg = "Training job fails at model registration stage. No model has been committed. Please retry training."
        super().__init__(msg)


def pre_evaluate_model(train_data: TrainWorkflowData, base_model_id: ID, dataset_id: ID, from_scratch: bool) -> None:
    """
    Pre-evaluate model if there is a previous model in the same model storage

    :param train_data: train workflow data
    :param base_model_id: ID of the new model that was trained
    :param dataset_id: ID of dataset that was used for training
    :param from_scratch: bool indicating whether the model was trained from scratch
    """
    if from_scratch:
        report_pre_evaluate_progress(progress=100, message="Pre-evaluation skipped because training from scratch.")
        return

    model_repo = ModelRepo(train_data.get_model_storage_identifier())
    base_model = model_repo.get_by_id(base_model_id)
    model_to_preevaluate = model_repo.get_latest_model_for_inference(
        base_model_id=base_model.previous_trained_revision_id
    )
    if isinstance(model_to_preevaluate, NullModel):
        report_pre_evaluate_progress(
            progress=100, message="No previous model found for this model architecture in the project."
        )
    else:
        report_pre_evaluate_progress(progress=0, message="Starting model pre-evaluating")
        dataset = train_data.get_dataset(dataset_id=dataset_id)
        try:
            pre_evaluate(
                train_data=train_data,
                dataset=dataset,
                model_to_preevaluate=model_to_preevaluate,
                progress_callback=report_pre_evaluate_progress,
            )
            report_pre_evaluate_progress(progress=100, message="Model is pre-evaluated")
        except Exception as e:
            logger.warning(
                "Pre-evaluation failed; training continues but the performance of the new model "
                "will not be compared with the currently active model. Exception details: %s",
                e,
            )
            report_progress(
                warning=(
                    "Pre-evaluation failed. Training will proceed without comparing performance to the previously "
                    "trained model."
                )
            )


@task(pod_spec=INFER_AND_EVALUATE_TASK_POD_SPEC, secret_requests=SECRETS)
@env_vars
@init_logger(package_name=__name__)
@task_telemetry
@task_progress(
    start_message="Starting model evaluation and inference",
    finish_message="Model is evaluated and inference is finished",
    failure_message="Model evaluation and inference failed",
)
def evaluate_and_infer(
    train_data: TrainWorkflowDataForFlyteTaskTrainer,
    should_activate_model: bool,
    infer_on_pipeline: bool,
    from_scratch: bool,
    keep_mlflow_artifacts: bool = False,
) -> None:
    """
    Evaluate a trained model & perform inference

    :param train_data: Train data
    :param dataset_id: Dataset ID
    :param base_model_id: Base model ID
    :param mo_model_id: Optimized model ID
    :param should_activate_model: Whether to activate model after training
    :param infer_on_pipeline: Whether to infer on pipeline
    :param from_scratch: Whether training was from scratch
    :param keep_mlflow_artifacts: If true, do not remove the artifacts in mlflow bucket even if training succeeds.
        It would be useful for debugging.
    :return ModelsIds: trained models IDs
    """
    finalize_train(
        train_data=train_data.train_data,
        train_output_model_ids=train_data.train_output_model_ids,
        keep_mlflow_artifacts=keep_mlflow_artifacts,
    )

    # Model has been trained
    update_model_trained_metadata(
        train_data=train_data.train_data,
        base_model_id=train_data.train_output_model_ids.base,
    )

    # Pre-evaluate model (if needed)
    pre_evaluate_model(
        train_data=train_data.train_data,
        base_model_id=ID(train_data.train_output_model_ids.base),
        dataset_id=ID(train_data.dataset_id),
        from_scratch=from_scratch,
    )

    # Evaluate the trained models on different subsets
    report_evaluate_progress(progress=0, message="Starting model evaluation")
    try:
        is_model_accepted, train_inference_subset_id = evaluate(
            train_data=train_data.train_data,
            dataset_id=train_data.dataset_id,
            base_model_id=train_data.train_output_model_ids.base,
            mo_model_id=train_data.train_output_model_ids.mo_fp32_with_xai,
            progress_callback=report_evaluate_progress,
        )

        if not is_model_accepted:
            raise ModelNotImprovedException

        if not should_activate_model:
            return

    except ModelNotImprovedException as err:
        raise err
    except Exception as err:
        logger.error("Error occurred during model evaluation", exc_info=err)
        raise EvaluationFailedException from err

    # Create inference model pipelines and register the pipelines with ModelMesh.
    report_post_model_acceptance_progress(progress=0, message="Activating trained model")
    try:
        register_models(
            project_id=ID(train_data.train_data.project_id),
            model_id=ID(train_data.train_output_model_ids.base),
            optimized_model_id=ID(train_data.train_output_model_ids.mo_fp32_with_xai),
            model_storage_id=ID(train_data.train_data.model_storage_id),
            task_id=ID(train_data.train_data.task_id),
        )
    except Exception as err:
        logger.error("Error occurred during model registration", exc_info=err)
        raise ModelRegistrationFailedException from err

    # Activate model
    try:
        post_model_acceptance(
            train_data=train_data.train_data,
            base_model_id=train_data.train_output_model_ids.base,
            inference_model_id=train_data.train_output_model_ids.mo_fp32_with_xai,
        )
    except Exception as err:
        logger.error("Error occurred during model activation", exc_info=err)
        raise EvaluationFailedException from err

    report_post_model_acceptance_progress(progress=100, message="Trained model is activated")

    # Inference on task
    report_task_infer_progress(progress=0, message="Generating task-level predictions on unannotated media")
    try:
        task_infer_on_unannotated(
            train_data=train_data.train_data,
            training_dataset_id=train_data.dataset_id,
            train_inference_subset_id=train_inference_subset_id,
            model_id=train_data.train_output_model_ids.mo_fp32_with_xai,
            progress_callback=report_task_infer_progress,
        )
    except Exception:
        logger.exception(
            "Task inference on unannotated data failed; model is accepted but batch predictions won't be available"
        )
        report_task_infer_progress(
            progress=100, message="Failed to generate task-level predictions on unannotated media"
        )
        # if task inference doesn't work, skip pipeline inference because it would likely fail too
        infer_on_pipeline = False

    # Inference on pipeline
    if not infer_on_pipeline:
        report_pipeline_infer_progress(100, "Skipped generating task-chain predictions on unannotated media")
        return

    report_pipeline_infer_progress(0, "Generating task-chain predictions on unannotated media")
    try:
        pipeline_infer_on_unannotated(
            train_data=train_data.train_data, progress_callback=report_pipeline_infer_progress
        )
    except Exception:
        logger.exception(
            "Pipeline inference on unannotated data failed; model is accepted but batch predictions won't be available"
        )
        report_pipeline_infer_progress(
            progress=100, message="Failed to generate task-chain predictions on unannotated media"
        )

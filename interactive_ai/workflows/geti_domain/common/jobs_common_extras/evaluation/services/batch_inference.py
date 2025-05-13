# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the BatchInference class"""

import logging
import os
import time
from collections.abc import Callable, Sequence

from geti_telemetry_tools import unified_tracing
from geti_telemetry_tools.tracing.common import tracer
from geti_types import DatasetStorageIdentifier, ProjectIdentifier
from iai_core.entities.annotation import AnnotationScene
from iai_core.entities.datasets import Dataset
from iai_core.entities.evaluation_result import EvaluationPurpose, EvaluationResult
from iai_core.entities.metadata import IMetadata
from iai_core.entities.model import Model, NullModel
from iai_core.entities.task_node import TaskNode
from iai_core.repos import EvaluationResultRepo
from iai_core.utils.post_process_predictions import PostProcessPredictionsUtils

from jobs_common.exceptions import CommandInitializationFailedException
from jobs_common.tasks.utils.progress import ProgressRange
from jobs_common.utils.progress_helper import noop_progress_callback
from jobs_common_extras.evaluation.entities.batch_inference_dataset import BatchInferenceDataset
from jobs_common_extras.evaluation.services.inferencer import (
    AnomalyInferencer,
    ClassificationInferencer,
    InferencerFactory,
)

ASYNC_INFERENCE_SIZE_MB_THRESHOLD = int(os.environ.get("ASYNC_INFERENCE_SIZE_MB_THRESHOLD", 150))
ASYNC_INFERENCE_GIGAFLOPS_THRESHOLD = int(os.environ.get("ASYNC_INFERENCE_GIGAFLOPS_THRESHOLD", 400))
ASYNC_INFERENCE_MODEL_TEMPLATE_ID_BLACKLIST = [
    "Custom_Counting_Instance_Segmentation_MaskRCNN_SwinT_FP16",
    "visual_prompting_model",
]

logger = logging.getLogger(__name__)


class BatchInference:
    """
    Represents a batch inference operation (performed using ModelAPI).
    This class holds all data needed for the inference, which is triggered by calling the method `run()`.

    :param project_identifier: project containing the model and datasets
    :param task_node: task node to which the model belong to
    :param model: model used for inference
    :param batch_inference_datasets: list of BatchInferenceDataset for which to run inference
    :param progress_callback: callback function to update progress
    :param progress_message: string message to use when updating the progress
    :param max_async_requests: Maximum number of concurrent requests that the asynchronous inferencer can make.
        Defaults to 0 (OpenVINO will try to select an optimal value based on the number of available CPU cores).
    :param progress_start: Start value used for progress reporting. Will start at 0 if unset
    :param progress_end: Start value used for progress reporting. Will end at 100 if unset
    """

    def __init__(  # noqa: PLR0913
        self,
        project_identifier: ProjectIdentifier,
        task_node: TaskNode,
        model: Model,
        batch_inference_datasets: Sequence[BatchInferenceDataset],
        progress_callback: Callable[[float, str], None] = noop_progress_callback,
        progress_message: str = "Inferring on dataset",
        max_async_requests: int = 0,
        progress_range: ProgressRange = ProgressRange(),
    ):
        self._set_async_inference_env_vars(max_async_requests=max_async_requests)
        self._validate_model(model)
        self._validate_datasets(batch_inference_datasets=batch_inference_datasets, task_node=task_node)
        # TODO: remove dataset storage after CVS-130844
        self.dataset_storage = batch_inference_datasets[0].dataset_storage
        self.project_identifier = project_identifier
        self.task_node = task_node
        self.model = model
        self.inferencer = InferencerFactory.create_inferencer(model=model, max_async_requests=max_async_requests)
        self.batch_inference_datasets = batch_inference_datasets
        self.progress_callback = progress_callback
        self.progress_message = progress_message
        self._progress: int = 0  # progress counter
        self._progress_pct: int = progress_range.start  # progress percentage
        self.total_progress_size = sum([len(batch_ds.input_dataset) for batch_ds in batch_inference_datasets])
        self.progress_start = progress_range.start
        self.progress_end = progress_range.end

    @property
    def output_datasets(self) -> tuple[Dataset, ...]:
        return tuple(ds.output_dataset for ds in self.batch_inference_datasets if ds.output_dataset is not None)

    def _create_evaluation_results(self) -> None:
        for dataset in self.batch_inference_datasets:
            if (
                dataset.annotated_dataset is None
                or dataset.evaluation_purpose is None
                or dataset.evaluation_result is not None
            ):
                continue
            if dataset.evaluation_purpose == EvaluationPurpose.MODEL_TEST:
                raise ValueError(
                    "Batch inference does not support the dynamic creation of model test results. Please manually "
                    "create the model test results and assign them to the corresponding BatchInferenceDataset."
                )
            evaluation_result = EvaluationResult(
                id_=EvaluationResultRepo.generate_id(),
                project_identifier=self.project_identifier,
                model_storage_id=self.model.model_storage.id_,
                model_id=self.model.id_,
                dataset_storage_id=self.dataset_storage.id_,
                ground_truth_dataset=dataset.annotated_dataset,
                prediction_dataset=dataset.input_dataset,
                purpose=dataset.evaluation_purpose,
            )
            EvaluationResultRepo(self.project_identifier).save(evaluation_result)
            dataset.evaluation_result = evaluation_result

    @unified_tracing
    def run(self, use_async: bool = False) -> None:
        """
        This method performs the following actions:
            - Initializes and saves the evaluation results for each inference dataset.
            - Run the batch inference on all the input datasets (in-place).

        :param use_async: whether to run the inference asynchronously
        """
        if use_async and not self._is_async_supported(self.model):
            use_async = False

        self._progress = 0  # reset progress
        logger.info("Saving evaluation results for datasets.")
        self._create_evaluation_results()
        logger.info(
            "Running batch inference on with ID '%s' (%s).",
            self.model.id_,
            self.model.precision,
        )
        for batch_dataset in self.batch_inference_datasets:
            self.infer_dataset(batch_dataset, use_async)
            with tracer.start_as_current_span("PostProcessPredictionsUtils.post_process_prediction_dataset"):
                # Make adjustments to complete the annotation scenes in the dataset:
                # - save the dataset (the input dataset has been modified in memory)
                # - set the 'purpose' of the dataset as requested
                # - reload the annotation scenes from database
                # - insert the empty label where appropriate
                # - set the label source of the predictions
                # - update the annotations 'kind' to match the dataset 'purpose'
                output_dataset = PostProcessPredictionsUtils.post_process_prediction_dataset(
                    dataset_storage=self.dataset_storage,
                    dataset=batch_dataset.input_dataset,
                    model=self.model,
                    task_node=self.task_node,
                    dataset_purpose=batch_dataset.output_dataset_purpose,
                    reload_from_db=False,
                    save_to_db=True,
                )
            batch_dataset.output_dataset = output_dataset

    @unified_tracing
    def infer_dataset(self, batch_dataset: BatchInferenceDataset, use_async: bool) -> None:
        logger.info(
            "Running %s batch inference on input dataset with ID '%s' and output dataset purpose '%s'.",
            "asynchronous" if use_async else "synchronous",
            batch_dataset.input_dataset.id_,
            batch_dataset.output_dataset_purpose.name,
        )
        total_time = time.perf_counter()
        dataset = batch_dataset.input_dataset
        dataset_storage_id = DatasetStorageIdentifier(
            workspace_id=self.project_identifier.workspace_id,
            project_id=self.project_identifier.project_id,
            dataset_storage_id=batch_dataset.dataset_storage.id_,
        )

        def add_prediction(
            dataset_item_idx: int,
            predicted_ann_scene: AnnotationScene,
            metadata: Sequence[IMetadata],
        ):
            dataset_item = dataset[dataset_item_idx]
            for data in metadata:
                dataset_item.append_metadata_item(data=data, model=self.model)

            # Add labels to ROI annotation only for classification and anomaly tasks, as they're needed for evaluation.
            # Excluding labels from other tasks helps prevent interference with task chain metrics.
            if isinstance(self.inferencer, ClassificationInferencer | AnomalyInferencer):
                predicted_labels = [label for anno in predicted_ann_scene.annotations for label in anno.get_labels()]
                dataset_item.append_labels(predicted_labels)
            else:
                dataset_item.append_annotations(predicted_ann_scene.annotations)

        for idx, dataset_item in enumerate(dataset):
            if use_async:
                self.inferencer.enqueue_prediction(
                    dataset_storage_id=dataset_storage_id,
                    item_idx=idx,
                    media=dataset_item.media,
                    result_handler=add_prediction,
                    roi=dataset_item.roi,
                )
            else:  # use sync API
                predicted_ann_scene, metadata = self.inferencer.predict(
                    dataset_storage_id=dataset_storage_id,
                    media=dataset_item.media,
                    roi=dataset_item.roi,
                )
                add_prediction(
                    dataset_item_idx=idx,
                    predicted_ann_scene=predicted_ann_scene,
                    metadata=metadata,
                )
            self._update_progress()

        if use_async:
            self.inferencer.await_all()

        total_time = time.perf_counter() - total_time
        logger.info(
            "Batch inference on dataset with ID '%s' took %s seconds (avg. per image: %s ms).",
            dataset.id_,
            total_time,
            int(total_time / len(dataset) * 1000),
        )

    def _update_progress(self) -> None:
        """Update total progress"""
        self._progress += 1
        _progress_pct = (
            int(self._progress / self.total_progress_size * (self.progress_end - self.progress_start))
            + self.progress_start
        )
        # Avoid reporting same progress multiple times
        if _progress_pct > self._progress_pct:
            self.progress_callback(_progress_pct, self.progress_message)
            self._progress_pct = _progress_pct

    @staticmethod
    def _validate_model(model: Model) -> None:
        """
        Perform sanity checks on the model

        :raises CommandInitializationFailedException: if the model is invalid
        """
        # Check that the model is not null
        if isinstance(model, NullModel):
            logger.error("Model %s to use for inference is NullModel", model.id_)
            raise CommandInitializationFailedException("Invalid model for inference")

        # Check that the model has trained weights
        if not model.has_trained_weights():
            logger.error(
                "Model %s for inference has status: %s",
                model.id_,
                model.model_status,
            )
            raise CommandInitializationFailedException("Inference model is not trained")

    @staticmethod
    def _validate_datasets(batch_inference_datasets: Sequence[BatchInferenceDataset], task_node: TaskNode) -> None:
        """
        Perform sanity checks on the batch inference datasets.

        :param batch_inference_datasets: the batch inference datasets to check.
        :param task_node: trainable task to perform inference
        :raises CommandInitializationFailedException: if an input or annotated dataset has issues
        """
        if not batch_inference_datasets:
            raise CommandInitializationFailedException(
                f"BatchInference requires at least one batch inference dataset for task {task_node.title}."
            )
        # Check that the input datasets is not empty
        for dataset in batch_inference_datasets:
            if len(dataset.input_dataset) == 0:
                logger.error(
                    "Empty inference dataset %s for task %s",
                    dataset.input_dataset.id_,
                    task_node.title,
                )
                raise CommandInitializationFailedException(
                    f"Empty inference dataset with ID {dataset.input_dataset.id_}"
                )

    @staticmethod
    def _set_async_inference_env_vars(max_async_requests: int) -> None:
        """Set the environment variables used by the openvino async inference runtime."""
        os.environ["KMP_AFFINITY"] = "granularity=fine,compact,1,0"
        if max_async_requests > 0:
            os.environ["OMP_NUM_THREADS"] = str(max_async_requests)

    @staticmethod
    def _is_async_supported(model: Model) -> bool:
        """
        Check if the model is supported for asynchronous inference. The following conditions are checked:
            - The model template is blacklisted for async inference.
            - The model exceeds the async inference thresholds for GFlops or size.

        :param model: the model to check
        :return: True if the model does support asynchronous inference, False otherwise
        """
        model_template = model.model_storage.model_template
        if model_template.model_template_id in ASYNC_INFERENCE_MODEL_TEMPLATE_ID_BLACKLIST:
            logger.warning(
                f"Model `{model.id_}` with template {model_template.name} is blacklisted for async inference."
            )
            return False
        if (
            model_template.gigaflops > ASYNC_INFERENCE_GIGAFLOPS_THRESHOLD
            or model_template.size > ASYNC_INFERENCE_SIZE_MB_THRESHOLD
        ):
            logger.warning(
                f"Model `{model.id_}` with template {model_template.name} ({model_template.gigaflops} GFlops, "
                f"{model.size} MB) exceeds the async inference thresholds."
            )
            return False
        return True

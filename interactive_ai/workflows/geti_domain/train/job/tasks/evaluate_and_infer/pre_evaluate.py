# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

"""
Pre-evaluation task module
"""

import logging
from collections.abc import Callable

from geti_telemetry_tools import unified_tracing
from jobs_common.utils.annotation_filter import AnnotationFilter
from jobs_common_extras.evaluation.entities.batch_inference_dataset import BatchInferenceDataset
from jobs_common_extras.evaluation.tasks.infer_and_evaluate import infer_and_evaluate
from jobs_common_extras.evaluation.utils.exceptions import EmptyEvaluationDatasetException
from sc_sdk.entities.annotation import AnnotationSceneKind
from sc_sdk.entities.datasets import Dataset, DatasetPurpose
from sc_sdk.entities.evaluation_result import EvaluationPurpose
from sc_sdk.entities.model import Model
from sc_sdk.entities.subset import Subset
from sc_sdk.utils.dataset_helper import DatasetHelper

from job.utils.train_workflow_data import TrainWorkflowData

logger = logging.getLogger(__name__)


@unified_tracing
def pre_evaluate(
    train_data: TrainWorkflowData,
    dataset: Dataset,
    model_to_preevaluate: Model,
    progress_callback: Callable[[float, str], None],
) -> None:
    """
    Evaluate the latest model trained in model storage (i.e. the most recent model that has the same architecture
    as the new one to be trained) on the current validation subset.

    :param train_data: train workflow data
    :param dataset: Dataset that includes items with VALIDATION subset
    :param model_to_preevaluate: OpenVino model that should be pre-evaluated. Note that this is the OpenVino model and
        not the base PyTorch model.
    :param progress_callback: A callback function to report step progress
    """
    project, task_node = train_data.get_common_entities()

    dataset_storage = project.get_training_dataset_storage()
    validation_dataset = dataset.get_subset(Subset.VALIDATION)
    filtered_validation_dataset = AnnotationFilter.apply_annotation_filters(
        dataset=validation_dataset,
        max_number_of_annotations=train_data.max_number_of_annotations,
        min_annotation_size=train_data.min_annotation_size,
    )
    if len(filtered_validation_dataset) == 0:
        raise EmptyEvaluationDatasetException(
            subset="validation",
            max_number_of_annotations=train_data.max_number_of_annotations,
            min_annotation_size=train_data.min_annotation_size,
        )

    batch_inference_datasets = [
        BatchInferenceDataset(
            dataset_storage=dataset_storage,
            input_dataset=DatasetHelper.create_dataset_with_filtered_annotations_up_to_task(
                input_dataset=filtered_validation_dataset,
                task_node=task_node,
                project=project,
                dataset_storage=dataset_storage,
                annotation_scene_kind=AnnotationSceneKind.INTERMEDIATE,
                save_to_db=False,
            ),
            annotated_dataset=filtered_validation_dataset,
            output_dataset_purpose=DatasetPurpose.EVALUATION,
            evaluation_purpose=EvaluationPurpose.PREEVALUATION,
        )
    ]
    infer_and_evaluate(
        project_identifier=project.identifier,
        task_node=task_node,
        model=model_to_preevaluate,
        batch_inference_datasets=batch_inference_datasets,
        progress_callback=progress_callback,
        progress_message="Pre-evaluating on validation dataset",
    )

# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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

from unittest.mock import MagicMock, patch

import pytest
from sc_sdk.algorithms import ModelTemplateList
from sc_sdk.entities.model_template import HyperParameterData, InstantiationType, ModelTemplate, TaskFamily, TaskType
from sc_sdk.utils.post_process_predictions import PostProcessPredictionsUtils

from jobs_common_extras.evaluation.services.batch_inference import BatchInference
from jobs_common_extras.evaluation.services.inferencer import InferencerFactory


@pytest.fixture
def fxt_model_template_blacklisted():
    hyper_parameters = HyperParameterData(base_path="")
    model_template = ModelTemplate(
        model_template_id="Custom_Counting_Instance_Segmentation_MaskRCNN_SwinT_FP16",
        model_template_path="",
        name="MaskRCNN_SwinT_FP16",
        task_type=TaskType.SEGMENTATION,
        task_family=TaskFamily.VISION,
        is_trainable=True,
        instantiation=InstantiationType.NONE,
        hyper_parameters=hyper_parameters,
        capabilities=["compute_representations"],
    )
    ModelTemplateList().register_model_template(model_template=model_template)
    yield model_template


@pytest.fixture
def fxt_model_template_large():
    hyper_parameters = HyperParameterData(base_path="")
    model_template = ModelTemplate(
        model_template_id="Object_Detection_ResNeXt101_ATSS",
        model_template_path="",
        name="ResNeXt101-ATSS",
        task_type=TaskType.DETECTION,
        task_family=TaskFamily.VISION,
        is_trainable=True,
        instantiation=InstantiationType.NONE,
        hyper_parameters=hyper_parameters,
        capabilities=["compute_representations"],
        gigaflops=434.75,
        size=344,
    )
    ModelTemplateList().register_model_template(model_template=model_template)
    yield model_template


@pytest.fixture
def fxt_model_template_small():
    hyper_parameters = HyperParameterData(base_path="")
    model_template = ModelTemplate(
        model_template_id="Custom_Counting_Instance_Segmentation_MaskRCNN_EfficientNetB2B",
        model_template_path="",
        name="MaskRCNN_EfficientNetB2B",
        task_type=TaskType.DETECTION,
        task_family=TaskFamily.VISION,
        is_trainable=True,
        instantiation=InstantiationType.NONE,
        hyper_parameters=hyper_parameters,
        capabilities=["compute_representations"],
        gigaflops=68.48,
        size=13.27,
    )
    ModelTemplateList().register_model_template(model_template=model_template)
    yield model_template


@pytest.mark.JobsComponent
class TestBatchInference:
    @pytest.mark.parametrize(
        "use_async, model_template_id, async_enabled",
        (
            (True, "Custom_Counting_Instance_Segmentation_MaskRCNN_SwinT_FP16", False),
            (True, "Object_Detection_ResNeXt101_ATSS", False),
            (True, "Custom_Counting_Instance_Segmentation_MaskRCNN_EfficientNetB2B", True),
            (False, "Custom_Counting_Instance_Segmentation_MaskRCNN_EfficientNetB2B", False),
        ),
    )
    def test_run(
        self,
        use_async,
        model_template_id,
        async_enabled,
        fxt_model_template_blacklisted,
        fxt_model_template_large,
        fxt_model_template_small,
        fxt_project_identifier,
    ) -> None:
        # Arrange
        model_template = ModelTemplateList().get_by_id(model_template_id)
        mock_model = MagicMock()
        mock_model_storage = MagicMock()
        mock_model_storage.model_template = model_template
        mock_model.model_storage = mock_model_storage
        mock_dataset = MagicMock()
        mock_dataset.input_dataset = [1, 2, 3]

        # Act
        with (
            patch.object(BatchInference, "_create_evaluation_results") as mock_create_evaluation_results,
            patch.object(InferencerFactory, "create_inferencer", return_value=MagicMock()) as mock_create_inferencer,
            patch.object(BatchInference, "infer_dataset") as mock_infer_dataset,
            patch.object(PostProcessPredictionsUtils, "post_process_prediction_dataset") as mock_post_process,
        ):
            batch_inference = BatchInference(
                project_identifier=fxt_project_identifier,
                task_node=MagicMock(),
                model=mock_model,
                batch_inference_datasets=[mock_dataset],
                max_async_requests=4,
            )
            batch_inference.run(use_async=use_async)

        # Assert
        mock_create_evaluation_results.assert_called_once()
        mock_create_inferencer.assert_called_once_with(model=mock_model, max_async_requests=4)
        mock_infer_dataset.assert_called_once_with(mock_dataset, async_enabled)
        mock_post_process.assert_called_once()

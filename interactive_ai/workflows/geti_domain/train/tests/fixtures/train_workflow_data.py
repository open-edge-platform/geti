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

from copy import deepcopy
from unittest.mock import MagicMock

import pytest
from jobs_common_extras.mlflow.utils.train_output_models import TrainOutputModelIds, TrainOutputModels

from job.utils.train_workflow_data import TrainWorkflowData, TrainWorkflowDataForFlyteTaskTrainer


@pytest.fixture
def fxt_train_output_model_ids(fxt_mongo_id) -> TrainOutputModelIds:
    return TrainOutputModelIds(
        fxt_mongo_id(0),
        fxt_mongo_id(1),
        fxt_mongo_id(2),
        fxt_mongo_id(3),
        fxt_mongo_id(4),
    )


@pytest.fixture
def fxt_train_output_models(fxt_model, fxt_train_output_model_ids) -> TrainOutputModels:
    def _create_model(id_):
        model = deepcopy(fxt_model)
        model.id_ = id_
        return model

    model_base = _create_model(fxt_train_output_model_ids.base)
    model_mo_fp32_with_xai = _create_model(fxt_train_output_model_ids.mo_fp32_with_xai)
    model_mo_fp32_without_xai = _create_model(fxt_train_output_model_ids.mo_fp32_without_xai)
    model_mo_fp16_without_xai = _create_model(fxt_train_output_model_ids.mo_fp16_without_xai)
    model_onnx = _create_model(fxt_train_output_model_ids.onnx)
    models = [
        model_base,
        model_mo_fp32_with_xai,
        model_mo_fp32_without_xai,
        model_mo_fp16_without_xai,
        model_onnx,
    ]

    return TrainOutputModels(*models)


@pytest.fixture
def mock_train_data(
    fxt_project,
    fxt_detection_node,
    fxt_configuration_1,
    fxt_norm_compiled_dataset_shards,
) -> TrainWorkflowData:
    """Mock of `TrainWorkflowData`.

    By introducing it, we can monkeypatch its member functions's return values.
    """
    train_data = MagicMock(spec=TrainWorkflowData)
    train_data.get_common_entities.return_value = (fxt_project, fxt_detection_node)
    train_data.get_hyper_parameters.return_value = fxt_configuration_1
    train_data.get_compiled_dataset_shards.return_value = fxt_norm_compiled_dataset_shards
    train_data.hyperparameters_id = "dummy_id"
    return train_data


@pytest.fixture
def fxt_train_data_for_flyte_task_trainer(
    fxt_train_data,
    fxt_dataset_id,
    fxt_train_output_model_ids,
    fxt_mongo_id,
    tmp_path,
) -> TrainWorkflowDataForFlyteTaskTrainer:
    train_data = fxt_train_data()
    tmp_file_path = tmp_path / "tmp"
    tmp_file_path.touch()
    return TrainWorkflowDataForFlyteTaskTrainer(
        train_data=train_data,
        dataset_id=str(fxt_dataset_id),
        organization_id=fxt_mongo_id(1),
        job_id=fxt_mongo_id(2),
        train_output_model_ids=fxt_train_output_model_ids,
    )

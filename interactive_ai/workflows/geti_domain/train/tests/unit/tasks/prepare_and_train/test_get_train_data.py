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
"""This module tests the get train data task"""

import os
from unittest.mock import MagicMock, patch

import pytest
from sc_sdk.entities.model import Model, NullModel
from sc_sdk.entities.project import Project
from sc_sdk.repos import ConfigurableParametersRepo, LabelSchemaRepo, ModelStorageRepo, ProjectRepo
from sc_sdk.services import ModelService

from job.tasks.prepare_and_train.get_train_data import get_train_data
from tests.unit.tasks.utils import TEST_ENV_VARS, return_none


@pytest.mark.JobsComponent
class TestGetTrainDataTask:
    workspace_id = "workspace_id"
    project_id = "project_id"
    task_id = "task_id"
    label_schema_id = "label_schema_id"
    model_storage_id = "model_storage_id"
    hyperparameters_id = "hyperparameters_id"
    active_model_id = "active_model_id"
    input_model_id = "input_model_id"

    @patch.dict(os.environ, TEST_ENV_VARS)
    @pytest.mark.parametrize("from_scratch", [True, False])
    @pytest.mark.parametrize("has_active_model", [True, False])
    @pytest.mark.parametrize("should_activate_model", [True, False])
    @pytest.mark.parametrize("infer_on_pipeline", [True, False])
    @pytest.mark.parametrize("obsolete_model", [True, False])
    @patch("job.tasks.prepare_and_train.get_train_data.select_input_model")
    @patch.object(ModelService, "get_inference_active_model")
    @patch.object(LabelSchemaRepo, "get_latest_view_by_task")
    @patch.object(Project, "get_trainable_task_node_by_id")
    @patch.object(ModelStorageRepo, "get_by_id")
    @patch.object(ProjectRepo, "get_by_id")
    @patch.object(ConfigurableParametersRepo, "get_by_id")
    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    def test_get_train_data_task(
        self,
        mocked_get_hyper_params,
        mocked_get_project,
        mocked_get_model_storage,
        mocked_get_task,
        mocked_get_label_schema,
        mocked_get_inference_active_model,
        mocked_select_input_model,
        from_scratch,
        has_active_model,
        should_activate_model,
        infer_on_pipeline,
        fxt_project,
        fxt_train_data,
        obsolete_model,
    ) -> None:
        # Arrange
        mocked_get_project.return_value = fxt_project
        mocked_get_label_schema.return_value = MagicMock(id_=self.label_schema_id)
        mocked_select_input_model.return_value = (
            None if obsolete_model else MagicMock(spec=Model, id_=self.input_model_id)
        )
        mocked_get_hyper_params.return_value = MagicMock(id=self.hyperparameters_id)
        mocked_get_model_storage.return_value = MagicMock(id_=self.model_storage_id)
        mocked_get_inference_active_model.return_value = (
            MagicMock(id_=self.active_model_id) if has_active_model else NullModel()
        )

        expected_train_data = fxt_train_data(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            task_id=self.task_id,
            label_schema_id=self.label_schema_id,
            model_storage_id=self.model_storage_id,
            hyperparameters_id=self.hyperparameters_id,
            from_scratch=from_scratch if not obsolete_model else True,
            should_activate_model=should_activate_model,
            infer_on_pipeline=infer_on_pipeline,
            active_model_id=self.active_model_id if has_active_model else "",
            input_model_id=self.input_model_id if not obsolete_model else None,
        )

        # Act
        train_data = get_train_data(
            project_id=fxt_project.id_,
            task_id=self.task_id,
            from_scratch=from_scratch,
            should_activate_model=should_activate_model,
            infer_on_pipeline=infer_on_pipeline,
            model_storage_id=self.model_storage_id,
            hyper_parameters_id=self.hyperparameters_id,
        )

        # Assert
        assert train_data == expected_train_data

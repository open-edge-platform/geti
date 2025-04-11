# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
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

import jobs_common.tasks.utils.secrets
import pytest

from tests.unit.tasks.mock_utils import mock_decorator

patch("jobs_common.tasks.utils.progress.task_progress", mock_decorator).start()
from job.tasks.optimization_task import shard_dataset_prepare_models_and_start_optimization  # noqa: E402


@pytest.mark.JobsComponent
@patch.object(jobs_common.tasks.utils.secrets, "set_env_vars", return_value=None)
@patch.object(jobs_common.tasks.utils.secrets, "setup_session_from_env", return_value=None)
class TestOptimizationTask:
    @pytest.mark.parametrize("enable_optimize_from_dataset_shard", [True, False])
    @patch("job.tasks.optimization_task.lock_project")
    @patch("job.tasks.optimization_task.ProjectRepo")
    @patch("job.tasks.optimization_task.ModelRepo")
    @patch("job.tasks.optimization_task.shard_dataset")
    @patch("job.tasks.optimization_task.prepare_optimize")
    @patch("job.tasks.optimization_task.create_flyte_container_task")
    def test_shard_dataset_prepare_models_and_start_optimization(
        self,
        mock_create_flyte_container_task,
        mock_prepare_optimize,
        mock_shard_dataset,
        mock_model_repo,
        mock_project_repo,
        mock_lock_project,
        mock_setup_session_from_env,
        mock_set_env_vars,
        fxt_optimization_trainer_ctx,
        enable_optimize_from_dataset_shard,
    ):
        # Arrange
        project_id = "project_id"
        model_storage_id = "model_storage_id"
        model_id = "model_id"
        max_shard_size = 100
        optimization_type = "type"
        command = ["command"]
        num_image_pulling_threads = 10
        num_upload_threads = 2
        enable_optimize_from_dataset_shard = True
        min_annotation_size = 10
        max_number_of_annotations = 100

        mock_project_repo().get_by_id.return_value = MagicMock()
        mock_model_repo().get_by_id.return_value = MagicMock()
        mock_shard_dataset.return_value = "compiled_dataset_shards_id"
        mock_prepare_optimize.return_value = fxt_optimization_trainer_ctx

        # Act
        result = shard_dataset_prepare_models_and_start_optimization(
            project_id=project_id,
            model_storage_id=model_storage_id,
            model_id=model_id,
            max_shard_size=max_shard_size,
            optimization_type=optimization_type,
            command=command,
            num_image_pulling_threads=num_image_pulling_threads,
            num_upload_threads=num_upload_threads,
            enable_optimize_from_dataset_shard=enable_optimize_from_dataset_shard,
            min_annotation_size=min_annotation_size,
            max_number_of_annotations=max_number_of_annotations,
        )

        # Assert
        if enable_optimize_from_dataset_shard:
            mock_lock_project.assert_called_once()
            mock_project_repo().get_by_id.assert_called_once()
            mock_model_repo().get_by_id.assert_called_once()
            mock_shard_dataset.assert_called_once()
        else:
            mock_lock_project.assert_not_called()
            mock_project_repo().get_by_id.assert_not_called()
            mock_model_repo().get_by_id.assert_not_called()
            mock_shard_dataset.assert_not_called()
        mock_prepare_optimize.assert_called_once()
        mock_create_flyte_container_task.assert_called_once()
        assert result == fxt_optimization_trainer_ctx

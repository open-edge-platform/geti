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
from unittest.mock import patch

import pytest
from sc_sdk.services.model_service import ModelService
from testfixtures import compare

from job.commands.update_active_model_command import UpdateActiveModelCommand


def do_nothing(self, *args, **kwargs) -> None:
    return None


@pytest.mark.JobsComponent
class TestUpdateActiveModelCommand:
    @pytest.fixture
    def fxt_update_active_model_command(
        self,
        fxt_trainable_task,
        fxt_model_storage_detection,
        fxt_model_storage_detection_2,
    ):
        fxt_trainable_task._active_model_storage = fxt_model_storage_detection
        with (
            patch.object(
                ModelService,
                "get_active_model_storage",
                return_value=fxt_model_storage_detection,
            ),
            patch.object(ModelService, "activate_model_storage"),
        ):
            cmd = UpdateActiveModelCommand(
                task_node=fxt_trainable_task,
                new_model_storage=fxt_model_storage_detection_2,
            )
            compare(cmd.old_model_storage, fxt_model_storage_detection, ignore_eq=True)
            compare(cmd.new_model_storage, fxt_model_storage_detection_2, ignore_eq=True)
            compare(
                cmd.task_node._active_model_storage,
                cmd.old_model_storage,
                ignore_eq=True,
            )
            assert cmd.task_node._active_model_storage != cmd.new_model_storage
            yield cmd

    def test_execute(
        self,
        fxt_update_active_model_command,
    ):
        # Arrange
        cmd = fxt_update_active_model_command

        # Act
        with patch.object(ModelService, "activate_model_storage") as patched_activate_model_storage:
            cmd.execute()

        # Assert
        patched_activate_model_storage.assert_called_once_with(
            model_storage=cmd.new_model_storage,
        )

    def test_revert(
        self,
        fxt_update_active_model_command,
    ):
        # Arrange
        cmd = fxt_update_active_model_command

        # Act
        with patch.object(ModelService, "activate_model_storage") as patched_activate_model_storage:
            cmd.revert_command()

        # Assert
        patched_activate_model_storage.assert_called_once_with(
            model_storage=cmd.old_model_storage,
        )

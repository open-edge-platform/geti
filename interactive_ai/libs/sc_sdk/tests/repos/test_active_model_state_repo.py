#
# INTEL CONFIDENTIAL
# Copyright (c) 2021 Intel Corporation
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material contains trade secrets and proprietary
# and confidential information of Intel or its suppliers and licensors. The
# Material is protected by worldwide copyright and trade secret laws and treaty
# provisions. No part of the Material may be used, copied, reproduced, modified,
# published, uploaded, posted, transmitted, distributed, or disclosed in any way
# without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
#
from unittest.mock import patch

import pytest

from sc_sdk.entities.active_model_state import ActiveModelState
from sc_sdk.repos import ActiveModelStateRepo


@pytest.mark.ScSdkComponent
class TestActiveModelStateRepo:
    def test_indexes(self, fxt_project_identifier) -> None:
        active_model_state_repo = ActiveModelStateRepo(fxt_project_identifier)

        indexes_names = set(active_model_state_repo._collection.index_information().keys())

        assert indexes_names == {
            "_id_",
            "organization_id_-1_workspace_id_-1_project_id_-1__id_1",
        }

    def test_get_by_task_node_id(self, fxt_active_model_state_repo, fxt_active_model_state) -> None:
        # Arrange
        repo = fxt_active_model_state_repo
        task_node_id = fxt_active_model_state.task_node_id

        # Act
        with patch.object(repo, "get_by_id", return_value=fxt_active_model_state) as mock_get_by_id:
            active_model_state = repo.get_by_task_node_id(task_node_id=task_node_id)

        # Assert
        mock_get_by_id.assert_called_once_with(task_node_id)
        assert active_model_state == fxt_active_model_state

    def test_delete_by_task_node_id(self, fxt_active_model_state_repo, fxt_active_model_state) -> None:
        # Arrange
        repo = fxt_active_model_state_repo
        task_node_id = fxt_active_model_state.task_node_id

        # Act
        with patch.object(repo, "delete_by_id") as mock_delete_by_id:
            repo.delete_by_task_node_id(task_node_id=task_node_id)

        # Assert
        mock_delete_by_id.assert_called_once_with(task_node_id)

    @pytest.fixture
    def fxt_active_model_state(self, fxt_ote_id, fxt_model_storage_classification):
        yield ActiveModelState(
            task_node_id=fxt_ote_id(11),
            active_model_storage=fxt_model_storage_classification,
        )

    @pytest.fixture
    def fxt_active_model_state_repo(self, fxt_empty_project_persisted):
        repo = ActiveModelStateRepo(fxt_empty_project_persisted.identifier)
        yield repo

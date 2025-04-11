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
from freezegun import freeze_time

from entities.auto_train_activation import AutoTrainActivation, NullAutoTrainActivation
from storage.mappers.auto_train_activation_mapper import AutoTrainActivationToMongo
from storage.repos.auto_train_activation_repo import ProjectBasedAutoTrainActivationRepo

from geti_types import ProjectIdentifier
from sc_sdk.services import ModelService


@pytest.fixture
def fxt_auto_train_activation(fxt_ote_id, fxt_session_ctx):
    yield AutoTrainActivation(
        task_node_id=fxt_ote_id(11),
        model_storage_id=fxt_ote_id(22),
        session=fxt_session_ctx,
        ready=False,
        ephemeral=False,
    )


@pytest.mark.ScSdkComponent
class TestAutoTrainActivationRepo:
    @freeze_time("2011-11-11 11:11:11")
    def test_auto_train_activation_repo(self, request, fxt_ote_id) -> None:
        # Arrange
        project_identifier = ProjectIdentifier(workspace_id=fxt_ote_id(1), project_id=fxt_ote_id(2))
        repo = ProjectBasedAutoTrainActivationRepo(project_identifier)
        request.addfinalizer(lambda: repo.delete_all())

        # Act

        # Assert
        assert repo.forward_map == AutoTrainActivationToMongo.forward
        assert repo.backward_map == AutoTrainActivationToMongo.backward
        assert repo.null_object == NullAutoTrainActivation()

    def test_upsert_timestamp_for_task(self, request, fxt_ote_id, fxt_auto_train_activation) -> None:
        # Arrange
        project_identifier = ProjectIdentifier(workspace_id=fxt_ote_id(1), project_id=fxt_ote_id(2))
        repo = ProjectBasedAutoTrainActivationRepo(project_identifier)
        request.addfinalizer(lambda: repo.delete_all())

        # Act
        fxt_auto_train_activation.ready = True
        repo.upsert_timestamp_for_task(instance=fxt_auto_train_activation)

        # Assert
        result = repo.get_by_id(fxt_auto_train_activation.id_)
        assert result.ready is False

    def test_set_auto_train_readiness_by_task_id(
        self, request, fxt_ote_id, fxt_auto_train_activation, fxt_model_storage
    ) -> None:
        # Arrange
        project_identifier = ProjectIdentifier(workspace_id=fxt_ote_id(1), project_id=fxt_ote_id(2))
        repo = ProjectBasedAutoTrainActivationRepo(project_identifier)
        request.addfinalizer(lambda: repo.delete_all())

        # Act & Assert
        with pytest.raises(ValueError):
            repo.set_auto_train_readiness_by_task_id(task_node_id=fxt_auto_train_activation.id_, readiness=True)
        repo.save(fxt_auto_train_activation)

        result_a = repo.get_by_id(fxt_auto_train_activation.id_)
        assert result_a.ready is False

        with patch.object(
            ModelService, "get_active_model_storage", return_value=fxt_model_storage
        ) as mock_get_active_model_storage:
            repo.set_auto_train_readiness_by_task_id(task_node_id=fxt_auto_train_activation.id_, readiness=True)

        mock_get_active_model_storage.assert_called_once_with(
            project_identifier=project_identifier, task_node_id=fxt_auto_train_activation.id_
        )
        result_b = repo.get_by_id(fxt_auto_train_activation.id_)
        assert result_b.ready is True
        assert result_b.model_storage_id == fxt_model_storage.id_

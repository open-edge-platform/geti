# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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

from active_learning.interactors import ActiveMapper
from active_learning.usecases import ActiveScoresUpdateUseCase


class TestActiveScoresUpdateUseCase:
    @pytest.mark.parametrize("asynchronous", (False, True))
    def test_on_output_datasets_and_metadata_created(
        self, asynchronous, fxt_media_identifier_factory, fxt_ote_id
    ) -> None:
        workspace_id = fxt_ote_id(1)
        project_id = fxt_ote_id(2)
        dataset_storage_id = fxt_ote_id(3)
        task_node_id = fxt_ote_id(4)
        model_storage_id = fxt_ote_id(5)
        model_id = fxt_ote_id(6)
        annotated_dataset_id = fxt_ote_id(7)
        train_dataset_with_predictions_id = fxt_ote_id(8)
        unannotated_dataset_with_predictions_id = fxt_ote_id(9)
        update_method_to_mock = "update_active_scores_async" if asynchronous else "update_active_scores"
        with patch.object(ActiveMapper, update_method_to_mock) as mock_update_scores:
            ActiveScoresUpdateUseCase.on_output_datasets_and_metadata_created(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                task_node_id=task_node_id,
                model_storage_id=model_storage_id,
                model_id=model_id,
                annotated_dataset_id=annotated_dataset_id,
                train_dataset_with_predictions_id=train_dataset_with_predictions_id,
                unannotated_dataset_with_predictions_id=unannotated_dataset_with_predictions_id,
                asynchronous=asynchronous,
            )

        mock_update_scores.assert_called_once_with(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
            task_node_id=task_node_id,
            model_storage_id=model_storage_id,
            model_id=model_id,
            annotated_dataset_id=annotated_dataset_id,
            train_dataset_with_predictions_id=train_dataset_with_predictions_id,
            unannotated_dataset_with_predictions_id=unannotated_dataset_with_predictions_id,
        )

    @pytest.mark.parametrize("asynchronous", (False, True))
    def test_on_media_uploaded(self, asynchronous, fxt_media_identifier_factory, fxt_ote_id) -> None:
        workspace_id = fxt_ote_id(1)
        project_id = fxt_ote_id(2)
        dataset_storage_id = fxt_ote_id(3)
        new_media = (fxt_media_identifier_factory(1), fxt_media_identifier_factory(2))
        init_method_to_mock = "init_active_scores_async" if asynchronous else "init_active_scores"
        with (
            patch.object(
                ActiveScoresUpdateUseCase, "_is_training_dataset_storage", return_value=True
            ) as mock_is_main_storage,
            patch.object(ActiveMapper, init_method_to_mock) as mock_init_scores,
        ):
            ActiveScoresUpdateUseCase.on_media_uploaded(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                media_identifiers=new_media,
                asynchronous=asynchronous,
            )

        mock_is_main_storage.assert_called_once()
        mock_init_scores.assert_called_once_with(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
            media_identifiers=new_media,
        )

    @pytest.mark.parametrize("asynchronous", (False, True))
    def test_on_media_deleted(self, asynchronous, fxt_media_identifier_factory, fxt_ote_id) -> None:
        workspace_id = fxt_ote_id(1)
        project_id = fxt_ote_id(2)
        dataset_storage_id = fxt_ote_id(3)
        del_media = (fxt_media_identifier_factory(1), fxt_media_identifier_factory(2))
        remove_method_to_mock = "remove_media_async" if asynchronous else "remove_media"
        with (
            patch.object(
                ActiveScoresUpdateUseCase, "_is_training_dataset_storage", return_value=True
            ) as mock_is_main_storage,
            patch.object(ActiveMapper, remove_method_to_mock, return_value=None) as mock_remove_media,
        ):
            ActiveScoresUpdateUseCase.on_media_deleted(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                media_identifiers=del_media,
                asynchronous=asynchronous,
            )

        mock_is_main_storage.assert_called_once()
        mock_remove_media.assert_called_once_with(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
            media_identifiers=del_media,
        )

    @pytest.mark.parametrize("asynchronous", (False, True))
    def test_on_project_deleted(self, asynchronous, fxt_media_identifier_factory, fxt_ote_id) -> None:
        workspace_id = fxt_ote_id(1)
        project_id = fxt_ote_id(2)
        dataset_storage_id = fxt_ote_id(3)
        remove_method_to_mock = "remove_media_async" if asynchronous else "remove_media"
        with patch.object(ActiveMapper, remove_method_to_mock, return_value=None) as mock_remove_media:
            ActiveScoresUpdateUseCase.on_project_deleted(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                asynchronous=asynchronous,
            )

        mock_remove_media.assert_called_once_with(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
            media_identifiers=None,
        )

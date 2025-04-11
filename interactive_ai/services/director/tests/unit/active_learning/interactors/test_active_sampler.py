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

from typing import TYPE_CHECKING
from unittest.mock import call, patch

from active_learning.entities import ActiveScoreSuggestionInfo
from active_learning.entities.active_manager import PipelineActiveManager, TaskActiveManager
from active_learning.interactors import ActiveSampler

from geti_types import ID

if TYPE_CHECKING:
    from geti_types import MediaIdentifierEntity


class TestActiveSampler:
    def test_get_active_set_task_level(self, fxt_task_active_manager, fxt_media_identifier_factory, fxt_ote_id) -> None:
        workspace_id: ID = fxt_ote_id(1)
        project_id: ID = fxt_ote_id(2)
        dataset_storage_id: ID = fxt_ote_id(3)
        task_node_id: ID = fxt_ote_id(5)
        model_id: ID = fxt_ote_id(5)
        media_identifier_1: MediaIdentifierEntity = fxt_media_identifier_factory(1)
        media_identifier_2: MediaIdentifierEntity = fxt_media_identifier_factory(2)
        dummy_user = ID("test_user")
        suggestions = (
            ActiveScoreSuggestionInfo(media_identifier_1, 0.4, (model_id,)),
            ActiveScoreSuggestionInfo(media_identifier_2, 0.5, (model_id,)),
        )
        with (
            patch.object(
                ActiveSampler, "_get_active_manager", return_value=fxt_task_active_manager
            ) as mock_get_active_manager,
            patch.object(TaskActiveManager, "get_suggestions", return_value=suggestions) as mock_get_suggestions,
            patch.object(TaskActiveManager, "mark_as_suggested") as mock_mark_suggested,
        ):
            active_set = ActiveSampler.get_active_set_task_level(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                task_id=task_node_id,
                size=2,
                user_id=dummy_user,
            )

        mock_get_active_manager.assert_called_once_with(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
            task_node_id=task_node_id,
        )
        mock_get_suggestions.assert_called_once_with(size=2)
        mock_mark_suggested.assert_called_once_with(
            suggested_media_info=suggestions,
            user_id=dummy_user,
            reason=f"Good candidate task-level ({fxt_task_active_manager.task_node_id})",
        )
        assert active_set == (media_identifier_1, media_identifier_2)

    def test_get_active_set_task_level_with_reset(
        self, fxt_task_active_manager, fxt_media_identifier_factory, fxt_ote_id
    ) -> None:
        """
        Test 'get_active_set_task_level' when all the media have been already suggested
        """
        workspace_id: ID = fxt_ote_id(1)
        project_id: ID = fxt_ote_id(2)
        dataset_storage_id: ID = fxt_ote_id(3)
        task_node_id: ID = fxt_ote_id(4)
        model_id: ID = fxt_ote_id(5)
        media_identifier_1: MediaIdentifierEntity = fxt_media_identifier_factory(1)
        media_identifier_2: MediaIdentifierEntity = fxt_media_identifier_factory(2)
        dummy_user = ID("test_user")
        suggestions = [
            # first invocation, no suggestions (all media already suggested)
            (),
            # second invocation, after reset
            (
                ActiveScoreSuggestionInfo(media_identifier_1, 0.4, (model_id,)),
                ActiveScoreSuggestionInfo(media_identifier_2, 0.5, (model_id,)),
            ),
        ]
        with (
            patch.object(
                ActiveSampler, "_get_active_manager", return_value=fxt_task_active_manager
            ) as mock_get_active_manager,
            patch.object(TaskActiveManager, "reset_suggestions") as mock_reset_suggestions,
            patch.object(TaskActiveManager, "get_suggestions", side_effect=suggestions) as mock_get_suggestions,
            patch.object(TaskActiveManager, "mark_as_suggested") as mock_mark_suggested,
        ):
            active_set = ActiveSampler.get_active_set_task_level(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                task_id=task_node_id,
                size=2,
                user_id=dummy_user,
            )

        mock_get_active_manager.assert_called_once_with(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
            task_node_id=task_node_id,
        )
        mock_reset_suggestions.assert_called_once()
        mock_get_suggestions.assert_has_calls([call(size=2), call(size=2)])
        mock_mark_suggested.assert_called_once_with(
            suggested_media_info=suggestions[1],
            user_id=dummy_user,
            reason=f"Good candidate task-level ({fxt_task_active_manager.task_node_id})",
        )
        assert active_set == (media_identifier_1, media_identifier_2)

    def test_get_active_set_project_level(
        self, fxt_pipeline_active_manager, fxt_media_identifier_factory, fxt_ote_id
    ) -> None:
        workspace_id: ID = fxt_ote_id(1)
        project_id: ID = fxt_ote_id(2)
        dataset_storage_id: ID = fxt_ote_id(3)
        model_id: ID = fxt_ote_id(4)
        media_identifier_1: MediaIdentifierEntity = fxt_media_identifier_factory(1)
        media_identifier_2: MediaIdentifierEntity = fxt_media_identifier_factory(2)
        dummy_user = ID("test_user")
        suggestions = (
            ActiveScoreSuggestionInfo(media_identifier_1, 0.4, (model_id,)),
            ActiveScoreSuggestionInfo(media_identifier_2, 0.5, (model_id,)),
        )
        with (
            patch.object(
                ActiveSampler,
                "_get_active_manager",
                return_value=fxt_pipeline_active_manager,
            ) as mock_get_active_manager,
            patch.object(PipelineActiveManager, "get_suggestions", return_value=suggestions) as mock_get_suggestions,
            patch.object(PipelineActiveManager, "mark_as_suggested") as mock_mark_suggested,
        ):
            active_set = ActiveSampler.get_active_set_project_level(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                size=2,
                user_id=dummy_user,
            )

        mock_get_active_manager.assert_called_once_with(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
        )
        mock_get_suggestions.assert_called_once_with(size=2)
        mock_mark_suggested.assert_called_once_with(
            suggested_media_info=suggestions,
            user_id=dummy_user,
            reason="Good candidate project-level",
        )
        assert active_set == (media_identifier_1, media_identifier_2)

    def test_get_active_set_project_level_with_reset(
        self, fxt_pipeline_active_manager, fxt_media_identifier_factory, fxt_ote_id
    ) -> None:
        """
        Test 'get_active_set_project_level' when all the media have been already suggested
        """
        workspace_id: ID = fxt_ote_id(1)
        project_id: ID = fxt_ote_id(2)
        dataset_storage_id: ID = fxt_ote_id(3)
        model_id: ID = fxt_ote_id(4)
        media_identifier_1: MediaIdentifierEntity = fxt_media_identifier_factory(1)
        media_identifier_2: MediaIdentifierEntity = fxt_media_identifier_factory(2)
        dummy_user = ID("test_user")
        suggestions = [
            # first invocation, no suggestions (all media already suggested)
            (),
            # second invocation, after reset
            (
                ActiveScoreSuggestionInfo(media_identifier_1, 0.4, (model_id,)),
                ActiveScoreSuggestionInfo(media_identifier_2, 0.5, (model_id,)),
            ),
        ]
        with (
            patch.object(
                ActiveSampler,
                "_get_active_manager",
                return_value=fxt_pipeline_active_manager,
            ) as mock_get_active_manager,
            patch.object(PipelineActiveManager, "reset_suggestions") as mock_reset_suggestions,
            patch.object(PipelineActiveManager, "get_suggestions", side_effect=suggestions) as mock_get_suggestions,
            patch.object(PipelineActiveManager, "mark_as_suggested") as mock_mark_suggested,
        ):
            active_set = ActiveSampler.get_active_set_project_level(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                size=2,
                user_id=dummy_user,
            )

        mock_get_active_manager.assert_called_once_with(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
        )
        mock_reset_suggestions.assert_called_once()
        mock_get_suggestions.assert_has_calls([call(size=2), call(size=2)])
        mock_mark_suggested.assert_called_once_with(
            suggested_media_info=suggestions[1],
            user_id=dummy_user,
            reason="Good candidate project-level",
        )
        assert active_set == (media_identifier_1, media_identifier_2)

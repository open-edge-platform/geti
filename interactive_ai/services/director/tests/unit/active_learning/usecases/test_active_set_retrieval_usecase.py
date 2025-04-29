# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import patch

from active_learning.interactors import ActiveSampler
from active_learning.usecases import ActiveSetRetrievalUseCase

from geti_types import ID


class TestActiveSetRetrievalUseCase:
    def test_get_active_set_task_level(self, fxt_media_identifier_factory, fxt_ote_id) -> None:
        workspace_id = fxt_ote_id(1)
        project_id = fxt_ote_id(2)
        dataset_storage_id = fxt_ote_id(3)
        task_id = fxt_ote_id(4)
        active_set = (fxt_media_identifier_factory(1), fxt_media_identifier_factory(2))
        with patch.object(ActiveSampler, "get_active_set_task_level", return_value=active_set) as mock_get_active_set:
            result = ActiveSetRetrievalUseCase.get_active_set_task_level(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                task_id=task_id,
                size=2,
                user_id=ID("dummy_user"),
            )

        mock_get_active_set.assert_called_once_with(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
            task_id=task_id,
            size=2,
            user_id=ID("dummy_user"),
        )
        assert result == active_set

    def test_get_active_set_project_level(self, fxt_media_identifier_factory, fxt_ote_id) -> None:
        workspace_id = fxt_ote_id(1)
        project_id = fxt_ote_id(2)
        dataset_storage_id = fxt_ote_id(3)
        active_set = (fxt_media_identifier_factory(1), fxt_media_identifier_factory(2))
        with patch.object(
            ActiveSampler, "get_active_set_project_level", return_value=active_set
        ) as mock_get_active_set:
            result = ActiveSetRetrievalUseCase.get_active_set_project_level(
                workspace_id=workspace_id,
                project_id=project_id,
                dataset_storage_id=dataset_storage_id,
                size=2,
                user_id=ID("dummy_user"),
            )

        mock_get_active_set.assert_called_once_with(
            workspace_id=workspace_id,
            project_id=project_id,
            dataset_storage_id=dataset_storage_id,
            size=2,
            user_id=ID("dummy_user"),
        )
        assert result == active_set

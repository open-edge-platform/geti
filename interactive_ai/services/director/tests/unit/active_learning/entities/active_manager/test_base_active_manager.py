# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from collections.abc import Sequence
from unittest.mock import patch

import pytest

from active_learning.entities import ActiveLearningProjectConfig, ActiveScoreSuggestionInfo
from active_learning.entities.active_manager.base_active_manager import BaseActiveManager
from active_learning.storage.repos import ActiveScoreRepo, ActiveSuggestionRepo

from geti_types import ID, MediaIdentifierEntity, VideoIdentifier
from sc_sdk.entities.video import Video
from sc_sdk.repos import DatasetStorageRepo, ProjectRepo, VideoRepo
from sc_sdk.services import ModelService


def do_nothing(*args, **kwargs):
    pass


# Since the BaseActiveManager class is abstract, for testing purposes we use
# a concrete implementation that defines the abstract method.
@pytest.fixture
def fxt_base_active_manager_testable(mock_project_repo, mock_dataset_storage_repo, fxt_project):
    class BaseActiveManagerTestable(BaseActiveManager):
        def __init__(self, workspace_id: ID, project_id: ID, dataset_storage_id: ID) -> None:
            super().__init__(workspace_id, project_id, dataset_storage_id)

        def get_configuration(self) -> ActiveLearningProjectConfig:
            return ActiveLearningProjectConfig()  # type: ignore[call-arg]

        def _get_unannotated_media_identifiers(
            self,
        ) -> list[MediaIdentifierEntity]:
            raise NotImplementedError

        def _get_best_candidates(
            self,
            candidates: Sequence[MediaIdentifierEntity],
            size: int,
            models_ids: Sequence[ID] | None = None,
        ) -> tuple[ActiveScoreSuggestionInfo, ...]:
            raise NotImplementedError

    def _build_manager(workspace_id: ID, project_id: ID, dataset_storage_id: ID):
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project),
            patch.object(
                DatasetStorageRepo,
                "get_by_id",
                return_value=fxt_project.get_training_dataset_storage(),
            ),
            patch.object(ActiveSuggestionRepo, "__init__", new=do_nothing),
            patch.object(ActiveScoreRepo, "__init__", new=do_nothing),
        ):
            active_manager = BaseActiveManagerTestable(workspace_id, project_id, dataset_storage_id)
            # load the caches
            active_manager.get_project()
            active_manager.get_dataset_storage()
            return active_manager

    yield _build_manager


class TestBaseActiveManager:
    def test_get_suggestions(
        self,
        fxt_ote_id,
        fxt_base_active_manager_testable,
        fxt_project,
        fxt_media_identifier_factory,
    ) -> None:
        model_id = fxt_ote_id(100)
        active_manager = fxt_base_active_manager_testable(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            dataset_storage_id=fxt_project.get_training_dataset_storage().id_,
        )
        # media 0: unannotated inferred
        # media 1: unannotated non-inferred
        # media 2: unannotated non-inferred
        # media 3: unannotated suggested
        unannotated_media = [fxt_media_identifier_factory(i) for i in range(4)]
        non_suggested_media = tuple(fxt_media_identifier_factory(i) for i in range(3))

        def dummy_get_best_candidates(candidates, size, models_ids):
            selected = non_suggested_media[:size]
            return tuple(
                ActiveScoreSuggestionInfo(
                    media_identifier=media,
                    score=0.3 if media == fxt_media_identifier_factory(0) else 1.0,
                    models_ids=(model_id,),
                )
                for media in selected
            )

        with (
            patch.object(ModelService, "get_inference_active_model_id", return_value=model_id),
            patch.object(
                active_manager,
                "_get_unannotated_non_suggested_media_identifiers",
                return_value=iter(unannotated_media),
            ) as mock_get_unannotated,
            patch.object(
                active_manager,
                "_get_best_candidates",
                side_effect=dummy_get_best_candidates,
            ) as mock_get_best_candidates,
        ):
            suggestions = active_manager.get_suggestions(size=2)
            suggested_media = {sug.media_identifier for sug in suggestions}

        mock_get_unannotated.assert_called_once()
        mock_get_best_candidates.assert_called_once_with(
            candidates=unannotated_media,
            size=2,
            models_ids=[model_id],
        )
        assert len(suggestions) == 2
        assert len(set(suggested_media)) == 2
        assert fxt_media_identifier_factory(0) in suggested_media
        assert fxt_media_identifier_factory(3) not in suggested_media

    def test_init_scores(
        self,
        fxt_base_active_manager_testable,
        fxt_project,
        fxt_video_entity,
        fxt_media_identifier_factory,
        fxt_ote_id,
    ) -> None:
        fxt_video_entity.stride = 10
        with (
            patch.object(Video, "total_frames", return_value=100),
            patch.object(Video, "fps", return_value=10),
        ):
            active_manager = fxt_base_active_manager_testable(
                workspace_id=fxt_project.workspace_id,
                project_id=fxt_project.id_,
                dataset_storage_id=fxt_project.get_training_dataset_storage().id_,
            )
            media_identifier_1 = fxt_media_identifier_factory(1)
            media_identifier_2 = fxt_media_identifier_factory(2)
            media_identifier_3 = VideoIdentifier(fxt_ote_id(3))
            with (
                patch.object(ActiveScoreRepo, "save_many", return_value=None) as mock_save_many,
                patch.object(VideoRepo, "get_by_id", return_value=fxt_video_entity),
            ):
                active_manager.init_scores(
                    media_identifiers=[
                        media_identifier_1,
                        media_identifier_2,
                        media_identifier_3,
                    ]
                )

            mock_save_many.assert_called_once()

    def test_mark_as_suggested(
        self,
        fxt_base_active_manager_testable,
        fxt_project,
        fxt_media_identifier,
        fxt_ote_id,
    ) -> None:
        active_manager = fxt_base_active_manager_testable(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            dataset_storage_id=fxt_project.get_training_dataset_storage().id_,
        )
        suggested_item = ActiveScoreSuggestionInfo(
            media_identifier=fxt_media_identifier,
            score=0.4,
            models_ids=(fxt_ote_id(1), fxt_ote_id(2)),
        )
        with patch.object(ActiveSuggestionRepo, "save_many", return_value=None) as mock_save_many:
            active_manager.mark_as_suggested(
                suggested_media_info=[suggested_item],
                user_id="dummy_user",
                reason="some reason",
            )

        mock_save_many.assert_called_once()

    def test_reset_suggestions(self, fxt_base_active_manager_testable, fxt_project) -> None:
        active_manager = fxt_base_active_manager_testable(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            dataset_storage_id=fxt_project.get_training_dataset_storage().id_,
        )
        with patch.object(ActiveSuggestionRepo, "delete_all") as mock_delete:
            active_manager.reset_suggestions()

        mock_delete.assert_called_once()

    @pytest.mark.parametrize("all_media", [True, False], ids=["all media", "some media"])
    def test_remove_media(
        self,
        all_media,
        fxt_base_active_manager_testable,
        fxt_project,
        fxt_media_identifier_factory,
    ) -> None:
        media_identifiers = [fxt_media_identifier_factory(i) for i in range(2)]
        active_manager = fxt_base_active_manager_testable(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
            dataset_storage_id=fxt_project.get_training_dataset_storage().id_,
        )
        with (
            patch.object(
                ActiveScoreRepo, "delete_by_media_identifier", return_value=None
            ) as mock_delete_scores_by_identifiers,
            patch.object(ActiveScoreRepo, "delete_all", return_value=None) as mock_delete_all_scores,
            patch.object(
                ActiveSuggestionRepo, "delete_by_media_identifier", return_value=None
            ) as mock_delete_suggestions_by_identifiers,
            patch.object(ActiveSuggestionRepo, "delete_all", return_value=None) as mock_delete_all_suggestions,
        ):
            if all_media:
                active_manager.remove_media()
            else:
                active_manager.remove_media(media_identifiers)

        if all_media:
            mock_delete_all_scores.assert_called_once()
            mock_delete_all_suggestions.assert_called_once()
        else:
            mock_delete_scores_by_identifiers.assert_called()
            mock_delete_suggestions_by_identifiers.assert_called()

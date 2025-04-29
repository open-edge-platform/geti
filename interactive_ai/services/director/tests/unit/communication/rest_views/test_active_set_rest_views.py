# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest
from testfixtures import compare

from communication.views.active_set_views import ActiveSetRESTViews

if TYPE_CHECKING:
    from geti_types import MediaIdentifierEntity


@pytest.fixture
def fxt_dummy_image_rest():
    yield {"MOCK_IMAGE_REST_KEY": "MOCK_IMAGE_REST_VALUE"}


@pytest.fixture
def fxt_dummy_video_rest():
    yield {"MOCK_VIDEO_REST_KEY": "MOCK_VIDEO_REST_VALUE"}


@pytest.fixture
def fxt_active_set(fxt_image_identifier, fxt_video_frame_identifier):
    yield fxt_image_identifier, fxt_video_frame_identifier


@pytest.fixture
def fxt_active_set_rest(fxt_dummy_image_rest, fxt_dummy_video_rest, fxt_video_frame_identifier, fxt_project):
    dataset_storage_id = fxt_project.get_training_dataset_storage().id_
    yield [
        dict(fxt_dummy_image_rest, dataset_id=str(dataset_storage_id)),
        dict(
            fxt_dummy_video_rest,
            active_frames=[fxt_video_frame_identifier.frame_index],
            dataset_id=str(dataset_storage_id),
        ),
    ]


class TestActiveSetRESTViews:
    def test_active_set_to_rest(
        self,
        mock_project_repo,
        mock_image_repo,
        mock_video_repo,
        fxt_active_set,
        fxt_active_set_rest,
        fxt_project,
        fxt_image_entity,
        fxt_video_entity,
        fxt_dummy_image_rest,
        fxt_dummy_video_rest,
    ) -> None:
        image_identifier, video_identifier = fxt_active_set
        # Arrange
        mock_media_entities_data = {
            image_identifier: fxt_image_entity,
            video_identifier: fxt_video_entity,
        }
        mock_media_per_task_states: dict[MediaIdentifierEntity, Any] = {}

        # Act
        with patch.object(
            ActiveSetRESTViews,
            "media_to_rest",
            side_effect=[fxt_dummy_image_rest, fxt_dummy_video_rest],
        ):
            active_set_rest = ActiveSetRESTViews.active_set_to_rest(
                dataset_storage_identifier=fxt_project.get_training_dataset_storage().identifier,
                media_entities_data=mock_media_entities_data,
                annotation_scene_states=mock_media_per_task_states,
            )

        # Assert
        compare(active_set_rest, fxt_active_set_rest)

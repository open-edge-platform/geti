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

import pytest

from sc_sdk.entities.annotation_scene_state import AnnotationSceneState, AnnotationState
from sc_sdk.repos import AnnotationSceneStateRepo

from geti_types import ImageIdentifier, VideoFrameIdentifier

MEDIA_ID_OFFSET = 1
ANN_SCENE_ID_OFFSET = 2
TASK1_ID_OFFSET = 3
TASK2_ID_OFFSET = 4
LABEL1_ID_OFFSET = 5
LABEL2_ID_OFFSET = 6
ANN1_ID_OFFSET = 7
ANN2_ID_OFFSET = 8
ANN_SCENE_STATE_ID_OFFSET = 9


@pytest.fixture
def fxt_task_to_labels_dict(fxt_mongo_id):
    yield {
        fxt_mongo_id(TASK1_ID_OFFSET): [fxt_mongo_id(LABEL1_ID_OFFSET)],
        fxt_mongo_id(TASK2_ID_OFFSET): [fxt_mongo_id(LABEL2_ID_OFFSET)],
    }


@pytest.fixture
def fxt_annotation_scene_state_certain(fxt_mongo_id):
    yield AnnotationSceneState(
        media_identifier=fxt_mongo_id(MEDIA_ID_OFFSET),
        annotation_scene_id=fxt_mongo_id(ANN_SCENE_ID_OFFSET),
        annotation_state_per_task={
            fxt_mongo_id(TASK1_ID_OFFSET): AnnotationState.ANNOTATED,
            fxt_mongo_id(TASK2_ID_OFFSET): AnnotationState.ANNOTATED,
        },
        unannotated_rois={},
        labels_to_revisit_per_annotation={},
        labels_to_revisit_full_scene=[],
        id_=fxt_mongo_id(ANN_SCENE_STATE_ID_OFFSET),
    )


@pytest.fixture
def fxt_annotation_scene_state_to_revisit_ann1_label1(fxt_mongo_id):
    yield AnnotationSceneState(
        media_identifier=fxt_mongo_id(MEDIA_ID_OFFSET),
        annotation_scene_id=fxt_mongo_id(ANN_SCENE_ID_OFFSET),
        annotation_state_per_task={
            fxt_mongo_id(TASK1_ID_OFFSET): AnnotationState.ANNOTATED,
            fxt_mongo_id(TASK2_ID_OFFSET): AnnotationState.ANNOTATED,
        },
        unannotated_rois={},
        labels_to_revisit_per_annotation={fxt_mongo_id(ANN1_ID_OFFSET): [fxt_mongo_id(LABEL1_ID_OFFSET)]},
        labels_to_revisit_full_scene=[],
        id_=fxt_mongo_id(ANN_SCENE_STATE_ID_OFFSET),
    )


@pytest.fixture
def fxt_annotation_scene_state_to_revisit_fullscene_label1(fxt_mongo_id):
    yield AnnotationSceneState(
        media_identifier=fxt_mongo_id(MEDIA_ID_OFFSET),
        annotation_scene_id=fxt_mongo_id(ANN_SCENE_ID_OFFSET),
        annotation_state_per_task={
            fxt_mongo_id(TASK1_ID_OFFSET): AnnotationState.ANNOTATED,
            fxt_mongo_id(TASK2_ID_OFFSET): AnnotationState.ANNOTATED,
        },
        unannotated_rois={},
        labels_to_revisit_per_annotation={},
        labels_to_revisit_full_scene=[fxt_mongo_id(LABEL1_ID_OFFSET)],
        id_=fxt_mongo_id(ANN_SCENE_STATE_ID_OFFSET),
    )


@pytest.fixture()
def fxt_video_annotation_scene_state_list_persisted(fxt_dataset_storage_identifier, fxt_ote_id):
    # list of persisted annotations scene states with video media identifiers
    task_id = fxt_ote_id(0)
    video_frame_identifier1 = VideoFrameIdentifier(video_id=fxt_ote_id(2), frame_index=1)
    video_frame_identifier2 = VideoFrameIdentifier(video_id=fxt_ote_id(2), frame_index=2)
    ann_scene_state1 = AnnotationSceneState(
        media_identifier=video_frame_identifier1,
        annotation_scene_id=fxt_ote_id(3),
        annotation_state_per_task={task_id: AnnotationState.ANNOTATED},
        unannotated_rois={},
        labels_to_revisit_per_annotation={fxt_ote_id(4): []},
        labels_to_revisit_full_scene=[],
        id_=AnnotationSceneStateRepo.generate_id(),
    )
    ann_scene_state2 = AnnotationSceneState(
        media_identifier=video_frame_identifier2,
        annotation_scene_id=fxt_ote_id(5),
        annotation_state_per_task={task_id: AnnotationState.PARTIALLY_ANNOTATED},
        unannotated_rois={},
        labels_to_revisit_per_annotation={fxt_ote_id(6): []},
        labels_to_revisit_full_scene=[],
        id_=AnnotationSceneStateRepo.generate_id(),
    )
    AnnotationSceneStateRepo(fxt_dataset_storage_identifier).save(ann_scene_state1)
    AnnotationSceneStateRepo(fxt_dataset_storage_identifier).save(ann_scene_state2)
    yield [ann_scene_state1, ann_scene_state2]


@pytest.mark.ScSdkComponent
class TestAnnotationSceneState:
    # fmt: off
    @pytest.mark.parametrize(
        "lazyfxt_annotation_scene_state, ann_id_offset, task_id_offset, expected_to_revisit",
        [
            ("fxt_annotation_scene_state_certain", ANN1_ID_OFFSET, TASK1_ID_OFFSET, False),
            ("fxt_annotation_scene_state_certain", ANN1_ID_OFFSET, TASK2_ID_OFFSET, False),
            ("fxt_annotation_scene_state_certain", ANN2_ID_OFFSET, TASK1_ID_OFFSET, False),
            ("fxt_annotation_scene_state_to_revisit_ann1_label1", ANN1_ID_OFFSET, TASK1_ID_OFFSET, True),
            ("fxt_annotation_scene_state_to_revisit_ann1_label1", ANN2_ID_OFFSET, TASK1_ID_OFFSET, False),
            ("fxt_annotation_scene_state_to_revisit_ann1_label1", ANN1_ID_OFFSET, TASK2_ID_OFFSET, False),
        ],
        ids=[
            "non-to_revisit, first annotation, first task",
            "non-to_revisit, first annotation, second task",
            "non-to_revisit, second annotation, first task",
            "to_revisit-ann1-task1, first annotation, first task",
            "to_revisit-ann1-task1, second annotation, first task",
            "to_revisit-ann1-task1, first annotation, second task",
        ]
    )
    # fmt: on
    def test_is_annotation_to_revisit_for_task(
        self,
        request,
        fxt_mongo_id,
        lazyfxt_annotation_scene_state,
        fxt_task_to_labels_dict,
        ann_id_offset,
        task_id_offset,
        expected_to_revisit,
    ) -> None:
        # Arrange
        fxt_annotation_scene_state: AnnotationSceneState = request.getfixturevalue(lazyfxt_annotation_scene_state)
        annotation_id = fxt_mongo_id(ann_id_offset)
        task_id = fxt_mongo_id(task_id_offset)

        # Act
        is_to_revisit = fxt_annotation_scene_state.is_annotation_to_revisit_for_task(
            annotation_id=annotation_id, task_labels=fxt_task_to_labels_dict[task_id]
        )

        # Assert
        assert is_to_revisit == expected_to_revisit

    # fmt: off
    @pytest.mark.parametrize(
        "lazyfxt_annotation_scene_state, ann_id_offset, expected_to_revisit",
        [
            ("fxt_annotation_scene_state_certain", ANN1_ID_OFFSET, False),
            ("fxt_annotation_scene_state_certain", ANN2_ID_OFFSET, False),
            ("fxt_annotation_scene_state_to_revisit_ann1_label1", ANN1_ID_OFFSET, True),
            ("fxt_annotation_scene_state_to_revisit_ann1_label1", ANN2_ID_OFFSET, False),
        ],
        ids=[
            "non-to_revisit, first annotation",
            "non-to_revisit, second annotation",
            "to_revisit-ann1-task1, first annotation",
            "to_revisit-ann1-task1, second annotation",
        ]
    )
    # fmt: on
    def test_is_annotation_to_revisit(
        self,
        request,
        fxt_mongo_id,
        lazyfxt_annotation_scene_state,
        ann_id_offset,
        expected_to_revisit,
    ) -> None:
        # Arrange
        fxt_annotation_scene_state: AnnotationSceneState = request.getfixturevalue(lazyfxt_annotation_scene_state)
        annotation_id = fxt_mongo_id(ann_id_offset)

        # Act
        is_to_revisit = fxt_annotation_scene_state.is_annotation_to_revisit(annotation_id=annotation_id)

        # Assert
        assert is_to_revisit == expected_to_revisit

    # fmt: off
    @pytest.mark.parametrize(
        "lazyfxt_annotation_scene_state, task_id_offset, expected_to_revisit",
        [
            ("fxt_annotation_scene_state_certain", TASK1_ID_OFFSET, False),
            ("fxt_annotation_scene_state_certain", TASK2_ID_OFFSET, False),
            ("fxt_annotation_scene_state_to_revisit_fullscene_label1", TASK1_ID_OFFSET, True),
            ("fxt_annotation_scene_state_to_revisit_fullscene_label1", TASK2_ID_OFFSET, False),
        ],
        ids=[
            "non-to_revisit, first task",
            "non-to_revisit, second task",
            "to_revisit-fullscene-task1, first task",
            "to_revisit-fullscene-task1, second task",
        ]
    )
    # fmt: on
    def test_is_media_to_revisit_at_scene_level_for_task(
        self,
        request,
        fxt_mongo_id,
        lazyfxt_annotation_scene_state,
        fxt_task_to_labels_dict,
        task_id_offset,
        expected_to_revisit,
    ) -> None:
        # Arrange
        fxt_annotation_scene_state: AnnotationSceneState = request.getfixturevalue(lazyfxt_annotation_scene_state)
        task_id = fxt_mongo_id(task_id_offset)

        # Act
        is_to_revisit = fxt_annotation_scene_state.is_media_to_revisit_at_scene_level_for_task(
            task_labels=fxt_task_to_labels_dict[task_id]
        )

        # Assert
        assert is_to_revisit == expected_to_revisit

    # fmt: off
    @pytest.mark.parametrize(
        "lazyfxt_annotation_scene_state, expected_to_revisit",
        [
            ("fxt_annotation_scene_state_certain", False),
            ("fxt_annotation_scene_state_to_revisit_fullscene_label1", True),
        ],
        ids=[
            "non-to_revisit",
            "to_revisit-fullscene-task1",
        ]
    )
    # fmt: on
    def test_is_media_to_revisit_at_scene_level(
        self,
        request,
        fxt_mongo_id,
        lazyfxt_annotation_scene_state,
        expected_to_revisit,
    ) -> None:
        # Arrange
        fxt_annotation_scene_state: AnnotationSceneState = request.getfixturevalue(lazyfxt_annotation_scene_state)

        # Act
        is_to_revisit = fxt_annotation_scene_state.is_media_to_revisit_at_scene_level()

        # Assert
        assert is_to_revisit == expected_to_revisit

    # fmt: off
    @pytest.mark.parametrize(
        "lazyfxt_annotation_scene_state, task_id_offset, expected_to_revisit",
        [
            ("fxt_annotation_scene_state_certain", TASK1_ID_OFFSET, False),
            ("fxt_annotation_scene_state_certain", TASK2_ID_OFFSET, False),
            ("fxt_annotation_scene_state_to_revisit_ann1_label1", TASK1_ID_OFFSET, True),
            ("fxt_annotation_scene_state_to_revisit_ann1_label1", TASK2_ID_OFFSET, False),
            ("fxt_annotation_scene_state_to_revisit_fullscene_label1", TASK1_ID_OFFSET, True),
            ("fxt_annotation_scene_state_to_revisit_fullscene_label1", TASK2_ID_OFFSET, False),
        ],
        ids=[
            "non-to_revisit, first task",
            "non-to_revisit, second task",
            "to_revisit-ann1-task1, first task",
            "to_revisit-ann1-task1, second task",
            "to_revisit-fullscene-task1, first task",
            "to_revisit-fullscene-task1, second task",
        ]
    )
    # fmt: on
    def test_is_media_to_revisit_for_task(
        self,
        request,
        fxt_mongo_id,
        lazyfxt_annotation_scene_state,
        fxt_task_to_labels_dict,
        task_id_offset,
        expected_to_revisit,
    ) -> None:
        # Arrange
        fxt_annotation_scene_state: AnnotationSceneState = request.getfixturevalue(lazyfxt_annotation_scene_state)
        task_id = fxt_mongo_id(task_id_offset)

        # Act
        is_to_revisit = fxt_annotation_scene_state.is_media_to_revisit_for_task(
            task_labels=fxt_task_to_labels_dict[task_id]
        )

        # Assert
        assert is_to_revisit == expected_to_revisit

    # fmt: off
    @pytest.mark.parametrize(
        "lazyfxt_annotation_scene_state, expected_to_revisit",
        [
            ("fxt_annotation_scene_state_certain", False),
            ("fxt_annotation_scene_state_to_revisit_ann1_label1", True),
            ("fxt_annotation_scene_state_to_revisit_fullscene_label1", True),
        ],
        ids=[
            "non-to_revisit",
            "to_revisit-ann1-task1",
            "to_revisit-fullscene-task1",
        ]
    )
    # fmt: on
    def test_is_media_to_revisit(
        self,
        request,
        fxt_mongo_id,
        lazyfxt_annotation_scene_state,
        expected_to_revisit,
    ) -> None:
        # Arrange
        fxt_annotation_scene_state: AnnotationSceneState = request.getfixturevalue(lazyfxt_annotation_scene_state)

        # Act
        is_to_revisit = fxt_annotation_scene_state.is_media_to_revisit()

        # Assert
        assert is_to_revisit == expected_to_revisit

    def test_get_state_media_level(self, fxt_mongo_id, fxt_image_identifier):
        ann_scene_state = AnnotationSceneState(
            media_identifier=fxt_image_identifier,
            annotation_scene_id=fxt_mongo_id(1),
            annotation_state_per_task={},
            unannotated_rois={},
            labels_to_revisit_per_annotation={fxt_mongo_id(2): []},
            labels_to_revisit_full_scene=[],
            id_=AnnotationSceneStateRepo.generate_id(),
        )
        assert ann_scene_state.get_state_media_level() == AnnotationState.NONE

    def test_count_images_state_for_task(
        self,
        fxt_ote_id,
        fxt_dataset_storage_identifier,
    ) -> None:
        # Arrange
        repo = AnnotationSceneStateRepo(fxt_dataset_storage_identifier)
        task_id1 = fxt_ote_id(0)
        task_id2 = fxt_ote_id(1)
        image_identifier1 = ImageIdentifier(fxt_ote_id(2))
        image_identifier2 = ImageIdentifier(fxt_ote_id(3))
        ann_scene_state1 = AnnotationSceneState(
            media_identifier=image_identifier1,
            annotation_scene_id=fxt_ote_id(4),
            annotation_state_per_task={task_id1: AnnotationState.ANNOTATED},
            unannotated_rois={},
            labels_to_revisit_per_annotation={fxt_ote_id(5): []},
            labels_to_revisit_full_scene=[],
            id_=AnnotationSceneStateRepo.generate_id(),
        )
        ann_scene_state2 = AnnotationSceneState(
            media_identifier=image_identifier2,
            annotation_scene_id=fxt_ote_id(6),
            annotation_state_per_task={task_id2: AnnotationState.PARTIALLY_ANNOTATED},
            unannotated_rois={},
            labels_to_revisit_per_annotation={fxt_ote_id(7): []},
            labels_to_revisit_full_scene=[],
            id_=AnnotationSceneStateRepo.generate_id(),
        )
        repo.save(ann_scene_state1)
        repo.save(ann_scene_state2)

        # Act
        result_count_images_task1 = repo.count_images_state_for_task([AnnotationState.ANNOTATED], task_id1)
        result_count_images_task1_empty = repo.count_images_state_for_task(
            [AnnotationState.PARTIALLY_ANNOTATED], task_id1
        )
        result_count_images_task2 = repo.count_images_state_for_task(
            [AnnotationState.ANNOTATED, AnnotationState.PARTIALLY_ANNOTATED], task_id2
        )

        # Assert
        assert result_count_images_task1 == 1
        assert result_count_images_task1_empty == 0
        assert result_count_images_task2 == 1

    def test_count_video_frames_state_for_task(
        self,
        fxt_ote_id,
        fxt_dataset_storage_identifier,
        fxt_video_annotation_scene_state_list_persisted,
    ):
        # Arrange
        repo = AnnotationSceneStateRepo(fxt_dataset_storage_identifier)
        task_id1 = fxt_ote_id(0)
        task_id2 = fxt_ote_id(1)

        # Act
        result_count_frames_empty = repo.count_video_frames_state_for_task([AnnotationState.ANNOTATED], task_id2)
        result_count_frames_single_state = repo.count_video_frames_state_for_task([AnnotationState.ANNOTATED], task_id1)
        result_count_frames_multiple_states = repo.count_video_frames_state_for_task(
            [AnnotationState.ANNOTATED, AnnotationState.PARTIALLY_ANNOTATED], task_id1
        )

        # Assert
        assert result_count_frames_empty == 0
        assert result_count_frames_single_state == 1
        assert result_count_frames_multiple_states == 2

    def test_count_videos_state_for_task(
        self,
        fxt_ote_id,
        fxt_dataset_storage_identifier,
        fxt_video_annotation_scene_state_list_persisted,
    ):
        # Arrange
        repo = AnnotationSceneStateRepo(fxt_dataset_storage_identifier)
        task_id1 = fxt_ote_id(0)
        task_id2 = fxt_ote_id(1)

        # Act
        result_count_videos = repo.count_videos_state_for_task(
            [AnnotationState.ANNOTATED, AnnotationState.PARTIALLY_ANNOTATED], task_id1
        )
        result_count_videos_empty = repo.count_videos_state_for_task(
            [AnnotationState.ANNOTATED, AnnotationState.PARTIALLY_ANNOTATED], task_id2
        )

        # Assert
        assert result_count_videos == 1
        assert result_count_videos_empty == 0

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import numpy as np
import pytest

from entities.reference_feature import NullReferenceFeature, ReferenceFeature, ReferenceMediaInfo
from repos.reference_feature_repo import ReferenceFeatureRepo

from geti_types import ImageIdentifier, VideoFrameIdentifier


@pytest.fixture
def fxt_task_id_1(fxt_ote_id):
    return fxt_ote_id(1001)


@pytest.fixture
def fxt_task_id_2(fxt_ote_id):
    return fxt_ote_id(1002)


@pytest.fixture
def fxt_reference_feature_1(fxt_ote_id, fxt_task_id_1):
    yield ReferenceFeature(
        task_id=fxt_task_id_1,
        label_id=fxt_ote_id(100),
        media_info=ReferenceMediaInfo(
            dataset_storage_id=fxt_ote_id(200),
            annotation_scene_id=fxt_ote_id(300),
            media_identifier=ImageIdentifier(image_id=fxt_ote_id(400)),
        ),
        reference_feature_adapter=None,
        numpy=np.ones((1, 4)),
    )


@pytest.fixture
def fxt_reference_feature_2(fxt_ote_id, fxt_task_id_1):
    yield ReferenceFeature(
        task_id=fxt_task_id_1,
        label_id=fxt_ote_id(101),
        media_info=ReferenceMediaInfo(
            annotation_scene_id=fxt_ote_id(301),
            dataset_storage_id=fxt_ote_id(201),
            media_identifier=VideoFrameIdentifier(video_id=fxt_ote_id(401), frame_index=10),
        ),
        reference_feature_adapter=None,
        numpy=np.zeros((1, 4)),
    )


@pytest.fixture
def fxt_reference_feature_3(fxt_ote_id, fxt_task_id_2):
    yield ReferenceFeature(
        task_id=fxt_task_id_2,
        label_id=fxt_ote_id(102),
        media_info=ReferenceMediaInfo(
            annotation_scene_id=fxt_ote_id(302),
            dataset_storage_id=fxt_ote_id(202),
            media_identifier=VideoFrameIdentifier(video_id=fxt_ote_id(401), frame_index=11),
        ),
        reference_feature_adapter=None,
        numpy=np.zeros((1, 4)),
    )


@pytest.mark.VisualPromptServiceComponent
class TestReferenceFeatureRepo:
    def test_save(self, request, fxt_session_ctx, fxt_project_identifier, fxt_reference_feature_1) -> None:
        # Arrange
        repo = ReferenceFeatureRepo(fxt_project_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        # check that reference feature does not exist in the DB
        assert isinstance(repo.get_by_id(fxt_reference_feature_1.id_), NullReferenceFeature)

        # Act
        repo.save(fxt_reference_feature_1)

        # Assert
        loaded_ref_feature = repo.get_by_id(fxt_reference_feature_1.id_)
        assert loaded_ref_feature == fxt_reference_feature_1
        assert np.array_equal(loaded_ref_feature.numpy, fxt_reference_feature_1.numpy)
        assert loaded_ref_feature.media_info == fxt_reference_feature_1.media_info

    def test_save_many(
        self, request, fxt_session_ctx, fxt_project_identifier, fxt_reference_feature_1, fxt_reference_feature_2
    ) -> None:
        # Arrange
        repo = ReferenceFeatureRepo(fxt_project_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        # check that reference features do not exist in the DB
        assert isinstance(repo.get_by_id(fxt_reference_feature_1.id_), NullReferenceFeature)
        assert isinstance(repo.get_by_id(fxt_reference_feature_2.id_), NullReferenceFeature)

        # Act
        repo.save_many([fxt_reference_feature_1, fxt_reference_feature_2])

        # Assert
        loaded_ref_feature_1 = repo.get_by_id(fxt_reference_feature_1.id_)
        loaded_ref_feature_2 = repo.get_by_id(fxt_reference_feature_2.id_)
        assert loaded_ref_feature_1 == fxt_reference_feature_1
        assert loaded_ref_feature_2 == fxt_reference_feature_2
        assert np.array_equal(loaded_ref_feature_1.numpy, fxt_reference_feature_1.numpy)
        assert np.array_equal(loaded_ref_feature_2.numpy, fxt_reference_feature_2.numpy)
        assert loaded_ref_feature_1.media_info == fxt_reference_feature_1.media_info
        assert loaded_ref_feature_2.media_info == fxt_reference_feature_2.media_info

    def test_delete_by_label_id(
        self, request, fxt_session_ctx, fxt_project_identifier, fxt_reference_feature_1, fxt_reference_feature_2
    ) -> None:
        # Arrange
        repo = ReferenceFeatureRepo(fxt_project_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        repo.save_many([fxt_reference_feature_1, fxt_reference_feature_2])
        assert repo.count() == 2

        # Act
        deleted = repo.delete_by_label_id(fxt_reference_feature_1.id_)

        # Assert
        assert deleted
        assert repo.count() == 1

    def test_delete_all(
        self,
        fxt_session_ctx,
        fxt_project_identifier,
        fxt_reference_feature_1,
        fxt_reference_feature_2,
        fxt_reference_feature_3,
    ) -> None:
        # Arrange
        repo = ReferenceFeatureRepo(fxt_project_identifier)
        repo.save_many([fxt_reference_feature_1, fxt_reference_feature_2, fxt_reference_feature_3])
        assert repo.count() == 3

        # Act
        any_deleted = repo.delete_all()

        # Assert
        assert any_deleted
        assert repo.count() == 0

    def test_get_all_by_task_id(
        self,
        request,
        fxt_session_ctx,
        fxt_project_identifier,
        fxt_task_id_1,
        fxt_task_id_2,
        fxt_reference_feature_1,
        fxt_reference_feature_2,
        fxt_reference_feature_3,
    ) -> None:
        # Arrange
        repo = ReferenceFeatureRepo(fxt_project_identifier)
        repo.save_many([fxt_reference_feature_1, fxt_reference_feature_2, fxt_reference_feature_3])
        request.addfinalizer(lambda: repo.delete_all())

        # Act
        ref_features_task_1 = list(repo.get_all_by_task_id(fxt_task_id_1))
        ref_features_task_2 = list(repo.get_all_by_task_id(fxt_task_id_2))
        ref_features_ids_task_1 = list(repo.get_all_ids_by_task_id(fxt_task_id_1))
        ref_features_ids_task_2 = list(repo.get_all_ids_by_task_id(fxt_task_id_2))

        # Assert
        assert ref_features_task_1 == [fxt_reference_feature_1, fxt_reference_feature_2]
        assert ref_features_task_2 == [fxt_reference_feature_3]
        assert ref_features_ids_task_1 == [fxt_reference_feature_1.id_, fxt_reference_feature_2.id_]
        assert ref_features_ids_task_2 == [fxt_reference_feature_3.id_]

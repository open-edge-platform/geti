#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

import pytest

from sc_sdk.entities.annotation_scene_state import AnnotationState
from sc_sdk.entities.dataset_storage_filter_data import DatasetStorageFilterData, NullDatasetStorageFilterData
from sc_sdk.entities.media import MediaPreprocessingStatus
from sc_sdk.entities.video import VideoFrameIdentifier, VideoIdentifier
from sc_sdk.entities.video_annotation_statistics import VideoAnnotationStatistics
from sc_sdk.repos import VideoRepo
from sc_sdk.repos.base.session_repo import QueryAccessMode
from sc_sdk.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo
from sc_sdk.repos.mappers import IDToMongo

from geti_types import ID, ImageIdentifier, MediaIdentifierEntity


@pytest.mark.ScSdkComponent
class TestDatasetStorageFilterRepo:
    def test_save_dataset_storage_filter_data(
        self, request, fxt_dataset_storage_persisted, fxt_dataset_storage_filter_data
    ) -> None:
        """
        <b>Description:</b>
        Check that a  DatasetStorageFilterData is correctly saved in the DatasetStorageFilterRepo

        <b>Input data:</b>
        A DatasetStorageFilterData

        <b>Expected results:</b>
        Test passes if the data that's saved to the repo
        and later retrieved is the same as the data that was created

        <b>Steps</b>
        1. Create test data
        2. Save test data to the repo
        3. Compare created data to data retrieved from the repo
        """
        repo = DatasetStorageFilterRepo(fxt_dataset_storage_persisted.identifier)
        request.addfinalizer(lambda: repo.delete_all())
        repo.upsert_dataset_storage_filter_data(fxt_dataset_storage_filter_data)

        data_id = fxt_dataset_storage_filter_data.media_identifier.as_id()
        retrieved_data = repo.get_by_id(id_=data_id)

        repo.delete_by_id(id_=fxt_dataset_storage_filter_data.id_)
        empty_data = repo.get_by_id(id_=data_id)

        assert retrieved_data == fxt_dataset_storage_filter_data
        assert isinstance(empty_data, NullDatasetStorageFilterData)

    def test_update_media_and_annotation_scene_filter_data(
        self, request, fxt_dataset_storage_persisted, fxt_dataset_storage_filter_data
    ) -> None:
        """
        <b>Description:</b>
        Check that creating and updating a DatasetStorageFilterData step by step using
        MediaFilterData and AnnotationSceneFilterData is correct and consistent and
        stable under race conditions.

        <b>Input data:</b>
        A DatasetStorageFilterData

        <b>Expected results:</b>
        Test passes if the data that's saved to the repo
        and later retrieved is the same as the data that was created

        <b>Steps</b>
        1. Create test data
        2. Save first media then annotation scene filter data
        3. Ensure retrieved data is correct
        4. Delete entry
        5. Save first annotation scene then media filter data
        6. Ensure retrieved data is correct
        """
        media_filter_data = DatasetStorageFilterData(
            media_identifier=fxt_dataset_storage_filter_data.media_identifier,
            media_filter_data=fxt_dataset_storage_filter_data.media_filter_data,
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )
        annotation_scene_filter_data = DatasetStorageFilterData(
            media_identifier=fxt_dataset_storage_filter_data.media_identifier,
            annotation_scene_filter_data=fxt_dataset_storage_filter_data.annotation_scene_filter_data,
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )
        repo = DatasetStorageFilterRepo(fxt_dataset_storage_persisted.identifier)
        repo.delete_all()
        request.addfinalizer(lambda: repo.delete_all())

        repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data=media_filter_data)
        retrieved_data_1 = repo.get_by_id(id_=fxt_dataset_storage_filter_data.id_)

        repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data=annotation_scene_filter_data)
        retrieved_data_2 = repo.get_by_id(id_=fxt_dataset_storage_filter_data.id_)

        repo.delete_by_id(id_=fxt_dataset_storage_filter_data.id_)
        empty_data = repo.get_by_id(id_=fxt_dataset_storage_filter_data.id_)

        assert retrieved_data_1.media_filter_data == fxt_dataset_storage_filter_data.media_filter_data
        assert retrieved_data_1.annotation_scene_filter_data is None
        assert retrieved_data_2.media_filter_data == fxt_dataset_storage_filter_data.media_filter_data
        assert (
            retrieved_data_2.annotation_scene_filter_data
            == fxt_dataset_storage_filter_data.annotation_scene_filter_data
        )
        assert isinstance(empty_data, NullDatasetStorageFilterData)

        repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data=annotation_scene_filter_data)
        retrieved_data_3 = repo.get_by_id(id_=fxt_dataset_storage_filter_data.id_)

        repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data=media_filter_data)
        retrieved_data_4 = repo.get_by_id(id_=fxt_dataset_storage_filter_data.id_)

        repo.delete_by_id(id_=fxt_dataset_storage_filter_data.id_)
        empty_data = repo.get_by_id(id_=fxt_dataset_storage_filter_data.id_)

        assert retrieved_data_3.media_filter_data is None
        assert (
            retrieved_data_3.annotation_scene_filter_data
            == fxt_dataset_storage_filter_data.annotation_scene_filter_data
        )
        assert retrieved_data_4.media_filter_data == fxt_dataset_storage_filter_data.media_filter_data
        assert (
            retrieved_data_4.annotation_scene_filter_data
            == fxt_dataset_storage_filter_data.annotation_scene_filter_data
        )
        assert isinstance(empty_data, NullDatasetStorageFilterData)

    def test_unannotated_frames(
        self,
        request,
        fxt_dataset_storage_persisted,
        fxt_video_entity,
        fxt_annotation_scene,
    ) -> None:
        """
        <b>Description:</b>
        Check that unannotated_frames are correctly calculated, even if video and its
        video frames are saved in a different order.

        <b>Input data:</b>
        A Video and VideoFrame annotation scene

        <b>Expected results:</b>
        Test passes if the unannotated frames are correct regardless of the order in
        which we save the data and/or saving the video entity twice.

        <b>Steps</b>
        1. Create test data
        2. Save first video then video frame filter data
        3. Ensure unannotated frames is correct
        4. Delete entry
        5. Save first video frame then video filter data
        6. Save video filter data again
        6. Ensure unannotated frames is correct
        """
        video_id = fxt_video_entity.media_identifier.media_id
        total_frames = fxt_video_entity.total_frames
        filter_video_id = fxt_video_entity.media_identifier.as_id()
        video_frame_identifier_1 = VideoFrameIdentifier(video_id=video_id, frame_index=3)
        video_frame_identifier_2 = VideoFrameIdentifier(video_id=video_id, frame_index=15)

        media_filter_data = DatasetStorageFilterData.create_dataset_storage_filter_data(
            media_identifier=fxt_video_entity.media_identifier,
            media=fxt_video_entity,
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )
        annotation_scene_filter_data = DatasetStorageFilterData.create_dataset_storage_filter_data(
            media_identifier=video_frame_identifier_1,
            annotation_scene=fxt_annotation_scene,
            media_annotation_state=AnnotationState.ANNOTATED,
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )
        dataset_storage_filter_data = DatasetStorageFilterData.create_dataset_storage_filter_data(
            media_identifier=video_frame_identifier_2,
            media=fxt_video_entity,
            annotation_scene=fxt_annotation_scene,
            media_annotation_state=AnnotationState.ANNOTATED,
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )
        repo = DatasetStorageFilterRepo(fxt_dataset_storage_persisted.identifier)
        repo.delete_all()
        request.addfinalizer(lambda: repo.delete_all())

        repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data=media_filter_data)
        retrieved_data_1 = repo.get_by_id(id_=filter_video_id)

        repo.upsert_dataset_storage_filter_data(
            dataset_storage_filter_data=annotation_scene_filter_data,
        )
        retrieved_data_2 = repo.get_by_id(id_=filter_video_id)

        repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data)
        retrieved_data_3 = repo.get_by_id(id_=filter_video_id)

        repo.delete_all()
        empty_data = repo.get_by_id(id_=filter_video_id)

        assert retrieved_data_1.media_filter_data.video_filter_data.unannotated_frames == total_frames  # type: ignore[union-attr]
        assert retrieved_data_2.media_filter_data.video_filter_data.unannotated_frames == total_frames - 1  # type: ignore[union-attr]
        assert retrieved_data_3.media_filter_data.video_filter_data.unannotated_frames == total_frames - 2  # type: ignore[union-attr]
        assert isinstance(empty_data, NullDatasetStorageFilterData)

        data_filter = repo.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
        data_filter["_id"] = IDToMongo.forward(filter_video_id)
        repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data)
        retrieved_data_4: dict = repo._collection.find_one(filter=data_filter)  # type: ignore[assignment]
        repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data=media_filter_data)
        retrieved_data_5 = repo.get_by_id(id_=filter_video_id)
        repo.upsert_dataset_storage_filter_data(
            dataset_storage_filter_data=annotation_scene_filter_data,
        )
        retrieved_data_6: dict = repo._collection.find_one(filter=data_filter)  # type: ignore[assignment]
        repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data=media_filter_data)
        retrieved_data_7 = repo.get_by_id(id_=filter_video_id)

        repo.delete_all()
        empty_data = repo.get_by_id(id_=filter_video_id)

        assert retrieved_data_4["unannotated_frames"] == -1  # type: ignore[union-attr]
        assert retrieved_data_5.media_filter_data.video_filter_data.unannotated_frames == total_frames - 1  # type: ignore[union-attr]
        assert retrieved_data_6["unannotated_frames"] == total_frames - 2  # type: ignore[union-attr]
        assert retrieved_data_7.media_filter_data.video_filter_data.unannotated_frames == total_frames - 2  # type: ignore[union-attr]
        assert isinstance(empty_data, NullDatasetStorageFilterData)

    def test_delete_by_media_id(
        self,
        request,
        fxt_dataset_storage_persisted,
        fxt_dataset_storage_filter_data_video,
        fxt_mongo_id,
    ) -> None:
        """
        <b>Description:</b>
        Check that data can be deleted by media id from the DatasetStorageFilterRepo

        <b>Input data:</b>
        A video and several video frame DatasetStorageFilterData entries with the same media_id
        and two images

        <b>Expected results:</b>
        Test passes if all three entries related to the same video is deleted, while the image
        data still persists.

        <b>Steps</b>
        1. Create test data
        2. Save test data to the repo
        3. Delete data by media id
        """
        repo = DatasetStorageFilterRepo(fxt_dataset_storage_persisted.identifier)
        repo.delete_all()
        request.addfinalizer(lambda: repo.delete_all())

        video_id = ID(fxt_mongo_id(11))
        image_id_1 = ID(fxt_mongo_id(12))
        image_id_2 = ID(fxt_mongo_id(13))
        media_identifiers = [
            VideoIdentifier(video_id=video_id),
            VideoFrameIdentifier(video_id=video_id, frame_index=5),
            VideoFrameIdentifier(video_id=video_id, frame_index=8),
            ImageIdentifier(image_id=image_id_1),
            ImageIdentifier(image_id=image_id_2),
        ]
        fxt_dataset_storage_filter_data_video.media_filter_data.video_filter_data.unannotated_frames = 100

        for media_identifier in media_identifiers:
            fxt_dataset_storage_filter_data_video.media_identifier = media_identifier
            repo.upsert_dataset_storage_filter_data(fxt_dataset_storage_filter_data_video)

        retrieved_data = set(repo.get_all_ids())
        expected_ids = {media_identifier.as_id() for media_identifier in media_identifiers}

        repo.delete_all_by_media_id(media_id=video_id)
        image_data = set(repo.get_all_ids())
        expected_image_ids = {
            media_identifier.as_id()
            for media_identifier in media_identifiers
            if isinstance(media_identifier, ImageIdentifier)
        }

        assert retrieved_data == expected_ids
        assert image_data == expected_image_ids

    def test_update_annotation_scenes_to_revisit(
        self,
        request,
        fxt_dataset_storage_persisted,
        fxt_dataset_storage_filter_data,
        fxt_dataset_storage_filter_data_video,
        fxt_mongo_id,
    ) -> None:
        """
        <b>Description:</b>
        Check that the media_annotation_state can be set to TO_REVISIT based on the annotation scene id.

        <b>Input data:</b>
        A video and several video frame DatasetStorageFilterData entries with the same media_id
        and two images

        <b>Expected results:</b>
        Test passes if media_annotation_state is updated for the correct entries

        <b>Steps</b>
        1. Create test data
        2. Save test data to the repo
        3. Check if media_annotation_state is ANNOTATED for all
        4. Update media_annotation_state of some entries to TO_REVISIT
        5. Check that the correct entries are updated
        """
        repo = DatasetStorageFilterRepo(fxt_dataset_storage_persisted.identifier)
        repo.delete_all()
        request.addfinalizer(lambda: repo.delete_all())

        video_id = ID(fxt_mongo_id(11))
        image_id_1 = ID(fxt_mongo_id(12))
        image_id_2 = ID(fxt_mongo_id(13))
        media_identifiers = [
            VideoIdentifier(video_id=video_id),
            VideoFrameIdentifier(video_id=video_id, frame_index=5),
            VideoFrameIdentifier(video_id=video_id, frame_index=8),
            ImageIdentifier(image_id=image_id_1),
            ImageIdentifier(image_id=image_id_2),
        ]
        annotation_scene_ids = [ID(fxt_mongo_id(i)) for i in range(len(media_identifiers))]
        fxt_dataset_storage_filter_data_video.media_filter_data.video_filter_data.unannotated_frames = 100

        for media_identifier, annotation_scene_id in zip(media_identifiers, annotation_scene_ids):
            if isinstance(media_identifier, ImageIdentifier):
                fxt_dataset_storage_filter_data.media_identifier = media_identifier
                fxt_dataset_storage_filter_data.annotation_scene_filter_data.annotation_scene_id = annotation_scene_id
                repo.upsert_dataset_storage_filter_data(fxt_dataset_storage_filter_data)
            else:
                fxt_dataset_storage_filter_data_video.media_identifier = media_identifier
                fxt_dataset_storage_filter_data_video.annotation_scene_filter_data.annotation_scene_id = (
                    annotation_scene_id
                )
                repo.upsert_dataset_storage_filter_data(fxt_dataset_storage_filter_data_video)

        retrieved_media_annotation_states = [data.media_annotation_state for data in repo.get_all()]
        expected_media_annotation_states = [AnnotationState.ANNOTATED for _ in media_identifiers]

        suspended_annotation_scene_ids = [ID(fxt_mongo_id(i)) for i in range(2, 4)]
        repo.update_annotation_scenes_to_revisit(annotation_scene_ids=suspended_annotation_scene_ids)
        all_retrieved_data = list(repo.get_all())
        to_revisit_media_identifiers = {
            data.media_identifier
            for data in all_retrieved_data
            if data.media_annotation_state is AnnotationState.TO_REVISIT
        }
        annotated_media_identifiers = {
            data.media_identifier
            for data in all_retrieved_data
            if data.media_annotation_state is AnnotationState.ANNOTATED
        }
        expected_to_revisit_media_identifiers = set(media_identifiers[2:4])
        expected_annotated_media_identifiers = set(media_identifiers[:2] + media_identifiers[4:])
        assert retrieved_media_annotation_states == expected_media_annotation_states
        assert to_revisit_media_identifiers == expected_to_revisit_media_identifiers
        assert annotated_media_identifiers == expected_annotated_media_identifiers

    def test_get_media_identifiers_by_annotation_state(
        self,
        request,
        fxt_video_entity,
        fxt_dataset_storage_persisted,
        fxt_dataset_storage_filter_data_video,
        fxt_mongo_id,
    ) -> None:
        """
        <b>Description:</b>
        Check that media identifiers can be obtained by media_annotation_state.
        In particular, check that unannotated video frames that do not have an entity in the DB are also included.

        <b>Input data:</b>
        A video and several annotated video frame DatasetStorageFilterData entries with the same media_id
        and two annotated images and five unannotated images.

        <b>Expected results:</b>
        Test passes if the correct media identifiers are returned.

        <b>Steps</b>
        1. Create test data
        2. Save test data to the repo
        3. Get unannotated media identifiers
        4. Get annotated media identifiers and limit result to two entities
        5. Check that the expected unannotated media identifiers are returned, including video frame identifiers that
           have no entry in the DB
        6. Check that the correct number of annotated media identifiers are returned, and that they are annotated.
        """
        repo = DatasetStorageFilterRepo(fxt_dataset_storage_persisted.identifier)
        repo.delete_all()
        request.addfinalizer(lambda: repo.delete_all())

        # Create video entity
        video_repo = VideoRepo(fxt_dataset_storage_persisted.identifier)
        video_repo.delete_all()
        request.addfinalizer(lambda: video_repo.delete_all())
        video_id = ID(fxt_mongo_id(11))
        video_identifier = VideoIdentifier(video_id=video_id)
        fxt_video_entity.id_ = video_id
        video_repo.save(instance=fxt_video_entity)

        # Create annotated media identifiers
        image_id_1 = ID(fxt_mongo_id(12))
        image_id_2 = ID(fxt_mongo_id(13))
        annotated_frame_indices = [
            60,
            96,
        ]  # video stride is 6, so need to be multiple of 6
        annotated_media_identifiers: list[MediaIdentifierEntity] = [
            ImageIdentifier(image_id=image_id_1),
            ImageIdentifier(image_id=image_id_2),
        ] + [
            VideoFrameIdentifier(video_id=video_id, frame_index=frame_index) for frame_index in annotated_frame_indices
        ]
        media_identifier: MediaIdentifierEntity

        # Save to repo
        annotation_scene_ids = [ID(fxt_mongo_id(i)) for i in range(len(annotated_media_identifiers))]
        for media_identifier, annotation_scene_id in zip(annotated_media_identifiers, annotation_scene_ids):
            fxt_dataset_storage_filter_data_video.media_identifier = media_identifier
            fxt_dataset_storage_filter_data_video.annotation_scene_filter_data.annotation_scene_id = annotation_scene_id
            repo.upsert_dataset_storage_filter_data(fxt_dataset_storage_filter_data_video)

        # Create unannotated media identifiers
        unannotated_image_media_identifiers: list[MediaIdentifierEntity] = [
            ImageIdentifier(image_id=ID(fxt_mongo_id(i))) for i in range(5)
        ]
        unannotated_media_identifiers: list[MediaIdentifierEntity] = unannotated_image_media_identifiers + [
            video_identifier
        ]

        # Save to repo
        fxt_dataset_storage_filter_data_video.media_annotation_state = AnnotationState.NONE
        fxt_dataset_storage_filter_data_video.annotation_scene_filter_data = None
        fxt_dataset_storage_filter_data_video.media_filter_data.unannotated_frames = fxt_video_entity.total_frames
        for media_identifier in unannotated_media_identifiers:
            fxt_dataset_storage_filter_data_video.media_identifier = media_identifier
            repo.upsert_dataset_storage_filter_data(fxt_dataset_storage_filter_data_video)

        # Get media identifiers by annotation state from DB
        retrieved_unannotated_media_identifiers = repo.get_media_identifiers_by_annotation_state(
            annotation_state=AnnotationState.NONE
        )
        retrieved_annotated_media_identifiers = repo.get_media_identifiers_by_annotation_state(
            annotation_state=AnnotationState.ANNOTATED, sample_size=2
        )

        # Assert correct response
        expected_unannotated_media_identifiers: list[MediaIdentifierEntity] = unannotated_image_media_identifiers + [
            VideoFrameIdentifier(video_id=video_id, frame_index=frame_index)
            for frame_index in range(0, fxt_video_entity.total_frames, fxt_video_entity.stride)
            if frame_index not in annotated_frame_indices
        ]
        assert set(retrieved_unannotated_media_identifiers) == set(expected_unannotated_media_identifiers)
        assert len(retrieved_annotated_media_identifiers) == 2
        assert set(retrieved_annotated_media_identifiers).issubset(set(annotated_media_identifiers))

    def test_get_video_annotation_statistics(
        self,
        request,
        fxt_dataset_storage_persisted,
        fxt_dataset_storage_filter_data_video,
        fxt_mongo_id,
    ) -> None:
        """
        <b>Description:</b>
        Check that the video annotation statistics are correctly obtained.

        <b>Input data:</b>
        Three video and several video frame DatasetStorageFilterData entries with the same media_id

        <b>Expected results:</b>
        Test passes if video annotation statistics are correct for both videos that were requested

        <b>Steps</b>
        1. Create test data
        2. Save test data to the repo
        3. Get the video annotation statistics for two videos
        4. Check that two results are returned and that both are correct
        """
        repo = DatasetStorageFilterRepo(fxt_dataset_storage_persisted.identifier)
        repo.delete_all()
        request.addfinalizer(lambda: repo.delete_all())

        video_id_1 = ID(fxt_mongo_id(12))
        video_id_2 = ID(fxt_mongo_id(13))
        video_id_3 = ID(fxt_mongo_id(14))
        media_identifiers = [
            VideoIdentifier(video_id=video_id_1),
            VideoFrameIdentifier(video_id=video_id_1, frame_index=5),
            VideoFrameIdentifier(video_id=video_id_1, frame_index=8),
            VideoIdentifier(video_id=video_id_2),
            VideoFrameIdentifier(video_id=video_id_2, frame_index=11),
            VideoFrameIdentifier(video_id=video_id_2, frame_index=12),
            VideoFrameIdentifier(video_id=video_id_2, frame_index=13),
            VideoIdentifier(video_id=video_id_3),
        ]
        annotation_scene_ids = [ID(fxt_mongo_id(i)) for i in range(len(media_identifiers))]
        fxt_dataset_storage_filter_data_video.media_filter_data.video_filter_data.unannotated_frames = 100

        for media_identifier, annotation_scene_id in zip(media_identifiers, annotation_scene_ids):
            fxt_dataset_storage_filter_data_video.media_identifier = media_identifier
            fxt_dataset_storage_filter_data_video.annotation_scene_filter_data.annotation_scene_id = annotation_scene_id
            if isinstance(media_identifier, VideoFrameIdentifier):
                fxt_dataset_storage_filter_data_video.media_annotation_state = (
                    AnnotationState.ANNOTATED
                    if media_identifier.frame_index < 12
                    else AnnotationState.PARTIALLY_ANNOTATED
                )
            else:
                fxt_dataset_storage_filter_data_video.media_annotation_state = AnnotationState.NONE
            repo.upsert_dataset_storage_filter_data(fxt_dataset_storage_filter_data_video)

        video_annotation_stats_by_id = repo.get_video_annotation_statistics_by_ids([video_id_1, video_id_2])

        assert set(video_annotation_stats_by_id.keys()) == {video_id_1, video_id_2}
        assert video_annotation_stats_by_id[video_id_1] == VideoAnnotationStatistics(
            annotated=2, partially_annotated=0, unannotated=98
        )
        assert video_annotation_stats_by_id[video_id_2] == VideoAnnotationStatistics(
            annotated=1, partially_annotated=2, unannotated=97
        )

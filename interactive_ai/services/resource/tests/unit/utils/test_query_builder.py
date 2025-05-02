# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import datetime
import logging
from copy import deepcopy
from unittest.mock import patch

import pytest
from flaky import flaky

from usecases.dataset_filter import DatasetFilter, DatasetFilterField, MediaScoreFilterField
from usecases.query_builder import MediaQueryResult, QueryBuilder, QueryResults

from geti_types import ID, ImageIdentifier, ProjectIdentifier, VideoFrameIdentifier
from iai_core.entities.annotation import Annotation, AnnotationScene, AnnotationSceneKind
from iai_core.entities.annotation_scene_state import AnnotationSceneState, AnnotationState
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.dataset_storage import DatasetStorage
from iai_core.entities.dataset_storage_filter_data import (
    AnnotationSceneFilterData,
    DatasetStorageFilterData,
    MediaFilterData,
)
from iai_core.entities.datasets import Dataset, DatasetIdentifier, DatasetPurpose
from iai_core.entities.media import MediaPreprocessingStatus
from iai_core.entities.shapes import Rectangle
from iai_core.entities.video_annotation_statistics import VideoAnnotationStatistics
from iai_core.repos import (
    AnnotationSceneRepo,
    AnnotationSceneStateRepo,
    DatasetRepo,
    DatasetStorageRepo,
    ImageRepo,
    VideoRepo,
)
from iai_core.repos.dataset_storage_filter_repo import DatasetStorageFilterRepo
from iai_core.services.dataset_storage_filter_service import DatasetStorageFilterService
from iai_core.utils.constants import DEFAULT_USER_NAME

logger = logging.getLogger(__name__)


class TestQueryBuilder:
    @pytest.mark.parametrize("fxt_filled_image_dataset_storage", [200], indirect=True)
    @flaky(max_runs=5, min_passes=1)
    def test_pagination_speed(self, request, fxt_filled_image_dataset_storage, fxt_media_filter):
        """
        Tests the pagination speed of the query builder on a repo with 200 images.
        First, it is timed how long it takes to get an item from the first page and then
        that time is compared against the time it takes to get the last page. This must
        not be more than 20% slower. It is also verified that the item in the last page
        is the expected item.
        """
        image_repo = ImageRepo(fxt_filled_image_dataset_storage.identifier)
        assert image_repo.count() == 200
        dataset_filter = DatasetFilter.from_dict(
            query=fxt_media_filter,
            limit=1,
            sort_by=DatasetFilterField.MEDIA_UPLOAD_DATE,
        )
        last_image_media_id = image_repo.get_one(latest=True).media_identifier.media_id

        # First time query is much slower so before timing we get rid of this overhead
        QueryBuilder.get_media_results_for_dataset_storage_filter(
            dataset_filter=dataset_filter,
            dataset_storage_identifier=fxt_filled_image_dataset_storage.identifier,
        )

        t1 = datetime.datetime.now()
        QueryBuilder.get_media_results_for_dataset_storage_filter(
            dataset_filter=dataset_filter,
            dataset_storage_identifier=fxt_filled_image_dataset_storage.identifier,
        )
        time_first_page = datetime.datetime.now() - t1

        dataset_filter.skip = 199
        t2 = datetime.datetime.now()
        query_results = QueryBuilder.get_media_results_for_dataset_storage_filter(
            dataset_filter=dataset_filter,
            dataset_storage_identifier=fxt_filled_image_dataset_storage.identifier,
        )
        time_last_page = datetime.datetime.now() - t2

        # Assert the query didn't match spurious data
        assert query_results.matching_images_count == 200
        assert query_results.matching_videos_count == 0
        # Assert fetching last page is not more than 20% slower than the first page
        assert (time_first_page * 1.2) > time_last_page
        # Assert the right media item is on the last page
        assert query_results.media_identifiers[0].media_id == last_image_media_id

    @pytest.mark.parametrize("fxt_filled_image_dataset_storage", [40], indirect=True)
    def test_sort_stability(self, fxt_filled_image_dataset_storage, fxt_media_filter) -> None:
        """
        This test verifies that the output is always ordered in a stable way, even when some items have
        duplicate values on the sorting field.
        """
        # Fetch 20 items in the middle, twice, then ensure that the same items are returned and in the same order
        dataset_filter = DatasetFilter.from_dict(
            query=fxt_media_filter,
            limit=20,
            skip=10,
            sort_by=DatasetFilterField.MEDIA_UPLOAD_DATE,
        )
        query_result_1 = QueryBuilder.get_media_results_for_dataset_storage_filter(
            dataset_filter=dataset_filter,
            dataset_storage_identifier=fxt_filled_image_dataset_storage.identifier,
        )
        query_result_2 = QueryBuilder.get_media_results_for_dataset_storage_filter(
            dataset_filter=dataset_filter,
            dataset_storage_identifier=fxt_filled_image_dataset_storage.identifier,
        )
        assert query_result_1.media_identifiers == query_result_2.media_identifiers

    def test_use_latest_annotation(
        self,
        fxt_storage_with_partial_and_full_annotation_on_one_image,
        fxt_annotation_scene_state_filter,
    ):
        """
        This tests verifies that the query builder constructs a query that only takes
        the latest annotation per annotation kind per media identifier into account.
        """

        fxt_annotation_scene_state_filter["rules"][0]["value"] = ["PARTIALLY_ANNOTATED"]
        dataset_filter = DatasetFilter.from_dict(
            query=fxt_annotation_scene_state_filter,
            limit=100,
            sort_by=DatasetFilterField.MEDIA_WIDTH,
        )
        results = QueryBuilder.get_media_results_for_dataset_storage_filter(
            dataset_filter=dataset_filter,
            dataset_storage_identifier=fxt_storage_with_partial_and_full_annotation_on_one_image.identifier,
        )
        assert len(results.media_identifiers) == 0

        fxt_annotation_scene_state_filter["rules"][0]["value"] = ["ANNOTATED"]
        dataset_filter = DatasetFilter.from_dict(
            query=fxt_annotation_scene_state_filter,
            limit=100,
            sort_by=DatasetFilterField.MEDIA_WIDTH,
        )
        results = QueryBuilder.get_media_results_for_dataset_storage_filter(
            dataset_filter=dataset_filter,
            dataset_storage_identifier=fxt_storage_with_partial_and_full_annotation_on_one_image.identifier,
        )
        assert len(results.media_identifiers) == 1

    def test_shape_area_filter(
        self,
        fxt_storage_with_partial_and_full_annotation_on_one_image,
    ) -> None:
        """
        This tests verifies that the shape filters work as expected. Dataset contains
        one rectangle with an area of 50% of the image.
        """

        # Dict for both shape filters. First value in list is expected to match one
        # item while the second should not match any items.
        test_cases = {"shape_area_percentage": [0.4, 0.6], "shape_area_pixel": [0, 1]}

        for filter_rule, value in test_cases.items():
            shape_filter = {
                "condition": "and",
                "rules": [
                    {
                        "field": filter_rule,
                        "operator": "greater",
                        "value": value[0],  # type: ignore
                    }
                ],
            }

            # First test with filter that should match the item with one shape
            dataset_filter = DatasetFilter.from_dict(
                query=shape_filter, limit=100, sort_by=DatasetFilterField.MEDIA_WIDTH
            )
            results = QueryBuilder.get_media_results_for_dataset_storage_filter(
                dataset_filter=dataset_filter,
                dataset_storage_identifier=fxt_storage_with_partial_and_full_annotation_on_one_image.identifier,
            )
            assert len(results.media_identifiers) == 1

            # Now test with filter that should not match the item with one shape anymore
            shape_filter["rules"][0]["value"] = value[1]  # type: ignore
            dataset_filter = DatasetFilter.from_dict(
                query=shape_filter, limit=100, sort_by=DatasetFilterField.MEDIA_WIDTH
            )
            results = QueryBuilder.get_media_results_for_dataset_storage_filter(
                dataset_filter=dataset_filter,
                dataset_storage_identifier=fxt_storage_with_partial_and_full_annotation_on_one_image.identifier,
            )
            assert len(results.media_identifiers) == 0

    def test_user_filter(
        self,
        fxt_storage_with_partial_and_full_annotation_on_one_image,
    ) -> None:
        """
        This tests verifies that the user filter works as expected
        """

        user_filter = {
            "condition": "and",
            "rules": [
                {
                    "field": "user_name",
                    "operator": "equal",
                    "value": DEFAULT_USER_NAME,
                }
            ],
        }

        # First test with filter that should match one item
        dataset_filter = DatasetFilter.from_dict(query=user_filter, limit=100, sort_by=DatasetFilterField.MEDIA_WIDTH)
        results = QueryBuilder.get_media_results_for_dataset_storage_filter(
            dataset_filter=dataset_filter,
            dataset_storage_identifier=fxt_storage_with_partial_and_full_annotation_on_one_image.identifier,
        )
        assert len(results.media_identifiers) == 1

        # Now test with filter that should not match anything
        user_filter["rules"][0]["value"] = "random name with no match"  # type: ignore
        dataset_filter = DatasetFilter.from_dict(query=user_filter, limit=100, sort_by=DatasetFilterField.MEDIA_WIDTH)
        results = QueryBuilder.get_media_results_for_dataset_storage_filter(
            dataset_filter=dataset_filter,
            dataset_storage_identifier=fxt_storage_with_partial_and_full_annotation_on_one_image.identifier,
        )
        assert len(results.media_identifiers) == 0

    def test_matching_video_frames(
        self,
        request,
        fxt_mongo_id,
        fxt_image_entity,
        fxt_video_entity,
        fxt_dataset_storage,
        fxt_annotation_scene,
    ) -> None:
        """
        Basic test that checks the filtering for a dataset storage works as expected.
        """
        ds_identifier = fxt_dataset_storage.identifier
        ds_filter_repo = DatasetStorageFilterRepo(dataset_storage_identifier=ds_identifier)
        request.addfinalizer(lambda: ds_filter_repo.delete_all())

        video_repo = VideoRepo(dataset_storage_identifier=ds_identifier)
        request.addfinalizer(lambda: video_repo.delete_all())

        for i in range(20):
            video_entity = deepcopy(fxt_video_entity)
            video_id = fxt_mongo_id(i)
            video_entity.id_ = video_id
            video_repo.save(video_entity)

            video_frame_id_1 = VideoFrameIdentifier(video_id=video_id, frame_index=5)
            video_frame_id_2 = VideoFrameIdentifier(video_id=video_id, frame_index=3)
            video_frame_id_3 = VideoFrameIdentifier(video_id=video_id, frame_index=8)

            ds_filter_data_video = DatasetStorageFilterData.create_dataset_storage_filter_data(
                media_identifier=video_entity.media_identifier,
                media=video_entity,
                media_annotation_state=AnnotationState.NONE,
                preprocessing=MediaPreprocessingStatus.FINISHED,
            )
            ds_filter_repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data=ds_filter_data_video)
            ds_filter_data_1 = DatasetStorageFilterData.create_dataset_storage_filter_data(
                media_identifier=video_frame_id_1,
                media=video_entity,
                annotation_scene=fxt_annotation_scene,
                media_annotation_state=AnnotationState.ANNOTATED,
                preprocessing=MediaPreprocessingStatus.FINISHED,
            )
            ds_filter_repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data=ds_filter_data_1)
            ds_filter_data_2 = DatasetStorageFilterData.create_dataset_storage_filter_data(
                media_identifier=video_frame_id_2,
                media=video_entity,
                annotation_scene=fxt_annotation_scene,
                media_annotation_state=AnnotationState.ANNOTATED,
                preprocessing=MediaPreprocessingStatus.FINISHED,
            )
            ds_filter_repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data=ds_filter_data_2)
            ds_filter_data_3 = DatasetStorageFilterData.create_dataset_storage_filter_data(
                media_identifier=video_frame_id_3,
                media=video_entity,
                annotation_scene=fxt_annotation_scene,
                media_annotation_state=AnnotationState.ANNOTATED,
                preprocessing=MediaPreprocessingStatus.FINISHED,
            )
            ds_filter_repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data=ds_filter_data_3)

        image_repo = ImageRepo(ds_identifier)
        request.addfinalizer(lambda: image_repo.delete_all())

        for i in range(15):
            image_id = fxt_mongo_id(20 + i)
            image_entity = deepcopy(fxt_image_entity)
            image_entity.id_ = image_id
            image_repo.save(image_entity)

            media_filter_data = MediaFilterData.from_media(media=image_entity)
            annotation_scene_filter_data = AnnotationSceneFilterData.from_annotation_scene(
                annotation_scene=fxt_annotation_scene
            )
            dataset_storage_filter_data = DatasetStorageFilterData(
                media_identifier=image_entity.media_identifier,
                media_filter_data=media_filter_data,
                annotation_scene_filter_data=annotation_scene_filter_data,
                media_annotation_state=AnnotationState.ANNOTATED,
                preprocessing=MediaPreprocessingStatus.FINISHED,
            )
            ds_filter_repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data)

        ds_filter = DatasetFilter.from_dict(
            query={
                "condition": "and",
                "rules": [
                    {
                        "field": "ANNOTATION_SCENE_STATE",
                        "operator": "EQUAL",
                        "value": "ANNOTATED",
                    },
                ],
            },
            limit=10,
            sort_by=DatasetFilterField.MEDIA_NAME,
        )
        ds_filter_all_videos = DatasetFilter.from_dict(
            query={
                "condition": "and",
                "rules": [
                    {
                        "field": "MEDIA_TYPE",
                        "operator": "EQUAL",
                        "value": "video",
                    },
                ],
            },
            limit=10,
            sort_by=DatasetFilterField.MEDIA_NAME,
        )

        result = QueryBuilder.get_media_results_for_dataset_storage_filter(
            dataset_filter=ds_filter,
            dataset_storage_identifier=ds_identifier,
        )
        result_all_video_frames = QueryBuilder.get_media_results_for_dataset_storage_filter(
            dataset_filter=ds_filter_all_videos,
            dataset_storage_identifier=ds_identifier,
        )

        assert len(result.media_query_results) == 10
        assert result.matching_images_count == 15
        assert result.matching_videos_count == 20
        assert result.matching_video_frames_count == 60
        assert len(result_all_video_frames.media_query_results) == 10
        assert result_all_video_frames.matching_images_count == 0
        assert result_all_video_frames.matching_videos_count == 20
        assert result_all_video_frames.matching_video_frames_count == 20 * fxt_video_entity.total_frames

    def test_media_type_filter(
        self,
        request,
        fxt_image_entity,
        fxt_video_entity,
        fxt_dataset_storage,
        fxt_annotation_scene,
    ) -> None:
        """
        Basic test that checks the filtering for a dataset storage works as expected.
        """
        ds_identifier = fxt_dataset_storage.identifier
        ds_filter_repo = DatasetStorageFilterRepo(dataset_storage_identifier=ds_identifier)
        request.addfinalizer(lambda: ds_filter_repo.delete_all())

        video_repo = VideoRepo(dataset_storage_identifier=ds_identifier)
        request.addfinalizer(lambda: video_repo.delete_all())
        video_repo.save(fxt_video_entity)

        video_id = fxt_video_entity.media_identifier.media_id
        video_frame_id_1 = VideoFrameIdentifier(video_id=video_id, frame_index=5)
        video_frame_id_2 = VideoFrameIdentifier(video_id=video_id, frame_index=13)
        video_frame_id_3 = VideoFrameIdentifier(video_id=video_id, frame_index=10)

        ds_filter_data_video = DatasetStorageFilterData.create_dataset_storage_filter_data(
            media_identifier=fxt_video_entity.media_identifier,
            media=fxt_video_entity,
            media_annotation_state=AnnotationState.NONE,
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )
        ds_filter_repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data=ds_filter_data_video)
        ds_filter_data_1 = DatasetStorageFilterData.create_dataset_storage_filter_data(
            media_identifier=video_frame_id_1,
            media=fxt_video_entity,
            annotation_scene=fxt_annotation_scene,
            media_annotation_state=AnnotationState.ANNOTATED,
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )
        ds_filter_repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data=ds_filter_data_1)
        ds_filter_data_2 = DatasetStorageFilterData.create_dataset_storage_filter_data(
            media_identifier=video_frame_id_2,
            media=fxt_video_entity,
            annotation_scene=fxt_annotation_scene,
            media_annotation_state=AnnotationState.ANNOTATED,
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )
        ds_filter_repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data=ds_filter_data_2)
        ds_filter_data_3 = DatasetStorageFilterData.create_dataset_storage_filter_data(
            media_identifier=video_frame_id_3,
            annotation_scene=fxt_annotation_scene,
            media_annotation_state=AnnotationState.ANNOTATED,
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )
        ds_filter_repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data=ds_filter_data_3)

        image_repo = ImageRepo(ds_identifier)
        request.addfinalizer(lambda: image_repo.delete_all())
        image_repo.save(fxt_image_entity)

        media_filter_data = MediaFilterData.from_media(media=fxt_image_entity)
        annotation_scene_filter_data = AnnotationSceneFilterData.from_annotation_scene(
            annotation_scene=fxt_annotation_scene
        )
        dataset_storage_filter_data = DatasetStorageFilterData(
            media_identifier=fxt_image_entity.media_identifier,
            media_filter_data=media_filter_data,
            annotation_scene_filter_data=annotation_scene_filter_data,
            media_annotation_state=AnnotationState.ANNOTATED,
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )
        ds_filter_repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data)

        ds_filter_image = DatasetFilter.from_dict(
            query={
                "condition": "and",
                "rules": [
                    {
                        "field": "MEDIA_TYPE",
                        "operator": "EQUAL",
                        "value": "image",
                    },
                ],
            },
            limit=100,
            sort_by=DatasetFilterField.MEDIA_NAME,
        )
        ds_filter_annotated_video = DatasetFilter.from_dict(
            query={
                "condition": "and",
                "rules": [
                    {
                        "field": "MEDIA_TYPE",
                        "operator": "EQUAL",
                        "value": "video",
                    },
                    {
                        "field": "ANNOTATION_SCENE_STATE",
                        "operator": "EQUAL",
                        "value": "ANNOTATED",
                    },
                ],
            },
            limit=100,
            sort_by=DatasetFilterField.MEDIA_NAME,
        )

        result_images = QueryBuilder.get_media_results_for_dataset_storage_filter(
            dataset_filter=ds_filter_image,
            dataset_storage_identifier=ds_identifier,
        )
        result_annotated_video = QueryBuilder.get_media_results_for_dataset_storage_filter(
            dataset_filter=ds_filter_annotated_video,
            dataset_storage_identifier=ds_identifier,
        )

        assert len(result_images.media_query_results) == 1
        assert result_images.media_query_results[0].media_identifier.media_id == fxt_image_entity.id_
        assert len(result_annotated_video.media_query_results) == 1
        assert result_annotated_video.matching_video_frames_count == 3
        assert result_annotated_video.media_query_results[0].media_identifier.media_id == fxt_video_entity.id_
        assert result_annotated_video.media_query_results[0].video_annotation_statistics == VideoAnnotationStatistics(
            annotated=3,
            partially_annotated=0,
            unannotated=(fxt_video_entity.total_frames - 3),
        )

    def test_media_score_filter_deterministic_scores(
        self,
        fxt_media_score_filter_factory,
        fxt_project_with_media_scores,
        fxt_model_test_result_ids,
    ) -> None:
        """
        <b>Description:</b>
        Check if the media score filter works correctly

        <b>Input data:</b>
        Project including media scores for 2 model tests with 36 media identifiers

        <b>Expected results:</b>
        We expect to get results with half of the media items, 16 videos and 2 image = 18 = 36/2
        This confirms filtering by label id and score works
        """
        label_id = None
        score_threshold = 0.5
        score_operator = "greater"
        media_score_filter_json = fxt_media_score_filter_factory(label_id, score_threshold, score_operator)
        media_score_filter = DatasetFilter.from_dict(
            query=media_score_filter_json,
            sort_by=MediaScoreFilterField.SCORE,
            limit=40,
        )
        results = QueryBuilder.get_results_for_media_scores_dataset_filter(
            dataset_filter=media_score_filter,
            dataset_storage_identifier=fxt_project_with_media_scores.get_dataset_storages()[0].identifier,
            model_test_result_id=fxt_model_test_result_ids[0],
        )

        assert isinstance(results, QueryResults)
        assert len(results.media_identifiers) == 18
        assert results.matching_images_count == 2
        assert results.matching_videos_count == 4
        assert results.matching_video_frames_count == 16
        for identifier in results.media_identifiers:
            assert isinstance(identifier, ImageIdentifier | VideoFrameIdentifier)
        assert isinstance(results, QueryResults)

    def test_media_score_filter_random_scores(
        self,
        fxt_media_score_filter_factory,
        fxt_project_with_media_scores,
        fxt_model_test_result_ids,
        fxt_label_ids,
    ) -> None:
        """
        <b>Description:</b>
        Check if the media score filter works correctly

        <b>Input data:</b>
        Project including media scores for 2 model tests with 36 media identifiers

         <b>Expected results:</b>
        We expect to get results with all the media items, 16 videos and 20 image = 36
        This confirms we can get all necessary results
        """
        for model_test_result_id in fxt_model_test_result_ids:
            for label_id in fxt_label_ids:
                score_threshold = 0.0
                score_operator = "greater_or_equal"
                media_score_filter_json = fxt_media_score_filter_factory(label_id, score_threshold, score_operator)
                media_score_filter = DatasetFilter.from_dict(
                    query=media_score_filter_json,
                    sort_by=MediaScoreFilterField.SCORE,
                    limit=40,
                )
                results = QueryBuilder.get_results_for_media_scores_dataset_filter(
                    dataset_filter=media_score_filter,
                    dataset_storage_identifier=fxt_project_with_media_scores.get_dataset_storages()[0].identifier,
                    model_test_result_id=model_test_result_id,
                )

                assert isinstance(results, QueryResults)
                assert len(results.media_identifiers) == 36
                assert results.matching_images_count == 20
                assert results.matching_videos_count == 4
                for identifier in results.media_identifiers:
                    assert isinstance(identifier, ImageIdentifier | VideoFrameIdentifier)

    def test_get_video_frame_results_for_dataset_storage_filter(
        self,
        request,
        fxt_video_entity,
        fxt_dataset_storage,
        fxt_annotation_scene,
    ) -> None:
        """
        Basic test that checks the filtering for a dataset storage works as expected.
        """
        ds_identifier = fxt_dataset_storage.identifier
        ds_filter_repo = DatasetStorageFilterRepo(dataset_storage_identifier=ds_identifier)
        request.addfinalizer(lambda: ds_filter_repo.delete_all())

        video_repo = VideoRepo(dataset_storage_identifier=ds_identifier)
        request.addfinalizer(lambda: video_repo.delete_all())
        video_repo.save(fxt_video_entity)

        video_id = fxt_video_entity.media_identifier.media_id
        video_frame_id_1 = VideoFrameIdentifier(video_id=video_id, frame_index=5)
        video_frame_id_2 = VideoFrameIdentifier(video_id=video_id, frame_index=3)
        video_frame_id_3 = VideoFrameIdentifier(video_id=ID("wrong_id"), frame_index=9)

        ds_filter_data_video = DatasetStorageFilterData.create_dataset_storage_filter_data(
            media_identifier=fxt_video_entity.media_identifier,
            media=fxt_video_entity,
            media_annotation_state=AnnotationState.NONE,
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )
        ds_filter_repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data=ds_filter_data_video)
        ds_filter_data_1 = DatasetStorageFilterData.create_dataset_storage_filter_data(
            media_identifier=video_frame_id_1,
            media=fxt_video_entity,
            annotation_scene=fxt_annotation_scene,
            media_annotation_state=AnnotationState.ANNOTATED,
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )
        ds_filter_repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data=ds_filter_data_1)
        ds_filter_data_2 = DatasetStorageFilterData.create_dataset_storage_filter_data(
            media_identifier=video_frame_id_2,
            media=fxt_video_entity,
            annotation_scene=fxt_annotation_scene,
            media_annotation_state=AnnotationState.ANNOTATED,
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )
        ds_filter_repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data=ds_filter_data_2)
        ds_filter_data_3 = DatasetStorageFilterData.create_dataset_storage_filter_data(
            media_identifier=video_frame_id_3,
            annotation_scene=fxt_annotation_scene,
            media_annotation_state=AnnotationState.ANNOTATED,
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )
        ds_filter_repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data=ds_filter_data_3)

        ds_filter_all = DatasetFilter.from_dict(
            query={},
            limit=100,
            sort_by=DatasetFilterField.MEDIA_NAME,
        )
        ds_filter_annotated = DatasetFilter.from_dict(
            query={
                "condition": "and",
                "rules": [
                    {
                        "field": "ANNOTATION_SCENE_STATE",
                        "id": "a2e742b2-edfc-4898-b568-f13127b13406",
                        "operator": "EQUAL",
                        "value": "ANNOTATED",
                    }
                ],
            },
            limit=100,
            sort_by=DatasetFilterField.MEDIA_NAME,
        )
        expected_frames = list(range(0, fxt_video_entity.total_frames, 3))
        expected_all_query_results = QueryResults(
            media_query_results=[],
            skip=100,
            matching_images_count=0,
            matching_videos_count=1,
            matching_video_frames_count=4,
            total_images_count=0,
            total_videos_count=2,
        )

        expected_annotated_query_results = QueryResults(
            media_query_results=[
                MediaQueryResult(
                    media_identifier=video_frame_id_2,
                    media=fxt_video_entity,
                    annotation_scene_id=fxt_annotation_scene.id_,
                    last_annotator_id=fxt_annotation_scene.last_annotator_id,
                ),
                MediaQueryResult(
                    media_identifier=video_frame_id_1,
                    media=fxt_video_entity,
                    annotation_scene_id=fxt_annotation_scene.id_,
                    last_annotator_id=fxt_annotation_scene.last_annotator_id,
                ),
            ],
            matching_video_frames_count=2,
            matching_videos_count=1,
            matching_images_count=0,
            total_videos_count=2,
            total_images_count=0,
            skip=100,
        )

        result_all = QueryBuilder.get_video_frame_results_for_dataset_storage_filter(
            dataset_filter=ds_filter_all,
            dataset_storage_identifier=ds_identifier,
            video_id=video_id,
            fps=2,
            include_frame_details=False,
        )
        result_annotated = QueryBuilder.get_video_frame_results_for_dataset_storage_filter(
            dataset_filter=ds_filter_annotated,
            dataset_storage_identifier=ds_identifier,
            video_id=video_id,
            fps=0,
            include_frame_details=True,
        )

        assert result_all.video_frame_indices == expected_frames
        assert result_all.query_results == expected_all_query_results
        assert result_annotated.video_frame_indices == [3, 5]
        assert result_annotated.query_results == expected_annotated_query_results

    def test_get_media_results_for_dataset_storage_filter(
        self,
        request,
        fxt_image_entity,
        fxt_dataset_storage,
        fxt_annotation_scene,
    ) -> None:
        """
        Basic test that checks the filtering for a dataset storage works as expected.
        """
        ds_identifier = fxt_dataset_storage.identifier
        ds_filter_repo = DatasetStorageFilterRepo(dataset_storage_identifier=ds_identifier)
        request.addfinalizer(lambda: ds_filter_repo.delete_all())
        image_repo = ImageRepo(ds_identifier)
        request.addfinalizer(lambda: image_repo.delete_all())
        image_repo.save(fxt_image_entity)

        media_filter_data = MediaFilterData.from_media(media=fxt_image_entity)
        annotation_scene_filter_data = AnnotationSceneFilterData.from_annotation_scene(
            annotation_scene=fxt_annotation_scene
        )
        dataset_storage_filter_data = DatasetStorageFilterData(
            media_identifier=fxt_image_entity.media_identifier,
            media_filter_data=media_filter_data,
            annotation_scene_filter_data=annotation_scene_filter_data,
            media_annotation_state=AnnotationState.ANNOTATED,
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )
        ds_filter_repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data)

        ds_filter = DatasetFilter.from_dict(
            query={},
            limit=100,
            sort_by=DatasetFilterField.MEDIA_NAME,
        )
        expected_media_query_results = [
            MediaQueryResult(
                media_identifier=fxt_image_entity.media_identifier,
                media=fxt_image_entity,
                annotation_scene_id=fxt_annotation_scene.id_,
                roi_id=None,
                last_annotator_id=ID("editor"),
            )
        ]
        expected_query_results = QueryResults(
            media_query_results=expected_media_query_results,
            skip=ds_filter.limit + ds_filter.skip,
            matching_images_count=1,
            matching_videos_count=0,
            matching_video_frames_count=0,
            total_images_count=1,
            total_videos_count=0,
        )

        with patch.object(DatasetStorageFilterRepo, "count", side_effect=[1, 0]):
            result = QueryBuilder.get_media_results_for_dataset_storage_filter(
                dataset_filter=ds_filter, dataset_storage_identifier=ds_identifier
            )

        assert result == expected_query_results

    def test_get_media_results_for_dataset_storage_filter_empty_annotation(
        self,
        request,
        fxt_image_entity,
        fxt_dataset_storage,
        fxt_annotation_scene,
    ) -> None:
        """
        If the media annotation state is NONE despite the existence of an annotation scene, it should be an empty
        annotation. The results should not return the annotation scene id.
        """
        ds_identifier = fxt_dataset_storage.identifier
        ds_filter_repo = DatasetStorageFilterRepo(dataset_storage_identifier=ds_identifier)
        request.addfinalizer(lambda: ds_filter_repo.delete_all())
        image_repo = ImageRepo(ds_identifier)
        request.addfinalizer(lambda: image_repo.delete_all())
        image_repo.save(fxt_image_entity)

        media_filter_data = MediaFilterData.from_media(media=fxt_image_entity)
        annotation_scene_filter_data = AnnotationSceneFilterData.from_annotation_scene(
            annotation_scene=fxt_annotation_scene
        )
        dataset_storage_filter_data = DatasetStorageFilterData(
            media_identifier=fxt_image_entity.media_identifier,
            media_filter_data=media_filter_data,
            annotation_scene_filter_data=annotation_scene_filter_data,
            media_annotation_state=AnnotationState.NONE,
            preprocessing=MediaPreprocessingStatus.FINISHED,
        )
        ds_filter_repo.upsert_dataset_storage_filter_data(dataset_storage_filter_data)

        ds_filter = DatasetFilter.from_dict(
            query={},
            limit=100,
            sort_by=DatasetFilterField.MEDIA_NAME,
        )
        expected_media_query_results = [
            MediaQueryResult(
                media_identifier=fxt_image_entity.media_identifier,
                media=fxt_image_entity,
                annotation_scene_id=None,
                roi_id=None,
                last_annotator_id=None,
            )
        ]
        expected_query_results = QueryResults(
            media_query_results=expected_media_query_results,
            skip=ds_filter.limit + ds_filter.skip,
            matching_images_count=1,
            matching_videos_count=0,
            matching_video_frames_count=0,
            total_images_count=1,
            total_videos_count=0,
        )

        with patch.object(DatasetStorageFilterRepo, "count", side_effect=[1, 0]):
            result = QueryBuilder.get_media_results_for_dataset_storage_filter(
                dataset_filter=ds_filter, dataset_storage_identifier=ds_identifier
            )

        assert result == expected_query_results

    @pytest.mark.parametrize("fxt_filled_image_dataset_storage", [5], indirect=True)
    def test_get_results_for_dataset(
        self,
        request,
        fxt_filled_image_dataset_storage,
        fxt_annotation_scene,
        fxt_image_entity,
        fxt_label_schema,
    ) -> None:
        """
        Basic test that checks the filtering for a specific dataset works as expected in
        a dataset storage with 2 datasets. The fixture already contains a dataset with 5
        items
        """
        ds_identifier = fxt_filled_image_dataset_storage.identifier
        image_repo = ImageRepo(ds_identifier)
        ann_scene_repo = AnnotationSceneRepo(ds_identifier)
        dataset_repo = DatasetRepo(ds_identifier)
        request.addfinalizer(lambda: image_repo.delete_all())
        request.addfinalizer(lambda: ann_scene_repo.delete_all())
        request.addfinalizer(lambda: dataset_repo.delete_all())
        image_repo.save(fxt_image_entity)
        ann_scene_repo.save(fxt_annotation_scene)
        # Add additional dataset to the DatasetStorage with 1 item
        dataset = Dataset(
            id=DatasetRepo.generate_id(),
            purpose=DatasetPurpose.TRAINING,
            label_schema_id=fxt_label_schema.id_,
        )
        dataset.append(
            DatasetItem(
                id_=DatasetRepo.generate_id(),
                media=fxt_image_entity,
                annotation_scene=fxt_annotation_scene,
            )
        )
        dataset_repo.save_deep(dataset)
        ds_filter = DatasetFilter.from_dict(query={}, limit=100)
        dataset_identifier = DatasetIdentifier.from_ds_identifier(ds_identifier, dataset.id_)
        results = QueryBuilder.get_results_for_training_revision_filter(
            dataset_filter=ds_filter,
            dataset_identifier=dataset_identifier,
        )
        assert len(results.media_identifiers) == 1

    @pytest.mark.parametrize("fxt_filled_image_dataset_storage", [5], indirect=True)
    def test_filter_images_in_training_revision(self, fxt_filled_image_dataset_storage):
        # Note: fxt_filled_image_dataset_storage assigns subset 'TRAINING' to all items
        subset_filter = DatasetFilter.from_dict(
            query={
                "condition": "and",
                "rules": [
                    {
                        "field": "subset",
                        "operator": "equal",
                        "value": "training",
                    }
                ],
            },
            limit=100,
        )
        dataset = next(iter(DatasetRepo(fxt_filled_image_dataset_storage.identifier).get_all()))
        dataset_identifier = DatasetIdentifier.from_ds_identifier(
            fxt_filled_image_dataset_storage.identifier, dataset.id_
        )
        results = QueryBuilder.get_results_for_training_revision_filter(
            dataset_filter=subset_filter, dataset_identifier=dataset_identifier
        )
        assert len(results.media_identifiers) == 5
        assert results.media_query_results[0].annotation_scene_id is not None
        assert results.media_query_results[0].roi_id is not None

    @pytest.mark.parametrize("fxt_filled_video_dataset_storage", [3], indirect=True)
    def test_filter_training_revision_with_video_frames(self, fxt_filled_video_dataset_storage):
        dataset_storage = fxt_filled_video_dataset_storage
        dataset = next(iter(DatasetRepo(dataset_storage.identifier).get_all()))

        ds_filter = DatasetFilter.from_dict(
            query={},
            limit=100,
        )
        dataset_identifier = DatasetIdentifier.from_ds_identifier(
            fxt_filled_video_dataset_storage.identifier, dataset.id_
        )

        results = QueryBuilder.get_results_for_training_revision_filter(
            dataset_filter=ds_filter,
            dataset_identifier=dataset_identifier,
        )
        assert results.matching_images_count == 0
        assert results.matching_video_frames_count == 12
        assert results.matching_videos_count == 3
        assert results.total_videos_count == 3
        assert results.total_images_count == 0
        assert len(results.media_identifiers) == 3
        assert results.media_identifiers[0].matched_frames == 4

    @pytest.mark.parametrize("fxt_filled_video_dataset_storage", [3], indirect=True)
    def test_filter_in_video_frames_training_revision(self, fxt_filled_video_dataset_storage):
        dataset_storage = fxt_filled_video_dataset_storage
        dataset = next(iter(DatasetRepo(dataset_storage.identifier).get_all()))
        video = next(iter(VideoRepo(dataset_storage.identifier).get_all()))
        # fxt_filled_video_dataset_storage assigns each video to a different subset:
        # determine which one corresponds to our video
        video_subset = next(
            item.subset for item in dataset if item.media_identifier.media_id == video.media_identifier.media_id
        )
        subset_filter = DatasetFilter.from_dict(
            query={
                "condition": "and",
                "rules": [
                    {
                        "field": "subset",
                        "operator": "equal",
                        "value": video_subset.name.lower(),
                    }
                ],
            },
            limit=100,
            sort_by=DatasetFilterField.MEDIA_UPLOAD_DATE,
        )
        dataset_identifier = DatasetIdentifier.from_ds_identifier(
            fxt_filled_video_dataset_storage.identifier, dataset.id_
        )

        results = QueryBuilder.get_results_for_training_revision_filter(
            dataset_filter=subset_filter,
            dataset_identifier=dataset_identifier,
            video_id=video.id_,
        )
        assert len(results.media_identifiers) == 4
        assert results.media_query_results[0].annotation_scene_id is not None
        assert results.media_query_results[0].roi_id is not None
        assert results.media_query_results[0].last_annotator_id == DEFAULT_USER_NAME


@pytest.fixture
def fxt_storage_with_partial_and_full_annotation_on_one_image(request, fxt_mongo_id, fxt_image_entity):
    """
    DatasetStorage to which first a partially annotated annotation is added and afterwards
    a fully annotated annotation is added.
    """
    media_identifier = fxt_image_entity.media_identifier
    project_identifier = ProjectIdentifier(workspace_id=fxt_mongo_id(0), project_id=fxt_mongo_id(1))
    test_dataset_storage = DatasetStorage(
        name="testing_storage",
        project_id=fxt_mongo_id(1),
        _id=DatasetStorageRepo.generate_id(),
        use_for_training=True,
    )
    ds_repo = DatasetStorageRepo(project_identifier)
    ds_repo.save(test_dataset_storage)
    request.addfinalizer(lambda: ds_repo.delete_by_id(test_dataset_storage.id_))

    ds_identifier = test_dataset_storage.identifier
    image_repo = ImageRepo(ds_identifier)
    image_repo.delete_all()
    image_repo.save(fxt_image_entity)
    request.addfinalizer(lambda: image_repo.delete_all())
    filter_repo = DatasetStorageFilterRepo(ds_identifier)
    filter_repo.delete_all()
    request.addfinalizer(lambda: filter_repo.delete_all())

    for state in [AnnotationState.PARTIALLY_ANNOTATED, AnnotationState.ANNOTATED]:
        annotation_scene = AnnotationScene(
            kind=AnnotationSceneKind.ANNOTATION,
            media_identifier=media_identifier,
            media_height=1,
            media_width=1,
            id_=AnnotationSceneRepo.generate_id(),
            annotations=[Annotation(shape=Rectangle(x1=0, y1=0, x2=0.5, y2=1), labels=[])],
        )
        AnnotationSceneRepo(test_dataset_storage.identifier).save(annotation_scene)
        annotation_scene_state = AnnotationSceneState(
            media_identifier=media_identifier,
            annotation_scene_id=annotation_scene.id_,
            annotation_state_per_task={fxt_mongo_id(1): state},
            unannotated_rois={},
            id_=AnnotationSceneStateRepo.generate_id(),
        )
        AnnotationSceneStateRepo(test_dataset_storage.identifier).save(annotation_scene_state)

        DatasetStorageFilterService.on_new_annotation_scene(
            project_id=ds_identifier.project_id,
            dataset_storage_id=ds_identifier.dataset_storage_id,
            annotation_scene_id=annotation_scene.id_,
        )

    yield test_dataset_storage

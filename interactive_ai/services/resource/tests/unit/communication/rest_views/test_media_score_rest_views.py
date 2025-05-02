# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import pytest
from testfixtures import compare

from communication.rest_views.filtered_dataset_rest_views import FilteredDatasetRESTView
from communication.rest_views.media_score_rest_views import MediaScoreRESTViews
from tests.fixtures.values import IDOffsets
from tests.unit.mocked_method_helpers import mock_get_image_by_id, mock_get_video_by_id
from usecases.dataset_filter import DatasetFilter
from usecases.query_builder import MediaQueryResult, QueryResults

from geti_fastapi_tools.exceptions import BadRequestException
from geti_types import ID, ImageIdentifier, VideoFrameIdentifier
from iai_core.entities.media_score import NullMediaScore
from iai_core.utils.annotation_scene_state_helper import AnnotationSceneStateHelper


@pytest.fixture
def fxt_test_result_annotation_id():
    yield ID("60d31793d5f1fb7e6415373b")


@pytest.fixture
def fxt_test_result_prediction_id():
    yield ID("60d31793d5f1fb7e6e3c1a59")


@pytest.fixture
def fxt_rest_image_scores(fxt_project, fxt_test_result_annotation_id, fxt_test_result_prediction_id):
    yield {
        "id": "60d31793d5f1fb7e6e3c1ab3",
        "name": "",
        "uploader_id": "",
        "type": "image",
        "annotation_state_per_task": [{"task_id": ID("60d31793d5f1fb7e6e3c1a5b"), "state": "none"}],
        "media_information": {
            "height": 10,
            "width": 10,
            "size": 0,
            "display_url": f"/api/v1/organizations/00000000-0000-0000-0000-000000000001"
            f"/workspaces/{fxt_project.workspace_id}"
            f"/projects/60d31793d5f1fb7e6e3c1a51"
            f"/datasets/60d31793d5f1fb7e6e3c1a52"
            f"/media/images/60d31793d5f1fb7e6e3c1ab3/display/full",
            "extension": ".png",
        },
        "thumbnail": f"/api/v1/organizations/00000000-0000-0000-0000-000000000001/workspaces/{fxt_project.workspace_id}"
        "/projects/60d31793d5f1fb7e6e3c1a51"
        "/datasets/60d31793d5f1fb7e6e3c1a52"
        "/media/images/60d31793d5f1fb7e6e3c1ab3/display/thumb",
        "test_result": {
            "annotation_id": str(fxt_test_result_annotation_id),
            "prediction_id": str(fxt_test_result_prediction_id),
        },
        "annotation_scene_id": None,
        "roi_id": None,
        "last_annotator_id": None,
        "preprocessing": {"status": "FINISHED"},
    }


class TestMediaScoreRESTViews:
    def test_filtered_scores_to_rest_mixed(
        self,
        fxt_organization_id,
        fxt_project,
        fxt_dataset_storage,
        fxt_mongo_id,
        fxt_model_test_result,
        fxt_media_score,
        fxt_test_result_annotation_id,
        fxt_test_result_prediction_id,
        fxt_rest_image_scores,
    ):
        # Arrange
        image_id = fxt_mongo_id(IDOffsets.EMPTY_IMAGE)
        image_identifier = ImageIdentifier(image_id=image_id)
        video_id = fxt_mongo_id(IDOffsets.EMPTY_VIDEO)
        video_frame_identifier_1 = VideoFrameIdentifier(video_id=video_id, frame_index=1)
        video_frame_identifier_2 = VideoFrameIdentifier(video_id=video_id, frame_index=30)
        mock_entities_data = [
            MediaQueryResult(image_identifier, mock_get_image_by_id(image_id)),
            MediaQueryResult(video_frame_identifier_1, mock_get_video_by_id(video_id)),
            MediaQueryResult(video_frame_identifier_2, mock_get_video_by_id(video_id)),
        ]
        query_results = QueryResults(
            media_query_results=mock_entities_data,
            skip=100,
            matching_images_count=100,
            matching_videos_count=100,
            matching_video_frames_count=100,
            total_videos_count=100,
            total_images_count=100,
        )
        mock_anno_states_per_task = AnnotationSceneStateHelper.get_media_per_task_states_from_repo(
            media_identifiers=query_results.media_identifiers,
            dataset_storage_identifier=fxt_dataset_storage.identifier,
            project=fxt_project,
        )
        mock_media_score_per_media_identifier = {
            image_identifier: fxt_media_score,
            video_frame_identifier_1: fxt_media_score,
            video_frame_identifier_2: fxt_media_score,
        }
        mock_annotation_id_per_media_identifier = {
            image_identifier: fxt_test_result_annotation_id,
            video_frame_identifier_1: fxt_test_result_annotation_id,
            video_frame_identifier_2: fxt_test_result_annotation_id,
        }
        mock_prediction_id_per_media_identifier = {
            image_identifier: fxt_test_result_prediction_id,
            video_frame_identifier_1: fxt_test_result_prediction_id,
            video_frame_identifier_2: fxt_test_result_prediction_id,
        }
        dataset_filter = DatasetFilter.from_dict(query={}, limit=3)

        # Act
        results = MediaScoreRESTViews.media_scores_to_rest(
            project=fxt_project,
            model_test_result=fxt_model_test_result,
            query_results=query_results,
            dataset_filter=dataset_filter,
            media_annotation_states_per_task=mock_anno_states_per_task,
            media_score_per_media_identifier=mock_media_score_per_media_identifier,
            annotation_id_per_media_identifier=mock_annotation_id_per_media_identifier,
            prediction_id_per_media_identifier=mock_prediction_id_per_media_identifier,
        )

        # Assert
        scores = [
            {"name": "F-measure", "value": 0.6, "label_id": "60d31793d5f1fb7e6e3c1ab5"},
            {"name": "F-measure", "value": 0.6, "label_id": None},
        ]
        assert "next_page" in results
        for media in results["media"]:
            del media["upload_time"]  # for later comparison
            if media["type"] == "image":
                for score in scores:
                    assert score in media["test_result"]["scores"]
                del media["test_result"]["scores"]
                compare(media, fxt_rest_image_scores, ignore_eq=True)

    def test_invalid_item_type(
        self,
        fxt_organization_id,
        fxt_model_test_result,
        fxt_project,
        fxt_empty_query_results,
        fxt_dataset_filter,
    ) -> None:
        """
        Asserts that an invalid media type raises a bad request exception.
        """
        invalid_rest_views = {"media": [{"type": "invalid"}]}
        with (
            pytest.raises(BadRequestException),
            patch.object(
                FilteredDatasetRESTView,
                "get_rest_media_from_query_results",
                return_value=invalid_rest_views,
            ),
        ):
            MediaScoreRESTViews.media_scores_to_rest(
                project=fxt_project,
                model_test_result=fxt_model_test_result,
                query_results=fxt_empty_query_results,
                dataset_filter=fxt_dataset_filter,
                media_annotation_states_per_task={},
                media_score_per_media_identifier={},
                annotation_id_per_media_identifier={},
                prediction_id_per_media_identifier={},
            )

    def test_no_dataset_get_test_result(self, fxt_broken_model_test_result, fxt_media_identifier, fxt_media_score):
        """
        Tests that an error is raised for a ModelTestResult without a prediction/ground
        truth dataset ID
        """
        expected_error_msg = (
            f"Ground truth and/or prediction dataset not yet set "
            f"for model test result with id '{fxt_broken_model_test_result.id_}'"
        )

        with pytest.raises(ValueError) as error:
            MediaScoreRESTViews._get_test_result_info(
                model_test_result=fxt_broken_model_test_result,
                media_identifier=fxt_media_identifier,
                media_score=fxt_media_score,
                annotation_id=ID("dummy_annotation_id"),
                prediction_id=ID("dummy_prediction_id"),
            )

        assert str(error.value) == expected_error_msg

    def test_no_media_identifier_get_test_result(self, fxt_model_test_result, fxt_media_identifier):
        """
        Tests that an error is raised when no media score is available for the model
        test result/media combination.
        """
        expected_error_msg = (
            f"Media score for media identifier '{fxt_media_identifier}' "
            f"is not found for model test result with id '{fxt_model_test_result.id_}'"
        )

        with pytest.raises(ValueError) as error:
            MediaScoreRESTViews._get_test_result_info(
                model_test_result=fxt_model_test_result,
                media_identifier=fxt_media_identifier,
                media_score=NullMediaScore(),
                annotation_id=ID("dummy_annotation_id"),
                prediction_id=ID("dummy_prediction_id"),
            )

        assert str(error.value) == expected_error_msg

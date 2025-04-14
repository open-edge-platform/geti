# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json
from http import HTTPStatus
from unittest.mock import patch

from testfixtures import compare

from communication.controllers.prediction_controller import PredictionController
from entities import PredictionType

from geti_types import ID, ImageIdentifier, VideoFrameIdentifier

DUMMY_ORGANIZATION_ID = "6682a33b-3d18-4dab-abee-f797090480e0"
DUMMY_WORKSPACE_ID = "567890123456789012340000"
DUMMY_PROJECT_ID = "234567890123456789010000"
DUMMY_DATASET_ID = "184377438465364732664000"
DUMMY_IMAGE_ID = "624738256723562375620000"
DUMMY_VIDEO_ID = "835463642801460237560000"
DUMMY_FRAME_INDEX = "123"
DUMMY_PREDICTION_TYPE = "latest"
DUMMY_DATA = {"dummy_key": "dummy_value"}

API_ORGANIZATION_PATTERN = f"/api/v1/organizations/{DUMMY_ORGANIZATION_ID}"
API_WORKSPACE_PATTERN = f"{API_ORGANIZATION_PATTERN}/workspaces/{DUMMY_WORKSPACE_ID}"
API_PROJECT_PATTERN = f"{API_WORKSPACE_PATTERN}/projects/{DUMMY_PROJECT_ID}"
API_DATASET_PATTERN = f"{API_PROJECT_PATTERN}/datasets/{DUMMY_DATASET_ID}"
API_IMAGE_PATTERN = f"{API_DATASET_PATTERN}/media/images"
API_VIDEO_PATTERN = f"{API_DATASET_PATTERN}/media/videos"
API_IMAGE_PREDICTION_PATTERN = f"{API_IMAGE_PATTERN}/{DUMMY_IMAGE_ID}/predictions/{DUMMY_PREDICTION_TYPE}"
API_VIDEO_PREDICTION_PATTERN = f"{API_VIDEO_PATTERN}/{DUMMY_VIDEO_ID}/predictions/{DUMMY_PREDICTION_TYPE}"
API_VIDEO_FRAME_PREDICTION_PATTERN = (
    f"{API_VIDEO_PATTERN}/{DUMMY_VIDEO_ID}/frames/{DUMMY_FRAME_INDEX}/predictions/{DUMMY_PREDICTION_TYPE}"
)

DUMMY_USER = ID("dummy_user")


class TestPredictionRESTEndpoint:
    def test_image_prediction_endpoint(self, fxt_director_app) -> None:
        media_identifier = ImageIdentifier(ID(DUMMY_IMAGE_ID))

        with patch.object(
            PredictionController,
            "get_prediction",
            return_value=DUMMY_DATA,
        ) as mock_get_prediction:
            result = fxt_director_app.get(API_IMAGE_PREDICTION_PATTERN)

        mock_get_prediction.assert_called_once_with(
            project_id=ID(DUMMY_PROJECT_ID),
            dataset_storage_id=ID(DUMMY_DATASET_ID),
            media_identifier=media_identifier,
            prediction_id=None,
            prediction_type=PredictionType.LATEST,
            task_id=None,
            model_id=None,
            label_only=False,
            for_inf_gateway=False,
        )
        assert result.status_code == HTTPStatus.OK
        compare(json.loads(result.content), DUMMY_DATA, ignore_eq=True)

    def test_image_prediction_endpoint_with_model_id(self, fxt_director_app, fxt_mongo_id) -> None:
        media_identifier = ImageIdentifier(ID(DUMMY_IMAGE_ID))
        model_id = fxt_mongo_id(3)

        with patch.object(
            PredictionController,
            "get_prediction",
            return_value=DUMMY_DATA,
        ) as mock_get_prediction:
            result = fxt_director_app.get(f"{API_IMAGE_PREDICTION_PATTERN}?model_id={model_id}")

        mock_get_prediction.assert_called_once_with(
            project_id=ID(DUMMY_PROJECT_ID),
            dataset_storage_id=ID(DUMMY_DATASET_ID),
            media_identifier=media_identifier,
            prediction_id=None,
            prediction_type=PredictionType.LATEST,
            task_id=None,
            model_id=ID(model_id),
            label_only=False,
            for_inf_gateway=False,
        )
        assert result.status_code == HTTPStatus.OK
        compare(json.loads(result.content), DUMMY_DATA, ignore_eq=True)

    def test_video_frame_prediction_endpoint(self, fxt_director_app) -> None:
        media_identifier = VideoFrameIdentifier(video_id=ID(DUMMY_VIDEO_ID), frame_index=int(DUMMY_FRAME_INDEX))
        endpoint = API_VIDEO_FRAME_PREDICTION_PATTERN

        with patch.object(
            PredictionController,
            "get_prediction",
            return_value=DUMMY_DATA,
        ) as mock_get_prediction:
            result = fxt_director_app.get(endpoint)

        mock_get_prediction.assert_called_once_with(
            project_id=ID(DUMMY_PROJECT_ID),
            dataset_storage_id=ID(DUMMY_DATASET_ID),
            media_identifier=media_identifier,
            prediction_id=None,
            prediction_type=PredictionType.LATEST,
            task_id=None,
            model_id=None,
            label_only=False,
            for_inf_gateway=False,
        )
        assert result.status_code == HTTPStatus.OK
        compare(json.loads(result.content), DUMMY_DATA, ignore_eq=True)

    def test_prediction_endpoint_invalid_arg(self, fxt_director_app) -> None:
        for api_pattern in [API_VIDEO_PREDICTION_PATTERN, API_IMAGE_PREDICTION_PATTERN]:
            endpoint = f"{api_pattern}?label_only=not_valid_arg"
            result = fxt_director_app.get(endpoint)

            assert result.status_code == HTTPStatus.BAD_REQUEST

    def test_video_prediction_endpoint(self, fxt_director_app) -> None:
        start_frame = 1
        end_frame = 100
        frameskip = 2
        endpoint = (
            f"{API_VIDEO_PREDICTION_PATTERN}?start_frame={start_frame}&end_frame={end_frame}&frameskip={frameskip}"
        )

        with patch.object(
            PredictionController,
            "get_video_predictions",
            return_value=DUMMY_DATA,
        ) as mock_get_prediction:
            result = fxt_director_app.get(endpoint)

        mock_get_prediction.assert_called_once_with(
            organization_id=DUMMY_ORGANIZATION_ID,
            project_id=ID(DUMMY_PROJECT_ID),
            dataset_id=ID(DUMMY_DATASET_ID),
            video_id=ID(DUMMY_VIDEO_ID),
            prediction_type=PredictionType.LATEST,
            task_id=None,
            model_id=None,
            label_only=False,
            start_frame=start_frame,
            end_frame=end_frame,
            frameskip=frameskip,
        )
        assert result.status_code == HTTPStatus.OK
        compare(json.loads(result.content), DUMMY_DATA, ignore_eq=True)

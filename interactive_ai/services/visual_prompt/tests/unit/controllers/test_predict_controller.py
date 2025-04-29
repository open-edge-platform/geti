# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from freezegun import freeze_time

from entities.exceptions import InferenceMediaNotFound, MissingInputMediaException
from services.controllers.predict_controller import PredictController
from services.models.media_info_payload import MediaInfoPayload
from services.visual_prompt_service import VPSPredictionResults

from geti_types import DatasetStorageIdentifier, ImageIdentifier
from sc_sdk.utils.time_utils import now


def return_none(*args, **kwargs) -> None:
    return None


class TestPredictController:
    @freeze_time("2024-01-01 00:00:01")
    def test_predict(self, fxt_project_identifier, fxt_ote_id, fxt_image):
        # Arrange
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_project_identifier.workspace_id,
            project_id=fxt_project_identifier.project_id,
            dataset_storage_id=fxt_ote_id(1000),
        )
        media_info = MediaInfoPayload(
            dataset_storage_id=dataset_storage_identifier.dataset_storage_id,
            image_id="dummy_media_id",
        )
        prediction_results = VPSPredictionResults(bboxes=[], rotated_bboxes=[], polygons=[])
        mock_request = MagicMock()
        mock_request.app.visual_prompt_service.infer.return_value = prediction_results
        task_id = fxt_ote_id(2000)
        expected_rest = {
            "predictions": [],
            "created": now().isoformat(),
            "media_identifier": {"image_id": fxt_image.id_, "type": "image"},
        }
        image_numpy = np.zeros(shape=(100, 100, 3))

        # Act
        with patch.object(
            PredictController, "_get_media", return_value=[image_numpy, ImageIdentifier(fxt_image.id_)]
        ) as mock_get_media:
            rest = PredictController.predict(
                request=mock_request,
                project_identifier=fxt_project_identifier,
                task_id=task_id,
                media_info_payload=media_info,
            )

        # Assert
        mock_get_media.assert_called_once_with(
            dataset_storage_identifier=dataset_storage_identifier,
            media_info_payload=media_info,
        )
        mock_request.app.visual_prompt_service.infer.assert_called_once_with(
            project_identifier=fxt_project_identifier,
            task_id=task_id,
            media=image_numpy,
        )
        assert rest == expected_rest

    def test_predict_invalid_input_media(self, fxt_project_identifier, fxt_ote_id):
        # Arrange
        mock_request = MagicMock()
        task_id = fxt_ote_id(2000)

        # Act & Assert
        with pytest.raises(MissingInputMediaException):
            PredictController.predict(
                request=mock_request,
                project_identifier=fxt_project_identifier,
                task_id=task_id,
                media_info_payload=None,
                file=None,
            )

    @pytest.mark.parametrize(
        "media_info_payload",
        (
            # missing media_id
            MediaInfoPayload(dataset_storage_id="dummy_dataset_id"),
            # missing video_id
            MediaInfoPayload(dataset_storage_id="dummy_dataset_id", frame_index=1),
            # missing frame_index
            MediaInfoPayload(dataset_storage_id="dummy_dataset_id", video_id="dummy_media_id"),
        ),
    )
    def test_predict_media_not_found(self, media_info_payload, fxt_project_identifier, fxt_ote_id):
        mock_request = MagicMock()
        with pytest.raises(InferenceMediaNotFound):
            PredictController.predict(
                request=mock_request,
                project_identifier=fxt_project_identifier,
                task_id=fxt_ote_id(1),
                media_info_payload=media_info_payload,
            )

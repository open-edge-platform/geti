# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os
from http import HTTPStatus
from unittest.mock import ANY, patch

import pytest

from services.controllers.predict_controller import PredictController
from services.models.media_info_payload import MediaInfoPayload


class TestPredictEndpoints:
    def test_prompt_media_info(self, fxt_test_app, fxt_project_identifier, fxt_session_ctx, fxt_ote_id) -> None:
        # Arrange
        task_id = fxt_ote_id(1)
        endpoint = (
            f"/api/v1/organizations/{fxt_session_ctx.organization_id}/workspaces/{fxt_session_ctx.workspace_id}"
            f"/projects/{fxt_project_identifier.project_id}/pipelines/{task_id}:prompt"
        )
        dummy_predict_rest: dict = {"predictions": []}
        media_info_payload = MediaInfoPayload(
            dataset_storage_id="dummy_dataset_id",
            image_id="dummy_image_id",
        )
        json_payload = {
            "dataset_id": media_info_payload.dataset_storage_id,
            "image_id": media_info_payload.image_id,
        }

        # Act
        with patch.object(PredictController, "predict", return_value=dummy_predict_rest) as mock_predict:
            result = fxt_test_app.post(endpoint, json=json_payload)

        # Assert
        mock_predict.assert_called_once_with(
            request=ANY,
            project_identifier=fxt_project_identifier,
            task_id=task_id,
            media_info_payload=media_info_payload,
            file=None,
        )
        assert result.status_code == HTTPStatus.OK

    def test_prompt_binary_file(self, fxt_test_app, fxt_project_identifier, fxt_session_ctx, fxt_ote_id) -> None:
        # Arrange
        task_id = fxt_ote_id(1)
        endpoint = (
            f"/api/v1/organizations/{fxt_session_ctx.organization_id}/workspaces/{fxt_session_ctx.workspace_id}"
            f"/projects/{fxt_project_identifier.project_id}/pipelines/{task_id}:prompt"
        )
        dummy_predict_rest: dict = {"predictions": []}
        image_file = os.path.dirname(__file__) + "/../../../data/crate.png"

        # Act
        with (
            patch.object(PredictController, "predict", return_value=dummy_predict_rest) as mock_predict,
            open(image_file, "rb") as f,
        ):
            result = fxt_test_app.post(endpoint, files={"file": ("crate.png", f, "image/png")})

            # Assert
            mock_predict.assert_called_once_with(
                request=ANY,
                project_identifier=fxt_project_identifier,
                task_id=task_id,
                media_info_payload=None,
                file=ANY,
            )
        assert result.status_code == HTTPStatus.OK

    @pytest.mark.parametrize(
        "payload",
        (
            {"dataset_id": "dummy_dataset_id"},
            {"image_id": "dummy_image_id"},
            {"dataset_id": "dummy_dataset_id", "video_id": "dummy_video_id"},
            {"dataset_id": "dummy_dataset_id", "video_frame": 1},
        ),
    )
    def test_prompt_missing_fields(
        self, payload, fxt_test_app, fxt_project_identifier, fxt_session_ctx, fxt_ote_id
    ) -> None:
        # Arrange
        task_id = fxt_ote_id(1)
        endpoint = (
            f"/api/v1/organizations/{fxt_session_ctx.organization_id}/workspaces/{fxt_session_ctx.workspace_id}"
            f"/projects/{fxt_project_identifier.project_id}/pipelines/{task_id}:prompt"
        )

        # Act & Assert
        with pytest.raises(ValueError):
            fxt_test_app.post(endpoint, json=payload)

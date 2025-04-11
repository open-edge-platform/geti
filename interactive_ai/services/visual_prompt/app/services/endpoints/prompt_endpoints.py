# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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

"""Endpoints related to visual prompting predict"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, UploadFile
from starlette import status
from starlette.responses import JSONResponse, Response

from services.controllers.predict_controller import PredictController
from services.models.media_info_payload import MediaInfoPayload
from services.rest_data_validator.media_rest_validator import MediaRestValidator
from utils.feature_flag import FeatureFlag

from geti_fastapi_tools.dependencies import get_project_identifier, setup_session_fastapi
from geti_feature_tools import FeatureFlagProvider
from geti_types import ID, ProjectIdentifier

router = APIRouter(
    prefix="/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}/pipelines",
    dependencies=[Depends(setup_session_fastapi)],
)


@router.post("/{task_id}:prompt", status_code=status.HTTP_200_OK)
def prompt_endpoint(
    request: Request,
    project_identifier: Annotated[ProjectIdentifier, Depends(get_project_identifier)],
    task_id: str,
    file: UploadFile = Depends(MediaRestValidator.validate_image_file),  # noqa: FAST002
    media_info_payload: MediaInfoPayload | None = Depends(MediaRestValidator.validate_media_info_payload),  # noqa: FAST002
) -> Response:
    """Endpoint to get predictions from the visual prompting model."""
    if not FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_VISUAL_PROMPT_SERVICE):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"message": "Visual Prompt Service is not enabled."},
        )

    predictions_rest = PredictController.predict(
        request=request,
        project_identifier=project_identifier,
        task_id=ID(task_id),
        media_info_payload=media_info_payload,
        file=file,
    )
    return JSONResponse(predictions_rest)

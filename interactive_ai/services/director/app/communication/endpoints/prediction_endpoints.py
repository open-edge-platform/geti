# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

"""
Endpoints to get predictions on media
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Query
from starlette.responses import JSONResponse

from communication.controllers.prediction_controller import PredictionController
from communication.exceptions import DeprecatedMethodException
from entities import PredictionType

from geti_fastapi_tools.dependencies import (
    get_dataset_id,
    get_image_id,
    get_optional_model_id,
    get_optional_task_id,
    get_organization_id,
    get_project_id,
    get_video_id,
    setup_session_fastapi,
)
from geti_types import ID, ImageIdentifier, MediaIdentifierEntity, VideoFrameIdentifier

logger = logging.getLogger(__name__)

prediction_api_prefix_url = (
    "/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/projects/{project_id}/datasets/{dataset_id}"
)

prediction_router = APIRouter(
    prefix=prediction_api_prefix_url,
    tags=["Prediction"],
    dependencies=[Depends(setup_session_fastapi)],
)


@prediction_router.get("/media/images/{image_id}/predictions/{prediction_type_or_id}")
def image_prediction_endpoint(  # noqa: PLR0913
    project_id: Annotated[ID, Depends(get_project_id)],
    dataset_id: Annotated[ID, Depends(get_dataset_id)],
    image_id: Annotated[ID, Depends(get_image_id)],
    prediction_type_or_id: str,
    task_id: Annotated[ID, Depends(get_optional_task_id)],
    model_id: Annotated[ID, Depends(get_optional_model_id)],
    label_only: Annotated[bool, Query()] = False,
    inf_gateway: Annotated[bool, Query()] = False,
) -> dict[str, Any]:
    """
    Endpoint to get a prediction on an image.

    :param organization_id: ID of the organization
    :param workspace_id: ID of the workspace the project belongs to
    :param project_id: ID of the project the image belongs to
    :param dataset_id: ID of the dataset the image belongs to
    :param image_id: ID of the image to generate a prediction for
    :param prediction_type_or_id: ID of prediction or latest, auto, or online.
        - latest: pull the latest one in the database
        - auto: send an inference request if there is no prediction in the database
        - online: always sends an inference request
    :return: REST response and return code
    :raises BadRequestException if query parameter label_only can't be parsed to a boolean
    """
    return _get_media_prediction(
        project_id=project_id,
        dataset_id=dataset_id,
        media_identifier=ImageIdentifier(image_id=image_id),
        prediction_type_or_id=prediction_type_or_id,
        task_id=task_id,
        model_id=model_id,
        label_only=label_only,
        inf_gateway=inf_gateway,
    )


@prediction_router.get("/media/videos/{video_id}/frames/{frame_index}/predictions/{prediction_type_or_id}")
def video_frame_prediction_endpoint(  # noqa: PLR0913
    project_id: Annotated[ID, Depends(get_project_id)],
    dataset_id: Annotated[ID, Depends(get_dataset_id)],
    video_id: Annotated[ID, Depends(get_video_id)],
    frame_index: Annotated[int, Path(ge=0)],
    prediction_type_or_id: str,
    task_id: Annotated[ID, Depends(get_optional_task_id)],
    model_id: Annotated[ID, Depends(get_optional_model_id)],
    label_only: Annotated[bool, Query()] = False,
    inf_gateway: Annotated[bool, Query()] = False,
) -> JSONResponse:
    """
    Endpoint to get a prediction on a video frame.

    :param organization_id: ID of the organization
    :param workspace_id: ID of the workspace the project belongs to
    :param project_id: ID of the project the image belongs to
    :param video_id: ID of the video containing the frame to generate a prediction for
    :param frame_index: Index of the frame to generate a prediction for
    :param dataset_id:
    :param prediction_type_or_id: ID of prediction or latest, auto, or online.
        - latest: pull the latest one in the database
        - auto: send an inference request if there is no prediction in the database
        - online: always sends an inference request
    :return: REST response and return code
    :raises BadRequestException if query parameter label_only can't be parsed to a boolean
    """
    return JSONResponse(
        _get_media_prediction(
            project_id=ID(project_id),
            dataset_id=ID(dataset_id),
            media_identifier=VideoFrameIdentifier(video_id=ID(video_id), frame_index=frame_index),
            prediction_type_or_id=prediction_type_or_id,
            task_id=task_id,
            model_id=model_id,
            label_only=label_only,
            inf_gateway=inf_gateway,
        )
    )


@prediction_router.get("/media/videos/{video_id}/predictions/{prediction_type}")
def video_prediction_endpoint(  # noqa: PLR0913
    organization_id: Annotated[ID, Depends(get_organization_id)],
    project_id: Annotated[ID, Depends(get_project_id)],
    dataset_id: Annotated[ID, Depends(get_dataset_id)],
    video_id: Annotated[ID, Depends(get_video_id)],
    task_id: Annotated[ID, Depends(get_optional_task_id)],
    model_id: Annotated[ID, Depends(get_optional_model_id)],
    prediction_type: str,
    start_frame: Annotated[int | None, Query(ge=0)] = None,
    end_frame: Annotated[int | None, Query(ge=0)] = None,
    frameskip: Annotated[int | None, Query(ge=1)] = None,
    label_only: Annotated[bool, Query()] = False,
) -> JSONResponse:
    """
    Endpoint to get predictions on frames of a video. Can pass parameters such as
    start/end frame and frame skip to only get predictions for a specific range of frames

    :param organization_id: ID of the organization
    :param project_id: ID of the project the image belongs to
    :param video_id: ID of the video to generate predictions for
    :param dataset_id:
    :param prediction_type: latest, auto, or online.
        - latest: pull the latest one in the database
        - auto: send an inference request if there is no prediction in the database
        - online: always sends an inference request
    :return: REST response and return code
    :raises BadRequestException if query parameter label_only can't be parsed to a boolean
    """
    if prediction_type != "latest":
        raise DeprecatedMethodException(
            f"Unsupported prediction type `{prediction_type}`. Only `latest` is supported by "
            f"this endpoint, for other modes please use the prediction endpoints in the inference "
            f"gateway."
        )  # type: ignore

    prediction_type_ = PredictionType[prediction_type.upper()]

    return JSONResponse(
        PredictionController.get_video_predictions(
            organization_id=organization_id,
            project_id=project_id,
            dataset_id=dataset_id,
            video_id=video_id,
            prediction_type=prediction_type_,
            task_id=task_id,
            model_id=model_id,
            label_only=label_only,
            start_frame=start_frame,
            end_frame=end_frame,
            frameskip=frameskip,
        )
    )


def _get_media_prediction(  # noqa: PLR0913
    project_id: ID,
    dataset_id: ID,
    media_identifier: MediaIdentifierEntity,
    prediction_type_or_id: str,
    model_id: ID | None,
    task_id: ID | None,
    inf_gateway: bool,
    label_only: bool,
) -> dict[str, Any]:
    prediction_type: PredictionType | None = None
    prediction_id: ID | None = None

    if prediction_type_or_id != "latest":
        raise DeprecatedMethodException(
            f"Unsupported prediction type `{prediction_type_or_id}`. Only `latest` is supported by "
            f"this endpoint, for other modes please use the prediction endpoints in the inference "
            f"gateway."
        )  # type: ignore
    try:
        prediction_type = PredictionType[prediction_type_or_id.upper()]
    except KeyError:
        # If prediction_type_or_id is not a PredictionType (latest, online or auto),
        # assume it is an ID.
        prediction_id = ID(prediction_type_or_id)

    return PredictionController.get_prediction(
        project_id=project_id,
        dataset_storage_id=dataset_id,
        media_identifier=media_identifier,
        prediction_id=prediction_id,
        prediction_type=prediction_type,
        task_id=task_id,
        model_id=model_id,
        label_only=label_only,
        for_inf_gateway=inf_gateway,
    )

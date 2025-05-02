# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements the export endpoints
"""

import logging
import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from geti_feature_tools.feature_flags import FeatureFlagProvider
from starlette.responses import FileResponse, JSONResponse, RedirectResponse, Response

from application.export_management import DatasetExportOperationConfig, ExportManager
from communication.helpers.http_exceptions import (
    BadRequestGetiBaseException,
    FileNotFoundGetiBaseException,
    InternalServerErrorGetiBaseException,
    NotEnoughSpaceGetiBaseException,
    NotImplementedGetiBaseException,
)
from communication.helpers.import_utils import ImportUtils
from communication.helpers.validation_helpers import (
    get_validated_dataset_storage,
    get_validated_mongo_id,
    get_validated_project,
)
from domain.entities.dataset_ie_file_metadata import ExportFormat
from features.feature_flags import FeatureFlag

from geti_fastapi_tools.dependencies import get_user_id_fastapi, setup_session_fastapi
from geti_fastapi_tools.exceptions import GetiBaseException
from geti_types import ID
from iai_core_py.entities.model_template import TaskType
from iai_core_py.repos import ProjectRepo
from iai_core_py.utils.filesystem import check_free_space_for_operation
from iai_core_py.utils.naming_helpers import slugify

api_version = "v1"
api_prefix_url = f"/api/{api_version}"
router = APIRouter(
    prefix=api_prefix_url + "/organizations/{organization_id}/workspaces/{workspace_id}",
    dependencies=[Depends(setup_session_fastapi)],
)
logger = logging.getLogger(__name__)


@router.post("/projects/{project_id}/datasets/{dataset_id}:prepare-for-export")
def prepare_dataset_endpoint(
    user_id: Annotated[ID, Depends(get_user_id_fastapi)],
    project_id: str,
    dataset_id: str,
    export_format: str,
    include_unannotated_media: bool = True,
    save_video_as_images: bool = True,
) -> Response:
    """
    Triggers the export of a dataset storage with include_unannotated_media to a dataset
    of the given format, and returns the url that can be used to monitor the status of
    the export operation

    :param request: The request object used to get user information
    :param project_id: ID of the project containing the dataset
    :param dataset_id: ID of the dataset storage
    :param export_format: The format to export the dataset to, should be in [voc, coco, yolo, datumaro]
    :param include_unannotated_media: If True, unannotated media are also exported
    :param save_video_as_images: Whether to export video as frame images or not.
        For formats that don't natively support videos (all except Datumaro),
        this parameter is implicitly overridden to true.
    :return: Job ID to process the request.
    """
    logger.info(
        f"Handling post `prepare_dataset_endpoint`: project_id={project_id}, "
        f"dataset_id={dataset_id}, export_format={export_format}, "
        f"include_unannotated_media={include_unannotated_media}, "
        f"save_video_as_images={save_video_as_images}"
    )

    try:
        fmt: ExportFormat = ExportFormat(export_format)
    except ValueError:
        error_msg = f"Export format not supported. Supported formats are {str([e.value for e in ExportFormat])}"
        logger.warning(error_msg)
        raise BadRequestGetiBaseException(error_msg)

    if fmt != ExportFormat.DATUMARO:
        save_video_as_images = True

    try:
        check_free_space_for_operation(operation="Project export", exception_type=NotEnoughSpaceGetiBaseException)

        project = get_validated_project(project_id=project_id)
        if (
            project.get_project_type().lower() == TaskType.KEYPOINT_DETECTION.name.lower()
            and not FeatureFlagProvider.is_enabled(feature_flag=FeatureFlag.FEATURE_FLAG_KEYPOINT_DETECTION_DATASET_IE)
        ):
            raise NotImplementedGetiBaseException("Exporting datasets from keypoint detection tasks is not supported")

        dataset_storage = get_validated_dataset_storage(identifier=project.identifier, dataset_storage_id=dataset_id)
        job_metadata = {
            "project": {
                "id": project_id,
                "name": project.name,
                "type": ImportUtils.project_type_to_rest_api_string(ImportUtils.get_project_type(project)),
            },
            "dataset": {
                "id": dataset_id,
                "name": dataset_storage.name,
            },
            "export_format": export_format,
        }

        logger.info("Feature flag for dataset ie jobs is enabled, submitting export dataset job")
        job_id = ExportManager().submit_export_job(
            project_id=ID(project_id),
            dataset_storage_id=ID(dataset_id),
            export_config=DatasetExportOperationConfig(
                export_format=fmt,
                include_unannotated=include_unannotated_media,
                save_video_as_images=save_video_as_images,
            ),
            author=user_id,
            metadata=job_metadata,
        )
    except GetiBaseException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Exception raised while submitting export_dataset job: {str(e)}")
        raise InternalServerErrorGetiBaseException("Unknown error faced during dataset exporting")

    logger.info(f"Submitted export dataset job with id {job_id}")
    return JSONResponse({"job_id": job_id})


@router.get("/projects/{project_id}/datasets/{dataset_id}/exports/{export_dataset_id}/download", response_model=None)
def download_dataset_endpoint(
    request: Request,
    project_id: str,
    dataset_id: str,
    export_dataset_id: str,
) -> FileResponse | RedirectResponse:
    """
    Downloads a zipped dataset with given id

    :param project_id: ID of the project containing the dataset
    :param dataset_id: ID of dataset storage under export
    :param export_dataset_id: ID of export dataset
    :param file_manager: FileFSManager object used for file management
    :param export_manager: ExportManager object used for file management
    :return: data of zipped dataset
    """
    logger.info(
        f"Handling get `download_dataset_endpoint`: project_id={project_id}, "
        f"dataset_id={dataset_id}, export_dataset_id={export_dataset_id}"
    )
    try:
        project = get_validated_project(project_id=project_id)
        _ = get_validated_dataset_storage(identifier=project.identifier, dataset_storage_id=dataset_id)
        file_id = get_validated_mongo_id(id=export_dataset_id, id_name="export_dataset_id")

        # In case of enabled feature flag, return a presigned URL to the user
        filename = get_download_file_name(dataset_storage_id=ID(dataset_id))

        internal_presigned_url = ExportManager().get_exported_dataset_presigned_url(file_id=file_id, filename=filename)

        # Create the base URL for the exposed S3 address
        request_base_ip = str(request.base_url).replace("http://", "").replace("https://", "").replace("/", "")
        s3_external_address = request_base_ip + "/api/v1/fileservice"
        # Create the URL to redirect the user to
        s3_internal_address = os.environ.get("S3_HOST", "impt-seaweed-fs:8333")
        external_presigned_url = internal_presigned_url.replace(s3_internal_address, s3_external_address)
        external_presigned_url = external_presigned_url.replace("http://", "https://")
    except GetiBaseException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)
    except HTTPException:
        raise
    except FileNotFoundError:
        message = f"The requested export dataset could not be found. Export Dataset ID: `{export_dataset_id}`."
        logger.warning(message)
        raise FileNotFoundGetiBaseException(message=message)
    except Exception as e:
        logger.exception(f"Exception raised while generating download url: {str(e)}")
        raise InternalServerErrorGetiBaseException("Unknown error faced during dataset downloading")

    headers = {
        "Content-Type": "application/zip",
        "Accept-Ranges": "bytes",  # Enable byte range support
    }
    return RedirectResponse(url=external_presigned_url, headers=headers)


def get_download_file_name(dataset_storage_id: ID, export_format: ExportFormat | None = None) -> str:
    """
    Return file name for export dataset

    :param dataset_storage_id: dataset storage id
    :param export_format: ExportFormat of the dataset
    :return: user-exposed name of the dataset
    """
    project = ProjectRepo().get_by_dataset_storage_id(dataset_storage_id)
    project_name = slugify(project.name)
    if export_format is None:
        return f"{project_name}-dataset.zip"
    return f"{project_name}-dataset-{export_format.name}.zip"

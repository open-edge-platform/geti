# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements the upload endpoints
"""

import logging
import os

from fastapi import APIRouter, Body, Depends, File, Header, HTTPException, Request, Response, status
from starlette.responses import JSONResponse

from application.file_object_management import FileObjectManager
from communication.helpers.http_exceptions import (
    CouldNotUploadZeroBytesException,
    InternalServerErrorGetiBaseException,
    NotEnoughSpaceGetiBaseException,
    PayloadTooLargeGetiBaseException,
)
from communication.helpers.validation_helpers import get_validated_mongo_id

from geti_fastapi_tools.dependencies import setup_session_fastapi
from geti_fastapi_tools.exceptions import GetiBaseException
from iai_core_py.utils.filesystem import MIN_FREE_SPACE_GIB, check_free_space_for_upload

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/organizations/{organization_id}/workspaces/{workspace_id}/datasets/uploads",
    dependencies=[Depends(setup_session_fastapi)],
)
TUS_VERSION = "1.0.0,"  # comma-separated list of version of TUS supported by the client
MAX_IMPORTABLE_DATASET_SIZE = int(os.environ.get("MAX_IMPORTABLE_DATASET_SIZE_GB", "200")) * 2**30
MAX_NUM_FILES_ZIPPED_ARCHIVE = int(os.environ.get("MAX_NUM_FILES_ZIPPED_ARCHIVE", f"{10**7}"))
UNZIP_BUFFER_SIZE_BYTES = int(os.environ.get("UNZIP_BUFFER_SIZE_BYTES", "512"))


@router.post("")
def upload_file(
    file: bytes = File(...),  # noqa: FAST002
) -> Response:
    """
    Simple file upload endpoint, saves uploaded bytes to file in the filesystem.

    :param file: data to upload
    :return: id of the uploaded file
    """
    logger.info("Handling post `upload_file`")
    try:
        size = len(file)
        if size == 0:
            raise CouldNotUploadZeroBytesException
        check_free_space_for_upload(
            upload_size=size,
            exception_type=NotEnoughSpaceGetiBaseException,
            min_free_space_after_upload_gib=(  # add extra margin space to extract the zip
                MIN_FREE_SPACE_GIB + 2 * (size / 2**30)
            ),
        )
        if size > MAX_IMPORTABLE_DATASET_SIZE:
            raise PayloadTooLargeGetiBaseException(size)
        import_id = FileObjectManager().save_file(file)
    except GetiBaseException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Exception raised while uploading a file: {str(e)}")
        raise InternalServerErrorGetiBaseException("Unknown error faced during dataset uploading")

    logger.info("Successfully uploaded file with id %s", str(import_id))
    return JSONResponse({"file_id": str(import_id)})


# TUS Protocol as defined in https://tus.io/protocols/resumable-upload.html


@router.options("/resumable")
def tus_options() -> Response:
    """
    TUS options endpoint
    Defines the version(s) and extension(s) of TUS supported by the server.

    :return: headers describing the TUS protocol implemented by the server
    """
    logger.info("Handling options `tus_options`")
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.headers.update({"Tus-Resumable": "1.0.0", "Tus-Version": "1.0.0", "Tus-Extension": "creation"})
    return response


@router.post("/resumable")
def create_tus_upload(
    request: Request,
    tus_resumable: str = Header(None),  # noqa: FAST002
    upload_length: int = Header(None),  # noqa: FAST002
) -> Response:
    """
    TUS post endpoint
    Implements the creation extension of TUS. Creates a file for upload and saves the total
    size of the file. Returns response with the url for uploading data to the file.

    :param request: request object, used to get request url
    :param tus_resumable: version of TUS used by the client
    :param upload_length: size in bytes of the file to be created
    :param file_manager: FileFSManager object used for file management
    :return: id of the file created in the server
    """
    logger.info(f"Handling post `create_tus_upload`: tus_resumable={tus_resumable}, upload_length={upload_length}")
    try:
        if upload_length == 0:
            raise CouldNotUploadZeroBytesException
        validate_tus(tus_resumable)
        check_free_space_for_upload(
            upload_size=upload_length,
            exception_type=NotEnoughSpaceGetiBaseException,
            min_free_space_after_upload_gib=(  # add extra margin space to extract the zip
                MIN_FREE_SPACE_GIB + 2 * (upload_length / 2**30)
            ),
        )
        if upload_length > MAX_IMPORTABLE_DATASET_SIZE:
            raise PayloadTooLargeGetiBaseException(upload_length)

        id_ = FileObjectManager().create_file(upload_length)

        # location is url of incoming request with https scheme and the addition of file id
        location = f"{request.url.replace(scheme='https')}/{id_}"
        response = Response(
            headers={"Location": location},
            status_code=status.HTTP_201_CREATED,
        )
    except GetiBaseException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Exception raised while creating tus_upload: {str(e)}")
        raise InternalServerErrorGetiBaseException("Unknown error faced during starting resumable upload")

    logger.info("TUS upload created for file with id %s", str(id_))
    return response


@router.head("/resumable/{file_id}")
def tus_upload_head(
    file_id: str,
    tus_resumable: str = Header(None),  # noqa: FAST002
) -> Response:
    """
    TUS head endpoint
    Returns info about file in the server, the total size of the file and the number of
    bytes already written to the file.

    :param file_id: id of file already created in the server
    :param tus_resumable: client's version of TUS
    :param file_manager: FileFSManager object used for file management
    :return: upload length and offset of the file in server
    """
    logger.info(f"Handling head `tus_upload_head`: file_id={file_id}, tus_resumable={tus_resumable}")
    try:
        file_id = get_validated_mongo_id(id=file_id)

        validate_tus(tus_resumable)

        file_metadata = FileObjectManager().get_file_metadata(file_id)

        size, offset = str(file_metadata.size), str(file_metadata.offset)
        response = Response(
            headers={
                "Upload-Length": str(file_metadata.size),
                "Upload-Offset": str(file_metadata.offset),
                "Cache-Content": "no-store",
            },
            status_code=status.HTTP_200_OK,
        )
    except GetiBaseException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Exception raised in tus_upload_head: {str(e)}")
        raise InternalServerErrorGetiBaseException("Unknown error faced while retrieving uploaded file information")

    logger.info(
        "TUS head request for file with id %s. Size: %s; Offset: %s",
        str(file_id),
        size,
        offset,
    )
    return response


@router.patch("/resumable/{file_id}")
def tus_upload_patch(
    file_id: str,
    data: bytes = Body(None),  # noqa: FAST002
    tus_resumable: str = Header(None),  # noqa: FAST002
    content_type: str = Header(None),  # noqa: FAST002
    upload_offset: int = Header(None),  # noqa: FAST002
) -> Response:
    """
    TUS patch endpoint
    Appends data to a file in the server starting from offset.

    :param file_id: if of file already created in the server
    :param data: data to append to the file
    :param tus_resumable: version of TUS used by the client
    :param content_type: content type of the request
    :param upload_offset: number of bytes already uploaded to the file
    :param file_manager: FileFSManager object used for file management
    :return: new offset after the data is appended
    """
    logger.info(
        f"Handling patch `tus_upload_patch`: file_id={file_id}, tus_resumable={tus_resumable}, "
        f"content_type={content_type}, upload_offset={upload_offset}"
    )
    try:
        file_id = get_validated_mongo_id(id=file_id)
        if data is None or len(data) == 0:
            raise CouldNotUploadZeroBytesException

        validate_tus(tus_resumable)

        if content_type != "application/offset+octet-stream":
            message = f"Unsupported media type received '{content_type}', expected 'application/offset+octet-stream'"
            logger.error(message)
            raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=message)

        file_metadata = FileObjectManager().get_file_metadata(file_id)

        if file_metadata.offset != upload_offset:
            message = f"Expected offset '{file_metadata.offset}', received '{upload_offset}' instead"
            logger.error(message)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)

        new_offset = FileObjectManager().append_to_file(id_=file_metadata.id_, data=data)
        response = Response(
            headers={"Upload-Offset": str(new_offset)},
            status_code=status.HTTP_204_NO_CONTENT,
        )
    except GetiBaseException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Exception raised while resuming upload: {str(e)}")
        raise InternalServerErrorGetiBaseException("Unknown error faced while resuming upload")

    logger.info(
        "Patch applied to file with id %s. New offset: %s",
        str(file_id),
        str(new_offset),
    )
    return response


@router.delete("/resumable/{file_id}")
def tus_delete(
    file_id: str,
) -> Response:
    """
    TUS Delete endpoint
    Deletes all upload data for the file with given id

    :param file_id: id of the file to be deleted
    :return: 204 no content response if file is successfully deleted
    """
    logger.info(f"Handling delete `tus_delete`: file_id={file_id}")
    try:
        file_id = get_validated_mongo_id(id=file_id)
        FileObjectManager().delete_file(file_id)
    except GetiBaseException as e:
        raise HTTPException(status_code=e.http_status, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Exception raised while deleting upload file: {str(e)}")
        raise InternalServerErrorGetiBaseException("Unknown error faced while deleting uploaded file")

    logger.info("TUS deleted for file with id %s", str(file_id))
    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


def validate_tus(tus_resumable: str) -> None:
    """
    Validate tus version based on the supported tus versions

    :param tus_resumable: version of tus used by the client
    :raises HTTPException: if tus version used by the client is not supported by the user
    """
    if tus_resumable not in TUS_VERSION.split(","):
        message = (
            f"Version of tus used by client: '{tus_resumable}' is not in the list of versions"
            f"supported by server: '{TUS_VERSION}'"
        )
        logger.error(message)
        raise HTTPException(
            headers={"tus-version": TUS_VERSION},
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=message,
        )

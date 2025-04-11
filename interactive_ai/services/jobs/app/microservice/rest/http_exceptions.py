# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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
from fastapi import HTTPException
from starlette import status

from geti_types import ID


class WorkspaceNotFoundHTTPException(HTTPException):
    """
    Exception raised when workspace could not be found in database.

    :param workspace_id: ID of the workspace
    """

    def __init__(self, workspace_id: ID) -> None:
        super().__init__(
            detail=f"Workspace with id {workspace_id} could not be found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class JobNotFoundHTTPException(HTTPException):
    """
    Exception raised when a job could not be found.

    :param job_id: ID of the Job
    """

    def __init__(self, job_id: ID) -> None:
        super().__init__(
            detail=f"Job with id `{job_id}` could not be found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class JobNotPermittedHTTPException(HTTPException):
    """
    Exception raised when a job access is not permitted.
    """

    def __init__(self) -> None:
        super().__init__(
            detail="Not permitted.",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class JobNotCancellableHTTPException(HTTPException):
    """
    Exception raised when job is non-cancellable and is already started
    """

    def __init__(self) -> None:
        super().__init__(
            detail="Job cannot be cancelled.",
            status_code=status.HTTP_412_PRECONDITION_FAILED,
        )


class BadRequestHTTPException(HTTPException):
    """
    Exception to indicate a general problem with the request.

    :param message: str message providing a short description of the error
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            detail=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

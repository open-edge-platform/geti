# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from starlette import status

from geti_fastapi_tools.exceptions import GetiBaseException


class FileNotFoundGetiBaseException(GetiBaseException):
    """
    Dataset file or folder not found HTTP exception
    """

    def __init__(self, message: str = "No dataset file or folder found with given id") -> None:
        super().__init__(
            message=message,
            error_code="file_not_found",
            http_status=status.HTTP_404_NOT_FOUND,
        )


class FileNotFullyUploadedGetiBaseException(GetiBaseException):
    """
    Dataset file not fully uploaded to server
    """

    def __init__(self) -> None:
        super().__init__(
            http_status=status.HTTP_412_PRECONDITION_FAILED,
            error_code="file_not_fully_uploaded",
            message="File with given id is not fully uploaded to the server",
        )


class NotEnoughSpaceGetiBaseException(GetiBaseException):
    """Not enough space in the filesystem to perform the required operation"""

    def __init__(self, message: str) -> None:
        super().__init__(
            http_status=status.HTTP_507_INSUFFICIENT_STORAGE,
            error_code="not_enough_space",
            message=message,
        )


class BadRequestGetiBaseException(GetiBaseException):
    """
    Bad request HTTP exception

    :param message: message to be sent to client with the http error response
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="bad_request",
            http_status=status.HTTP_400_BAD_REQUEST,
        )


class CouldNotUploadZeroBytesException(BadRequestGetiBaseException):
    """
    Could not upload a file with a size of 0 bytes
    """

    def __init__(self) -> None:
        super().__init__(message="Could not upload a file with a size of 0 bytes.")


class InvalidIdGetiBaseException(GetiBaseException):
    """
    Exception raised when an invalid ID is used in a request

    :param invalid_id: The invalid ID received
    """

    def __init__(self, id_name: str, invalid_id: str) -> None:
        super().__init__(
            message=f"Invalid request parameters: '{id_name}'. The provided string is not a valid ID: '{invalid_id}'.",
            error_code="invalid_id",
            http_status=status.HTTP_400_BAD_REQUEST,
        )


class InternalServerErrorGetiBaseException(GetiBaseException):
    """
    Unknown error during dataset loading
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="internal_server_error",
            message=message,
        )


class MaxProjectsReachedGetiBaseException(GetiBaseException):
    """
    The organization has reached the maximum number of projects
    """

    def __init__(self, maximum: int) -> None:
        message = (
            f"You have hit the limit of number of projects in your organization ({maximum}). "
            f"Please delete some projects before making new ones."
        )
        super().__init__(
            http_status=status.HTTP_409_CONFLICT,
            error_code="max_projects_reached",
            message=message,
        )


class MaxLabelsReachedGetiBaseException(GetiBaseException):
    """
    The project has too many labels
    """

    def __init__(self, maximum: int) -> None:
        message = f"A project can only have a maximum of {maximum} labels. Please try with fewer labels"
        super().__init__(
            http_status=status.HTTP_409_CONFLICT,
            error_code="max_labels_reached",
            message=message,
        )


class NotImplementedGetiBaseException(GetiBaseException):
    """
    The requested feature is not implemented
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            http_status=status.HTTP_501_NOT_IMPLEMENTED,
            error_code="not_implemented",
            message=message,
        )


class PayloadTooLargeGetiBaseException(GetiBaseException):
    """
    Exception raised when the request payload is too large.

    :param max_size: Max size in bytes
    """

    def __init__(self, max_size: float) -> None:
        super().__init__(
            http_status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            error_code="payload_too_large",
            message=f"Request too large: exceeding {max_size / (2**20)} MB is not allowed.",
        )

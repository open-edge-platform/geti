import http

from geti_types import ID


class GetiBaseException(Exception):
    """
    Base class for Geti exceptions with a predefined HTTP error code.

    :param message: str message providing short description of error
    :param error_code: str id of error
    :param http_status: int default http status code to return to user
    """

    def __init__(self, message: str, error_code: str, http_status: int) -> None:
        self.message = message
        self.error_code = error_code
        self.http_status = http_status
        super().__init__(message)


class UserException(GetiBaseException):
    """
    Exception to indicate a user related problem in the request.

    :param message: str message providing a short description of the error
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="user_error",
            http_status=http.HTTPStatus.UNAUTHORIZED,
        )


class MissingRequestAccessTokenException(UserException):
    """Exception raised when the 'x-auth-request-access-token' header is missing."""

    def __init__(self) -> None:
        super().__init__("No user information provided in the request header")


class InvalidRequestAccessTokenException(UserException):
    """Exception raised when the 'x-auth-request-access-token' header has an invalid value."""

    def __init__(self, value: str | bytes) -> None:
        super().__init__(f"Invalid x-auth-request-access-token header value: `{value!r}`")


class BadRequestException(GetiBaseException):
    """
    Exception to indicate a general problem with the request.

    :param message: str message providing a short description of the error
    """

    http_status = http.HTTPStatus.BAD_REQUEST

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="bad_request",
            http_status=self.http_status,
        )


class BodyMissingRequiredParameters(GetiBaseException):
    """
    This error can be raised if the body of the request is missing required parameters.

    :param message: str containing a custom error message
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="body_missing_required_parameters",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class InvalidEntityIdentifierException(GetiBaseException):
    """
    This error is raised when an invalid entity identifier is passed in a request

    :param message: str containing a custom error message
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="invalid_entity_identifier",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class InvalidMediaException(GetiBaseException):
    """
    Exception raised when uploaded media file is invalid.

    :param message: str containing a custom message.
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="invalid_media",
            http_status=http.HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
        )


class MissingPayloadException(GetiBaseException):
    """Exception raised when the request payload is missing (null length)"""

    def __init__(self) -> None:
        super().__init__(
            message="Missing request body",
            error_code="missing_payload",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class PayloadTooLargeException(GetiBaseException):
    """
    Exception raised when the request payload is too large.

    :param max_size: Max size in MB
    """

    def __init__(self, max_size: float) -> None:
        super().__init__(
            message=f"Request too large: exceeding {max_size} MB is not allowed.",
            error_code="payload_too_large",
            http_status=http.HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
        )


class InvalidIDException(GetiBaseException):
    """
    Exception raised when an invalid ID is used in a request

    :param id_name: Name of the ID that is not a valid ID
    :param invalid_id: The invalid ID that was received from the user
    """

    http_status = http.HTTPStatus.BAD_REQUEST

    def __init__(self, id_name: str, invalid_id: str) -> None:
        super().__init__(
            message=f"Invalid request parameters: '{id_name}'. The provided string is not a valid ID: '{invalid_id}'.",
            error_code="bad_request",
            http_status=self.http_status,
        )


class ProjectNotFoundException(GetiBaseException):
    """
    Exception raised when project could not be found in database.

    :param project_id: ID of the project
    """

    def __init__(self, project_id: ID) -> None:
        super().__init__(
            message=f"The requested project could not be found. Project ID: `{project_id}`.",
            error_code="project_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )


class DatasetStorageNotFoundException(GetiBaseException):
    """
    Exception raised when dataset storage could not be found in database.

    :param dataset_storage_id: ID of the dataset storage
    """

    def __init__(self, dataset_storage_id: ID) -> None:
        super().__init__(
            message=f"The requested dataset could not be found. Dataset Storage ID: `{dataset_storage_id}`.",
            error_code="dataset_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )


class ModelNotFoundException(GetiBaseException):
    """
    Exception raised when model could not be found in database.

    :param model_id: ID of the model
    """

    def __init__(self, model_id: ID) -> None:
        super().__init__(
            message=f"The requested model could not be found. Model ID: `{model_id}`. ",
            error_code="model_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )

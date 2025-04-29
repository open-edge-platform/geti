"""
Common gateway errors.
"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from enum import IntEnum


class ResponseError(Exception):
    """Endpoint error for returning response error"""

    def __init__(self, message: str, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(message)


class WrongInputError(Exception):
    """Defines that invalid body was passed in request"""

    def __init__(self, internal_exception: Exception) -> None:
        self.internal_exception = internal_exception
        super().__init__()


class WrongPasswordFormatError(Exception):
    """Defines that wrong password format is passed in the request's body"""


class BadTokenError(Exception):
    """Defines that wrong token is passed in the request's body"""


class InvalidExpirationDate(Exception):
    """Defines that passed expiration date is invalid"""


class InvalidServiceId(Exception):
    """Defines that passed service id is not valid"""


# TODO: remove as old gateway legacy?
class GeneralError(IntEnum):
    """General gateway error."""

    NOTAUTHENTICATED = 0
    FILE_NOT_FOUND = 3
    TYPE_NOT_FOUND = 5
    CONNECTION_ERROR = 6
    K8S_ERROR = 7
    NAME_ALREADY_EXIST = 8
    INTERNAL_SYSTEM_ERROR = 9
    INVALID_INPUT = 10
    TASK_NOT_FOUND = 13
    FORBIDDEN = 14
    ELEMENT_NOT_FOUND = 15
    NOT_PERMITTED = 16
    WRONG_OLD_PASSWORD = 17
    SAME_NEW_PASSWORD = 18
    USER_ALREADY_EXISTS = 19
    EMAIL_ALREADY_REGISTERED = 20
    USER_NOT_FOUND = 21
    WEAK_PASSWORD = 22
    INVALID_EMAIL = 23
    NO_ANOTHER_ADMIN = 24
    IMAGE_TOO_BIG = 25
    NOT_IMAGE = 26
    INCORRECT_EXTENSION = 27


class ErrorMessages:
    """
    Class with error messages returned by the Gateway endpoints.
    """

    USER_ALREADY_EXISTS = "This email address is already being used."
    USER_NOT_FOUND = "User doesn't exist."
    WRONG_OLD_PASSWORD = "That’s an incorrect password. Try again."  # noqa: S105, RUF001
    SAME_NEW_PASSWORD = "Password should be different from your old password."  # noqa: S105
    EMAIL_ALREADY_REGISTERED = "This email address is already being used."
    INVALID_EMAIL = "Invalid email."
    IMAGE_TOO_BIG = "Your profile image must be 0.5 MB or less."
    IMAGE_TOO_SMALL = (
        "Uploaded image {filename} for user {user_id} is too small: {width}x{height} pixels. "
        "Minimum size is {min_size}x{min_size} pixels."
    )
    NOT_IMAGE = "File must be an image."
    INCORRECT_EXTENSION = "This image extension is not supported."
    WEAK_PASSWORD = "Specified password does not meet minimal requirements."  # noqa: S105
    OTHER_ERROR = "Unknown error has occurred."
    INCORRECT_OR_EXPIRED_SERVICE_ID = "Invalid or expired service id."
    SMTP_SERVER_NOT_CONFIGURED = (
        "The mail server is not set up for the platform. "
        "Contact an IT administrator from your organization to generate a new password for your account."
    )

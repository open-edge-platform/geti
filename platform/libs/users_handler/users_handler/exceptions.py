"""Custom exceptions"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


class UserHandlerError(Exception):
    """Default Exception for User Handler"""


class UserDoesNotExist(Exception):
    """Separate Exception for none existing user"""


class WrongOldPassword(Exception):
    """Exception for wrong old password syntax"""


class SameNewPassword(Exception):
    """Exception for the same new and old passwords"""


class UserAlreadyExists(Exception):
    """Exception for the same user id"""


class EmailAlreadyExists(Exception):
    """Exception for the same email"""


class ConnectionFault(Exception):
    """Exception for connection error"""


class WeakPassword(Exception):
    """Exception for too weak password"""


class InvalidEmail(Exception):
    """Exception for invalid email address"""


class WrongUserToken(Exception):
    """Exception for invalid user email token"""


class ImageTooBig(Exception):
    """Exception for too large image to handle it in ldap"""


class ImageTooSmall(Exception):
    """
    Exception for too small image size to handle it in ldap.
    Attributes:
        min_size - minimum image size accepted, pixels.
        image_width, image_height - actual size of the image, pixels.
    """

    def __init__(self, min_size: int, image_width: int, image_height: int) -> None:
        super().__init__()
        self.min_size = min_size
        self.image_width = image_width
        self.image_height = image_height


class IncorrectExtension(Exception):
    """Exception for not supported file extension"""


class NotImage(Exception):
    """Exception for invalid avatar files"""


class LastAdminDeletionError(Exception):
    """Exception for the only admin deletion attempt"""


class ResourceDefinitionError(ValueError):
    """Exception for invalid access resource definitions."""

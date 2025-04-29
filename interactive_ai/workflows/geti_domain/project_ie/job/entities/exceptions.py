# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Exceptions raised by Project I/E entities and services"""

from jobs_common.exceptions import TaskErrorMessage

# Low-level exceptions (errors on R/W operations)


class ManifestNotFoundError(Exception):
    """Exception raised when trying to access the manifest in a project archive but it is not found"""


class ManifestAlreadyExistsError(Exception):
    """Exception raised when trying to create a manifest to a project archive that already has one"""


class CollectionNotFoundError(Exception):
    """Exception raised when trying to access a collection in a project archive but it is not found"""


class CollectionAlreadyExistsError(Exception):
    """Exception raised when trying to create a collection to a project archive that already has one"""


class CollectionWriteError(Exception):
    """Exception raised when an error occurs while writing to a collection"""


class ProjectArchiveParsingError(Exception):
    """Exception raised when a project archive cannot be correctly parsed and interpreted"""


# High-level exceptions


class ExportProjectFailedException(Exception, TaskErrorMessage):
    """
    Generic error raised when a project cannot be exported.

    More specific exceptions can inherit from this class and refine the exception message (must be user-friendly).

    :param reason: Optional details about why the error occurred
    """

    def __init__(self, reason: str | None = None) -> None:
        if reason:
            message = f"Failed to export project: {reason}"
        else:
            message = "Failed to export project."
        super().__init__(message)


class ImportProjectFailedException(Exception, TaskErrorMessage):
    """
    Generic error raised when a project cannot be imported.

    More specific exceptions can inherit from this class and refine the exception message (must be user-friendly).

    :param reason: Optional details about why the error occurred
    """

    def __init__(self, reason: str | None = None) -> None:
        if reason:
            message = f"Failed to import project: {reason}."
        else:
            message = "Failed to import project."
        super().__init__(message)


class ExportDataRedactionFailedException(ExportProjectFailedException):
    """Exception raised when the data redaction step fails while exporting a project."""

    def __init__(self) -> None:
        super().__init__(reason="an error occurred while preparing the data to export")


class ImportDataRedactionFailedException(ImportProjectFailedException):
    """Exception raised when the data redaction step fails while importing a project."""

    def __init__(self) -> None:
        super().__init__(reason="an error occurred while preparing the data to import")


class ZipBombDetectedError(ImportProjectFailedException):
    """
    Exception raised when trying to import a file that is potentially a zip-bomb

    Note: this exception must NOT redefine the generic user-facing message for security reasons
    """


class InvalidZipFileStructure(ImportProjectFailedException):
    """Exception raised when the zip does not have the expected file structure"""

    def __init__(self) -> None:
        super().__init__(
            reason="the zip archive has an invalid file structure; please double-check that the uploaded file is "
            "actually a project exported from Geti, and not something else (e.g. a dataset)"
        )


class SignatureVerificationFailed(ImportProjectFailedException):
    """Raised when the signature verification of a file has failed."""

    def __init__(self) -> None:
        super().__init__(
            reason=(
                "the digital signature does not match the contents of the archive, "
                "or the project was signed with an untrusted key"
            )
        )


class SignatureKeysNotFound(ExportProjectFailedException, ImportProjectFailedException):
    """Raised when signature private/public keys cannot be found."""

    def __init__(self) -> None:
        super().__init__(reason="failed to locate the key necessary to sign/verify the project")


class ImportProjectUnsupportedVersionException(ImportProjectFailedException):
    """Raised when importing a project with unsupported data version."""

    def __init__(self, version: str) -> None:
        super().__init__(reason=f"project has unsupported data version '{version}'")


class ProjectUpgradeFailedException(ImportProjectFailedException):
    """Raised when the data upgrade has failed while importing a project."""

    def __init__(self) -> None:
        super().__init__(reason="an error has occurred while upgrading the project data to the current version")

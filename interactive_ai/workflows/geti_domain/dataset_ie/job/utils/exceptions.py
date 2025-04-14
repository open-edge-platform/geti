# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module defines the exceptions that can be raised in the dataset IE jobs
"""

from jobs_common.exceptions import CommandDeliberateFailureException, TaskErrorMessage


class DatasetIEException(CommandDeliberateFailureException, TaskErrorMessage):
    """
    Base exception class for dataset ie job
    """

    def __init__(self, msg: str) -> None:
        super().__init__(msg)


class MaxMediaReachedException(DatasetIEException):
    """
    Raised when the maximum number of media in the project has been reached
    """


class FileNotFoundException(DatasetIEException):
    """
    Given dataset ID is not found.
    """


class ProjectNotFoundException(DatasetIEException):
    """
    Given project ID is not found in the workspace.
    """


class DatasetFormatException(DatasetIEException):
    """
    Could not detect dataset format or detected dataset format is not supported.
    """


class DatasetLoadingException(DatasetIEException):
    """
    Could not load the dataset.
    """


class DatasetParsingException(DatasetIEException):
    """
    Could not parse the dataset.
    """


class UnsupportedMappingException(DatasetIEException):
    """
    Could not import a dataset to a project due to unsupported cross-prject mapping.
    """


class ResearvedLabelException(DatasetIEException):
    """
    Could not use reserved label name.
    """


class InvalidIDException(DatasetIEException):
    """
    ID is invalid (not in a mongo ObjectId format)
    """


class InvalidLabelException(DatasetIEException):
    """
    Label ID or label name is invalid or unknown
    """


class InvalidMediaException(DatasetIEException):
    """
    Media is invalid - cannot read it or contains an error
    """


class MaxDatasetStorageReachedException(DatasetIEException):
    """
    Max dataset storage reached
    """


class DatasetStorageAlreadyExistsException(DatasetIEException):
    """
    Given dataset storage name already exist
    """


# internal server errors
# class name will be desplayed as Code (see src/jobs/geti_domain/common/jobs_common/tasks/utils/progress.py)
class InternalServerError(Exception):
    pass


class WrongS3CredentialsProvider(InternalServerError):
    pass


class MissingEnvVariables(InternalServerError):
    pass

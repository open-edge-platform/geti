# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines the exceptions potentially raised by the scheduler."""

from iai_core.entities.model_test_result import MetricType


class TaskErrorMessage:
    """
    Mix-in for exceptions which can be thrown to report a failure message to user.
    By default, error message is a string representation of the exception, if custom logic is needed then message
    method should be overridden.
    """

    def __init__(self) -> None:
        pass

    @property
    def message(self) -> str:
        """Task error message"""
        return str(self)


class CommandInternalError(Exception):
    """Raised when a command fails to execute due to an internal error."""

    def __init__(self, msg: str = "") -> None:
        if not msg:
            msg = "The command failed due to an internal error."
        super().__init__(msg)


class CommandDeliberateFailureException(Exception):
    """
    Raised when a command fails to execute intentionally because some condition is
    not met, e.g. the quality of the output is not as good as expected.
    """

    def __init__(self, msg: str = "") -> None:
        if not msg:
            msg = "The command failed deliberately because some condition is not met"
        super().__init__(msg)


class CommandInitializationFailedException(Exception):
    """Raised when an error occurs before a command is fully initialized."""

    def __init__(self, msg: str = "") -> None:
        if not msg:
            msg = "A problem occurred while initializing the command."
        super().__init__(msg)


class CommandCancelledException(Exception):
    """Raised when a command is cancelled"""


class TrainingPodFailedException(CommandInternalError):
    """Raised when the training pod reports a failed status."""

    def __init__(self) -> None:
        msg = "Internal error in the training framework, please try again or change the model architecture/template."
        super().__init__(msg)


class InferencePodFailedException(CommandInternalError):
    """Raised when the inference pod reports a failed status."""

    def __init__(self) -> None:
        msg = "Internal failure in the inference framework"
        super().__init__(msg)


class OptimizationPodFailedException(CommandInternalError):
    """Raised when the optimization pod reports a failed status."""

    def __init__(self) -> None:
        msg = "Internal failure in the optimization framework"
        super().__init__(msg)


class DatasetCreationFailedException(CommandInternalError):
    """Raised when a dataset cannot be created."""

    def __init__(self) -> None:
        msg = "Failed to setup the dataset"
        super().__init__(msg)


class DataShardCreationFailedException(CommandInternalError):
    """Raised when dataset shards cannot be created."""

    def __init__(self) -> None:
        msg = "Failed to setup the dataset"
        super().__init__(msg)


class ComputePerformanceFailedException(CommandInternalError):
    """Raised when a performance cannot be computed."""

    def __init__(self) -> None:
        msg = "Failed to compute performance"
        super().__init__(msg)


class OutputDatasetNotAvailableException(CommandInternalError):
    """Raised when the output dataset created through inference is unavailable"""

    def __init__(self) -> None:
        msg = "Output dataset is unavailable"
        super().__init__(msg)


class TestDatasetEmptyException(CommandInternalError):
    """Raised when the test dataset of a model testing job contains no annotated data"""

    def __init__(self) -> None:
        msg = "Test dataset does not contain any annotated data."
        super().__init__(msg)


class InvalidOptimizationTypeException(ValueError):
    """Raised when optimization job with wrong type is created."""

    def __init__(self, optimization_type: str) -> None:
        msg = f"Unsupported optimization type: '{optimization_type}'. Currently, only 'POT' is supported."
        super().__init__(msg)


class UnsupportedMetricTypeForModelTestingException(ValueError):
    """
    Raised when a model testing job is launched on a metric type that is not supported
    """

    def __init__(self, metric_type: MetricType) -> None:
        msg = f"Model testing job is not available for metric of type '{metric_type.name}'"
        super().__init__(msg)


class UnsupportedModelFormatForModelTestingException(ValueError):
    """
    Raised when a model testing job is launched with a model format that is not supported
    """

    def __init__(self, format: str) -> None:
        msg = f"Model testing is not supported for model with format '{format}'"
        super().__init__(msg)

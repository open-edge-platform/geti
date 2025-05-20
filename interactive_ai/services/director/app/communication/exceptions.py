# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import http

from fastapi import HTTPException
from starlette import status

from geti_fastapi_tools.exceptions import GetiBaseException
from geti_types import ID
from iai_core.entities.model import ModelOptimizationType
from iai_core.entities.project import Project
from iai_core.entities.task_node import TaskNode


class InvalidConfigurationException(GetiBaseException):
    """
    This error is raised when an invalid value is attempted to be set for a
    configurable parameter

    :param message: str containing a custom error message
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="invalid_configuration_value",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class ObsoleteTrainingAlgorithmException(GetiBaseException):
    """
    This error can be raised if a request is made to train a model with an obsolete algorithm (model template).

    :param model_template_id: ID of the model template that is obsolete.
    """

    def __init__(self, model_template_id: str) -> None:
        super().__init__(
            message=f"The model template with id `{model_template_id}` is obsolete and cannot be used for training.",
            error_code="obsolete_training_algorithm",
            http_status=http.HTTPStatus.UNPROCESSABLE_ENTITY,
        )


class ModelAlreadyOptimizedException(GetiBaseException):
    """
    This error can be raised if a request is made to optimize an already optimized model
    with the same parameters.

    :param model_id: ID of the model to raise the error for.
    :param optimization_type: The type of optimization requested for the model.
    """

    def __init__(self, model_id: ID, optimization_type: ModelOptimizationType) -> None:
        super().__init__(
            message=f"This model has already been optimized "
            f"with the requested parameters for optimization type "
            f"'{optimization_type.name}' and cannot be optimized again. "
            f"Model ID: `{str(model_id)}`.",
            error_code="model_already_optimized",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class DatasetStorageHasNoAnnotationsException(GetiBaseException):
    """
    Exception raised when a dataset storage does not have any annotations

    :param dataset_name: name of the dataset storage
    """

    def __init__(self, dataset_name: str) -> None:
        super().__init__(
            message=f"Dataset '{dataset_name}' has no annotations.",
            error_code="dataset_has_no_annotations",
            http_status=http.HTTPStatus.CONFLICT,
        )


class NotEnoughDatasetItemsException(GetiBaseException):
    """
    Exception raised when not enough annotations have been processed into dataset items yet.
    """

    def __init__(self) -> None:
        super().__init__(
            message="Some annotations are not yet processed. Please try again later.",
            error_code="annotations_not_yet_processed",
            http_status=http.HTTPStatus.SERVICE_UNAVAILABLE,
        )


class TaskNotTrainableException(GetiBaseException):
    """
    This Error is raised when a call is made for training or configuring a task that is
    not trainable.

    :param task_node_id: ID of the task node for which a request was made
    """

    def __init__(self, task_node: TaskNode) -> None:
        message = f"Task node `{task_node.title}` is not trainable. Task Node ID: `{task_node.id_}`."
        super().__init__(
            message=message,
            error_code="task_not_trainable",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class TaskNotFoundInProjectException(GetiBaseException):
    """
    Exception raised when the task node is not part of the project

    :param task_id: ID of the task
    :param project: The project
    """

    def __init__(self, task_id: ID, project: Project) -> None:
        super().__init__(
            message=f"The requested task cannot be found in project `{project.name}`. "
            f"Task Node ID: `{task_id}`, Project ID: `{project.id_}`.",
            error_code="task_not_found_in_project",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class ConfigurationMismatchException(GetiBaseException):
    """
    This error is raised when a configuration is attempted to be saved that does not
    match the expected configuration structure for that particular task or component

    :param message: str containing a custom error message
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="cannot_set_configuration",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class JobCreationFailedException(GetiBaseException):
    """
    This error can be raised if job creation is requested but fails

    :param message: str containing a custom error message
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="job_creation_failed",
            http_status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
        )


class JobInsufficientBalanceException(GetiBaseException):
    """
    This error can be raised if there are not enough credits during job creation

    :param message: str containing a custom error message
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="job_insufficient_balance",
            http_status=http.HTTPStatus.PRECONDITION_FAILED,
        )


class NotReadyForTrainingException(GetiBaseException):
    """
    Exception raised when a manual training trigger is received for a task that is not
    ready for training

    :param reason: message detailing the reason why the task is not ready
    """

    def __init__(self, reason: str) -> None:
        super().__init__(
            message=f"Unable to start training. {reason}",
            error_code="project_not_train_ready",
            http_status=http.HTTPStatus.NOT_ACCEPTABLE,
        )


class NotReadyForOptimizationException(GetiBaseException):
    """
    Exception raised when a manual optimization trigger is received for a model that cannot currently be optimized

    :param reason: message detailing the reason why the task is not ready
    """

    def __init__(self, reason: str) -> None:
        super().__init__(
            message=f"Unable to start optimization. {reason}",
            error_code="model_not_optimization_ready",
            http_status=http.HTTPStatus.NOT_ACCEPTABLE,
        )


class NotEnoughSpaceException(GetiBaseException):
    """
    This error can be raised if a request is blocked because there is not enough space on the disk.

    :param message: str containing a custom error message
    """

    http_status = http.HTTPStatus.INSUFFICIENT_STORAGE

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="not_enough_space",
            http_status=self.http_status,
        )


class MissingJobPayloadAttribute(GetiBaseException):
    """
    Exception raised when a job payload attribute is expected but missing.

    :param attribute: the missing attribute
    """

    def __init__(self, attribute: str) -> None:
        super().__init__(
            message=f"The job payload is missing the required attribute '{attribute}'.",
            error_code="missing_job_payload_attribute",
            http_status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
        )


class DeprecatedMethodException(GetiBaseException):
    """
    This error is raised when a functionality, or part of it, has been deprecated and
    is therefore no longer supported

    :param message: the message that describes the error
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="deprecated_method",
            http_status=http.HTTPStatus.NOT_IMPLEMENTED,
        )


class UnsupportedFormatForModelTestingException(GetiBaseException):
    """
    This error is raised when submitting a model test job for a model with unsupported format.

    :param model_format: the unsupported model format
    """

    def __init__(self, model_format: str) -> None:
        super().__init__(
            message=f"Model testing is not supported for model with format '{model_format}'. "
            f"Only models with OpenVino format is supported.",
            error_code="unsupported_model_test",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class DeprecatedMetricModelTestingException(GetiBaseException):
    """
    This error is raised when submitting a model test job with a deprecated metric.

    :param metric: the deprecated metric
    """

    def __init__(self, metric: str) -> None:
        super().__init__(
            message=f"Model testing with a {metric} metric has been deprecated'",
            error_code="deprecated_model_metric_test",
            http_status=http.HTTPStatus.UNPROCESSABLE_ENTITY,
        )


class PurgedModelException(GetiBaseException):
    """
    This exception is raised when an operation is performed on a purged model that is not allowed.

    :param message: the message that describes the error
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="model_purging_not_possible",
            http_status=http.HTTPStatus.UNPROCESSABLE_ENTITY,
        )


class DeprecatedModelTestException(GetiBaseException):
    """
    This exception is raised when a request is made for a model test which has been deprecated.

    :param model_test_id: the ID of the model test which has been deprecated
    """

    def __init__(self, model_test_id: ID) -> None:
        super().__init__(
            message=f"The requested model test (ID:{model_test_id}) has been deprecated.",
            error_code="deprecated_model_test",
            http_status=http.HTTPStatus.UNPROCESSABLE_ENTITY,
        )


class ObsoleteModelOptimizationException(GetiBaseException):
    """
    This error can be raised if a request is made to optimise an obsolete model.

    :param model_id: ID of the model that is obsolete.
    """

    def __init__(self, model_id: str) -> None:
        super().__init__(
            message=f"The model with id `{model_id}` is obsolete and cannot be used for optimization.",
            error_code="obsolete_model",
            http_status=http.HTTPStatus.UNPROCESSABLE_ENTITY,
        )


class WorkspaceNotFoundException(GetiBaseException):
    """
    Exception raised when workspace could not be found in database.

    :param workspace_id: ID of the workspace
    """

    def __init__(self, workspace_id: ID | None) -> None:
        super().__init__(
            message=f"The requested workspace could not be found. Workspace ID: `{workspace_id}`.",
            error_code="workspace_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )


class DatasetStorageNotInProjectException(GetiBaseException):
    """
    Exception raised when no dataset storage with given id found in project

    :param project_id: ID of project
    :param dataset_storage_id: ID of dataset storage
    """

    def __init__(self, project: Project, dataset_storage_id: ID) -> None:
        super().__init__(
            message=f"The requested dataset could not be found in project `{project.name}`. "
            f"Project ID: '{project.id_}', "
            f"Dataset Storage ID: `{dataset_storage_id}`. ",
            error_code="dataset_not_found_in_project",
            http_status=http.HTTPStatus.NOT_FOUND,
        )


class ModelStorageNotFoundException(GetiBaseException):
    """
    Exception raised when model storage could not be found in database.

    :param model_storage_id: ID of the model storage
    :param message: Optional custom message. Overrides the default message if specified
    """

    def __init__(self, model_storage_id: ID, message: str | None = None) -> None:
        if message is None:
            message = (
                f"The requested model storage or model group could not be found. "
                f"Model Storage ID: `{model_storage_id}`. "
            )
        super().__init__(
            message=message,
            error_code="model_storage_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )


class TaskNotFoundException(GetiBaseException):
    """
    Exception raised when task could not be found in database.

    :param task_id: ID of the task
    """

    def __init__(self, task_id: ID) -> None:
        super().__init__(
            message=f"The requested task could not be found. Task Node ID: `{task_id}`. ",
            error_code="task_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )


class AlgorithmNotFoundException(GetiBaseException):
    """
    Exception raised when an algorithm could not be found in the model storages of a task

    :param message: str containing a custom error message
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="algorithm_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )


class VideoNotFoundException(GetiBaseException):
    """
    Exception raised when video could not be found in database.

    :param video_id: ID of the video
    :param dataset_storage_id: ID of the dataset_storage
    """

    def __init__(self, video_id: ID, dataset_storage_id: ID) -> None:
        super().__init__(
            message=(
                f"The requested video could not be found in this dataset. "
                f"Dataset Storage ID: `{dataset_storage_id}`, "
                f"Video ID: `{video_id}'. "
            ),
            error_code="video_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )


class PredictionNotFoundException(GetiBaseException):
    """
    Exception raised when a prediction is requested by ID but is not found in the database

    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="prediction_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )


class NoPredictionsFoundException(GetiBaseException):
    """
    Exception raised when no prediction exists for the media in the database

    """

    def __init__(self, media_id: ID) -> None:
        super().__init__(
            message=f"There are no predictions that belong to the requested media. Media ID: `{media_id}`.",
            error_code="no_predictions_found",
            http_status=http.HTTPStatus.NO_CONTENT,
        )


class ConfigurationNotFoundException(GetiBaseException):
    """This error is raised when a configuration is not found in the repository

    :param message: str containing a custom error message
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="configuration_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )


class NoModelTrainedException(GetiBaseException):
    """
    This error is raised when a request is made for inference, but there is no trained model
    """

    def __init__(self) -> None:
        super().__init__(
            message="",
            error_code="no_model_trained_error",
            http_status=http.HTTPStatus.NO_CONTENT,
        )


class NoActiveMediaException(GetiBaseException):
    """
    This error can be raised if an active piece of media is requested but none exist at this moment

    :param message: str containing a custom error message
    """

    def __init__(self, message: str | None = None) -> None:
        message = "No active media found in dataset" if message is None else message
        super().__init__(
            message=message,
            error_code="no_active_media",
            http_status=http.HTTPStatus.NO_CONTENT,
        )


class ModelTestResultNotFoundException(GetiBaseException):
    """
    Exception raised when model test result could not be found in database.

    :param model_test_result_id: ID of the model test result
    """

    def __init__(self, model_test_result_id: ID) -> None:
        super().__init__(
            message=f"The requested test results could not be found.Model Test Result ID: `{model_test_result_id}`.",
            error_code="test_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )


class LabelNotFoundException(GetiBaseException):
    """
    Exception raised when label could not be found in database.

    :param label_id: ID of the label
    :param label_name: Name of the label
    :param project: Project to which the label belongs
    :param message: Preset message to send with the exception
    """

    def __init__(
        self,
        label_id: ID | None = None,
        label_name: str | None = None,
        project: Project | None = None,
        message: str | None = None,
    ) -> None:
        label_identifier = f"Label ID: `{label_id}`. " if label_id is not None else ""

        label_description = f"Label `{label_name}`" if label_name is not None else "The requested label"

        if message is not None:
            pass
        elif project is None:
            message = f"{label_description} could not be found. {label_identifier}"
        else:
            message = (
                f"{label_description} does not belong to project `{project.name}`. "
                f"Project ID: `{project.id_}`. {label_identifier}"
            )

        super().__init__(
            message=message,
            error_code="label_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )


class NotEnoughSpaceHTTPException(HTTPException):
    """Not enough space in the filesystem to perform the required operation"""

    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail=message,
        )


class ProjectConfigurationNotFoundException(GetiBaseException):
    """Exception raised when the project configuration could not be found in the database"""

    def __init__(self, project_id: ID) -> None:
        super().__init__(
            http_status=status.HTTP_404_NOT_FOUND,
            error_code="project_configuration_not_found",
            message=f"Project configuration not found for project ID: {project_id}",
        )


class TaskNodeNotFoundException(GetiBaseException):
    """
    Exception raised when task node could not be found in database.

    :param task_node_id: ID of the task node
    """

    def __init__(self, task_node_id: ID) -> None:
        super().__init__(
            message=f"The requested task node could not be found. Task Node ID: `{task_node_id}`.",
            error_code="task_node_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )

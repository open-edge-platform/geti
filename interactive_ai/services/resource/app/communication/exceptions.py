# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import http
from collections.abc import Mapping

from geti_fastapi_tools.exceptions import GetiBaseException
from geti_types import ID, ImageIdentifier, MediaIdentifierEntity, VideoFrameIdentifier
from iai_core_py.entities.annotation import AnnotationSceneKind
from iai_core_py.entities.datasets import DatasetPurpose
from iai_core_py.entities.model_template import TaskType
from iai_core_py.entities.project import Project


class NodePositionIsOutOfBoundsException(GetiBaseException):
    """
    Error raised when a node's position is out of bounds.
    """

    def __init__(self) -> None:
        super().__init__(
            message="One of the node's position is out of bounds.",
            error_code="node_out_of_bounds",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class NodeNameNotInLabelsException(GetiBaseException):
    """
    Error raised when a node name is not in the list of labels
    """

    def __init__(self) -> None:
        super().__init__(
            message="One of the node names is not in the list of labels.",
            error_code="node_name_not_in_labels",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class IncorrectNodeNameInGraphException(GetiBaseException):
    """
    Error raised when a graph edge has an incorrect node name.
    """

    def __init__(self) -> None:
        super().__init__(
            message="One of the edges of the graph has an incorrect name.",
            error_code="incorrect_node_in_graph",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class DatasetStorageAlreadyExistsException(GetiBaseException):
    """
    Exception raised when a dataset storage with the same name already exists

    :param name: str with name of the dataset storage
    """

    def __init__(self, name: str) -> None:
        super().__init__(
            message=f"Cannot create or update dataset. Another dataset with name '{name}' already exists.",
            error_code="dataset_already_exists",
            http_status=http.HTTPStatus.CONFLICT,
        )


class MaxNumberOfDatasetsException(GetiBaseException):
    """
    Exception raised when the limit of datasets is exceeded

    :param maximum: the maximum allowed number of datasets
    """

    def __init__(self, maximum: int) -> None:
        super().__init__(
            message=f"Cannot create another dataset. The maximum of {maximum} has been reached.",
            error_code="too_many_datasets",
            http_status=http.HTTPStatus.CONFLICT,
        )


class DuplicatedAnnotationIDException(GetiBaseException):
    """
    Exception raised when a request contains duplicate annotation IDs

    :param message: str containing a custom message.
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="duplicated_annotation_id",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class ConflictingExclusiveLabelsException(GetiBaseException):
    """
    Exception raised when a request contains annotations having multiple labels
    that are mutually exclusive (i.e. incompatible) within that annotation.

    :param groups_with_conflicts: Dict mapping the name of each group to the
        list of conflicting labels.
    """

    def __init__(self, groups_with_conflicts: Mapping[str, set[str]]) -> None:
        message = (
            f"Cannot create annotation due to conflicting labels. These exclusive "
            f"groups have two or more labels: {groups_with_conflicts}"
        )
        super().__init__(
            message=message,
            error_code="conflicting_exclusive_labels",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class InvalidFilterException(GetiBaseException):
    """
    This Error is raised when a call is made to filter the dataset with an invalid JSON
    query

    :param message: str containing a custom error message
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="invalid_filter",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class EmptyProjectNameException(GetiBaseException):
    """Error raised when a request contains an empty project name"""

    def __init__(self) -> None:
        message = "The project name cannot be empty."
        super().__init__(
            message=message,
            error_code="empty_project_name",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class NoTasksInProjectException(GetiBaseException):
    """
    Error raised when a request contains a project without any task

    :param operation: Type of operation being applied to the project
    """

    def __init__(self, operation: str) -> None:
        message = f"Cannot {operation} a project without tasks in the pipeline."
        super().__init__(
            message=message,
            error_code="taskless_project",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class NoTasksConnectionsException(GetiBaseException):
    """Error raised when a request contains a project with no connections between the tasks"""

    def __init__(self) -> None:
        message = "Cannot create a project without connections between the tasks in the pipeline."
        super().__init__(
            message=message,
            error_code="no_tasks_connections",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class DuplicateTaskNamesException(GetiBaseException):
    """Error raised when a request contains tasks with duplicate names"""

    def __init__(self) -> None:
        message = "Task titles must be unique"
        super().__init__(
            message=message,
            error_code="duplicate_task_names",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class InvalidTaskTypeException(GetiBaseException):
    """
    Error raised when a request contains an invalid task

    :param task_type: The task type which is invalid
    """

    def __init__(self, task_type: str) -> None:
        message = f"Task type '{task_type}' is not valid."
        super().__init__(
            message=message,
            error_code="invalid_task_type",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class BadNumberOfConnectionsException(GetiBaseException):
    """Error raised when a request contains a wrong number of connections between the tasks"""

    def __init__(self) -> None:
        message = "Number of connections should be one less than the number of tasks"
        super().__init__(
            message=message,
            error_code="bad_number_of_task_connections",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class TooManySourceTasksException(GetiBaseException):
    """Error raised when a request contains more than one task whose input is not connected to another task"""

    def __init__(self) -> None:
        message = "All tasks but one should appear in a connection as 'to'"
        super().__init__(
            message=message,
            error_code="too_many_source_tasks",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class TooManySinkTasksException(GetiBaseException):
    """Error raised when a request contains more than one task whose output is not connected to another task"""

    def __init__(self) -> None:
        message = "All tasks but one should appear in a connection as 'from'"
        super().__init__(
            message=message,
            error_code="too_many_sink_tasks",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class TooManyTasksException(GetiBaseException):
    """Error raised when a request contains more than 2 tasks"""

    def __init__(self) -> None:
        message = "Maximum of two trainable tasks are permitted in a project."
        super().__init__(
            message=message,
            error_code="too_many_tasks",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class TooManyLabelsException(GetiBaseException):
    """Error raised when a request contains too many labels"""

    def __init__(self, maximum: int) -> None:
        message = f"Maximum of {maximum} labels are permitted in a project."
        super().__init__(
            message=message,
            error_code="too_many_labels",
            http_status=http.HTTPStatus.CONFLICT,
        )


class UnconnectedTasksException(GetiBaseException):
    """Error raised when a request contains tasks without connections"""

    def __init__(self) -> None:
        message = "One or more tasks are not connected in the pipeline"
        super().__init__(
            message=message,
            error_code="unconnected_tasks",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class BadNumberOfLabelsException(GetiBaseException):
    """
    Error raised when a request contains a task with a wrong number of labels

    :param task_title: Name of the task
    :param num_labels: Number of labels found in the task REST description
    :param expected_num_labels_str: Human-readable string to explain the expected
        number of labels
    """

    def __init__(self, task_title: str, num_labels: int, expected_num_labels_str: str) -> None:
        message = (
            f"Wrong number of labels provided for task `{task_title}`; "
            f"found {num_labels}, expected {expected_num_labels_str}."
        )
        super().__init__(
            message=message,
            error_code="bad_number_of_labels",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class DuplicateLabelNamesException(GetiBaseException):
    """Error raised when a request contains labels with duplicate names"""

    def __init__(self) -> None:
        message = "Label names must be unique"
        super().__init__(
            message=message,
            error_code="duplicate_label_names",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class DuplicateHotkeysException(GetiBaseException):
    """Error raised when a request contains labels with duplicate hotkeys"""

    def __init__(self) -> None:
        message = "Label hotkeys must be unique"
        super().__init__(
            message=message,
            error_code="duplicate_label_hotkeys",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class DuplicateLabelColorsException(GetiBaseException):
    """Error raised when a request contains labels with duplicate colors"""

    def __init__(self) -> None:
        message = "Label colors must be unique"
        super().__init__(
            message=message,
            error_code="duplicate_label_colors",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class UnsupportedHierarchicalLabelsException(GetiBaseException):
    """
    Error raised when a request contains hierarchical labels in a task that does
    not support them.

    :param task_type: Type of the task containing the labels
    """

    def __init__(self, task_type: TaskType) -> None:
        message = f"Labels for task of type `{task_type}` cannot be hierarchical"
        super().__init__(
            message=message,
            error_code="unsupported_hierarchical_labels",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class ParentLabelNotFoundException(GetiBaseException):
    """
    Error raised when a request contains a label whose parent can not be found.

    :param label_name: Name of the label
    :param parent_id: ID or name of the parent label
    """

    def __init__(self, label_name: str, parent_id: str) -> None:
        message = f"Could not locate the parent of label `{label_name}`. Parent Label ID `{parent_id}`."
        super().__init__(
            message=message,
            error_code="parent_label_not_found",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class EmptyParentLabelException(GetiBaseException):
    """
    Error raised when a request contains a label whose parent is an empty label.

    :param label_name: Name of the label
    """

    def __init__(self, label_name: str) -> None:
        message = f"Label '{label_name}' cannot be a child of an empty label."
        super().__init__(
            message=message,
            error_code="empty_parent_label",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class MultiTaskLabelGroupException(GetiBaseException):
    """
    Error raised when a request contains a label group that spans across multiple tasks

    :param group_name: Name of the label group
    """

    def __init__(self, group_name: str) -> None:
        message = (
            f"The label group '{group_name}' is used in multiple tasks, but "
            f"label groups can only apply to a single task."
        )
        super().__init__(
            message=message,
            error_code="multi_task_label_group",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class MultipleEmptyLabelsException(GetiBaseException):
    """
    Error raised when a request contains a task that contains multiple empty labels

    :param group_name: Name of the label group
    """

    def __init__(self, group_name: str) -> None:
        message = f"Label group '{group_name}' contains multiple empty labels. "
        super().__init__(
            message=message,
            error_code="multiple_empty_labels",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class MismatchingParentsInLabelGroupException(GetiBaseException):
    """
    Error raised when a request contains a label group where two or more labels
    have a different parent.

    :param group_name: Name of the label group
    """

    def __init__(self, group_name: str) -> None:
        message = (
            f"Label group '{group_name}' has labels with different parents, but "
            f"labels in the same group are not allowed to have different parents."
        )
        super().__init__(
            message=message,
            error_code="mismatching_parents_in_label_group",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class ReservedLabelNameException(GetiBaseException):
    """
    Error raised when a request contains a user-defined label with a reserved name.
    """

    def __init__(self, label_name: str) -> None:
        message = f"The label name or group '{label_name}' is a reserved name and cannot be assigned manually."
        super().__init__(
            message=message,
            error_code="reserved_empty_label",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class EmptyLabelAdditionException(GetiBaseException):
    """Error raised when a request attempts to add a new empty label."""

    def __init__(self) -> None:
        message = "Empty labels cannot be added to existing tasks."
        super().__init__(
            message=message,
            error_code="empty_label_addition",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class MissingLabelsException(GetiBaseException):
    """Error raised when a request attempt to update the project, but omitted labels that are currently in the
    project."""

    def __init__(self, label_ids: list[ID]) -> None:
        message = (
            f"Not all of the project's labels were present in the request body. If you "
            f"wish to delete labels, please set the 'is_deleted' flag to true for the labels you "
            f"wish to remove. The following labels were missing: `{label_ids}`."
        )
        super().__init__(
            message=message,
            error_code="missing_labels",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class SelfReferencingParentLabelException(GetiBaseException):
    """Error raised when a request contains a label whose parent is the label itself."""

    def __init__(self) -> None:
        message = "The parent of a label cannot be the label itself"
        super().__init__(
            message=message,
            error_code="self_referencing_parent_label",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class InvalidLabelDeletedException(GetiBaseException):
    """Error raised when a request tries to delete a label which does not adhere to the
    label restrictions of a project."""

    def __init__(self, reason: str) -> None:
        message = f"One or more labels can not be deleted because of the following reason: {reason}"
        super().__init__(
            message=message,
            error_code="invalid_label_deleted",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class MediaUploadedWithNoLabelToAnomalyTaskException(GetiBaseException):
    """Error raised when media without a label is uploaded to an Anomaly task"""

    def __init__(self) -> None:
        super().__init__(
            message="You cannot upload media without a label to an Anomaly task.",
            error_code="deleted_label_in_annotation",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class IncompatibleModelFormatException(GetiBaseException):
    """
    Error raised when the client requests for code deployment for non-OpenVINO models
    """

    def __init__(self, model_id: ID) -> None:
        super().__init__(
            message=f"Cannot deploy code because the requested model is not in OpenVINO IR format. "
            f"Model ID: `{model_id}`.",
            error_code="incompatible_model_format",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class UnexpectedDatasetPurposeException(GetiBaseException):
    """
    Error raised when the provided dataset id does not have the expected purpose.
    """

    def __init__(self, dataset_id: ID, expected_purpose: DatasetPurpose) -> None:
        super().__init__(
            message=f"Requested dataset is not a {expected_purpose.name.lower()} dataset. Dataset ID: `{dataset_id}`.",
            error_code="dataset_is_not_a_training_dataset",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class VideoFrameOutOfRangeException(GetiBaseException):
    """
    Error raised when a video frame is requested, but this frame is out of range.
    """

    def __init__(self, video_id: ID, frame_index: int, total_frames: int) -> None:
        super().__init__(
            message=f"Requested video frame with frame_index {frame_index} is out of range for video with "
            f"{total_frames} frames. Video ID: {video_id}.",
            error_code="frame_index_out_of_range",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class WrongNumberOfNodesException(GetiBaseException):
    """
    Error raised a graph edge is made with wrong number of nodes (other than 2).
    """

    def __init__(self) -> None:
        super().__init__(
            message="One of the edges of the graph has a wrong number of nodes.",
            error_code="wrong_number_of_nodes",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class DuplicateEdgeInGraphException(GetiBaseException):
    """
    Error raised when a graph edge is made with duplicate edges.
    """

    def __init__(self) -> None:
        super().__init__(
            message="The provided graph contains a duplicate edge.",
            error_code="duplicate_edge_in_graph",
            http_status=http.HTTPStatus.BAD_REQUEST,
        )


class CodeDeploymentCorruptException(GetiBaseException):
    """
    Error raised when the code deployment is in Done state, but the binary URL is not set properly.
    """

    def __init__(self, code_deployment_id: ID, deployment_state: str) -> None:
        super().__init__(
            message=f"The code deployment file cannot be found or is corrupted. "
            f"Please try again. "
            f"Deployment state: {deployment_state}, "
            f"Code Deployment ID: `{code_deployment_id}`. ",
            error_code="code_deployment_corrupt",
            http_status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
        )


class CodeDeploymentFileIsNotReadyException(GetiBaseException):
    """
    Error raised when the client requests to download code deployment that is not ready to be downloaded.
    """

    def __init__(self, code_deployment_id: ID, deployment_state: str) -> None:
        super().__init__(
            message=f"The code deployment is not ready for download. "
            f"Please wait a few seconds for the packaging process to finish and try again. "
            f"Deployment state: {deployment_state}. "
            f"Code Deployment ID: `{code_deployment_id}`. ",
            error_code="code_deployment_download_not_ready",
            http_status=http.HTTPStatus.SERVICE_UNAVAILABLE,
        )


class ProjectLockedException(GetiBaseException):
    """
    Exception raised when project entity is locked for deletion/modification

    :param name: str with name of the project
    """

    def __init__(self, name: str) -> None:
        super().__init__(
            message=f"Project {name} is locked for deletion/modification. "
            f"Please wait until all jobs related to this project are finished "
            f"or cancel them to allow deletion/modification.",
            error_code="project_locked",
            http_status=http.HTTPStatus.CONFLICT,
        )


class SettingsTooLongException(GetiBaseException):
    """
    Exception raised when the user settings string is too large.
    """

    def __init__(self, max_settings_length: int) -> None:
        super().__init__(
            message=f"Settings provided exceed the maximum of {str(max_settings_length)} characters",
            error_code="settings_too_long",
            http_status=http.HTTPStatus.BAD_REQUEST,
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


class FileNotFoundException(GetiBaseException):
    """
    This Error is raised when a call is made to the binary repo but the file is not present.

    :param message: str containing a custom error message
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="file_not_found",
            http_status=http.HTTPStatus.INTERNAL_SERVER_ERROR,
        )


class ModelStorageNotActivableException(GetiBaseException):
    """
    This error is raised when a model storage activation is requested, but the storage
    cannot be activated. This is the case when the model storage has no successful models.

    :param model_storage_id: ID of the model storage
    """

    def __init__(self, model_storage_id: ID) -> None:
        super().__init__(
            message=f"Model storage cannot be activated. Model Storage ID: `{model_storage_id}`.",
            error_code="model_storage_not_activable",
            http_status=http.HTTPStatus.METHOD_NOT_ALLOWED,
        )


class CurrentlyNotImplementedException(GetiBaseException):
    """
    This error is raised when a functionality, or part of it, is not yet implemented
    but, it is expected that it will be implemented.

    :param message: the message that describes the error
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="not_implemented",
            http_status=http.HTTPStatus.METHOD_NOT_ALLOWED,
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


class TrainingRevisionNotFoundException(GetiBaseException):
    """
    Exception raised when dataset (=training revision) could not be found in the database.

    :param dataset_id: ID of the dataset
    """

    def __init__(self, dataset_id: ID) -> None:
        super().__init__(
            message=f"The requested training revision could not be found. Dataset ID: `{dataset_id}",
            error_code="training_revision_not_found",
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


class LabelSchemaNotFoundException(GetiBaseException):
    """
    Exception raised when label could not be found in database.

    :param label_schema_id: Optional, ID of the label schema
    :param project_id: Optional, ID of the project the schema refers to
    :param task_node_id: Optional, ID of the task node the schema refers to
    """

    def __init__(
        self,
        label_schema_id: ID | None = None,
        project_id: ID | None = None,
        task_node_id: ID | None = None,
    ) -> None:
        schema_id_msg = f"Label Schema ID: `{label_schema_id}`, " if label_schema_id else ""
        project_id_msg = f"Project ID: `{project_id}`, " if project_id else ""
        task_node_id_msg = f"Task Node ID: `{task_node_id}`. " if task_node_id else ""

        message = f"The requested label schema could not be found. {schema_id_msg}{project_id_msg}{task_node_id_msg}"
        super().__init__(
            message=message,
            error_code="label_schema_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )


class AnnotationsNotFoundException(GetiBaseException):
    """
    Exception raised when annotation could not be found in database.

    :param media_identifier: MediaIdentifierEntity of the media for which annotations
        are not found
    """

    def __init__(self, media_identifier: MediaIdentifierEntity) -> None:
        if isinstance(media_identifier, ImageIdentifier):
            message = f"Annotations for this image could not be found.  Image ID: `{media_identifier.media_id}`. "
        elif isinstance(media_identifier, VideoFrameIdentifier):
            message = (
                f"Annotations for frame index {media_identifier.frame_index} for this video could not be found. "
                f" Video ID: `{media_identifier.media_id}`. "
            )
        else:
            message = f"Annotations for this media could not be found. Media ID: `{media_identifier.media_id}`. "

        super().__init__(
            message=message,
            error_code="annotation_not_found",
            http_status=http.HTTPStatus.NO_CONTENT,
        )


class AnnotationSceneNotFoundException(GetiBaseException):
    """
    Exception raised when annotation scene could not be found in database.

    :param annotation_scene_id: ID of the annotation scene that is not found
    """

    def __init__(
        self,
        annotation_scene_id: ID,
        annotation_kind: AnnotationSceneKind | None = None,
    ) -> None:
        if annotation_kind is not None:
            message = (
                f"The requested annotation scene is not of kind ANNOTATION, but of kind {annotation_kind}. "
                f"Annotation Scene ID: `{annotation_scene_id}`. "
            )
        else:
            message = (
                f"The requested annotation scene could not be found. Annotation Scene ID: `{annotation_scene_id}`. "
            )

        super().__init__(
            message=message,
            error_code="annotation_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )


class ImageNotFoundException(GetiBaseException):
    """
    Exception raised when image could not be found in database.

    :param image_id: ID of the image
    :param dataset_storage_id: ID of the DatasetStorage
    """

    def __init__(self, image_id: ID, dataset_storage_id: ID) -> None:
        super().__init__(
            message=(
                f"The requested image could not be found in this dataset. "
                f"Dataset Storage ID: `{dataset_storage_id}`, "
                f"Image ID: `{image_id}`. "
            ),
            error_code="image_not_found",
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


class VideoFrameNotFoundException(GetiBaseException):
    """
    Exception raised when video frame could not be found in a video.

    :param video_id: ID of the video
    :param frame_index: int of frame index
    """

    def __init__(self, video_id: ID, frame_index: int) -> None:
        super().__init__(
            message=(
                f"The requested frame index {frame_index} could not be found in this video. Video ID: `{video_id}`. "
            ),
            error_code="video_frame_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )


class VideoThumbnailNotFoundException(GetiBaseException):
    """
    Exception raised when a video thumbnail could not be found in database.

    :param video_id: ID of the video
    """

    def __init__(self, video_id: ID) -> None:
        super().__init__(
            message=(
                f"Thumbnail video for this video "
                f"is not ready yet. Generation of the thumbnail "
                f"video has been queued. "
                f"Video ID: `{video_id}`. "
            ),
            error_code="thumbnail_video_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )


class NoUserSettingsException(GetiBaseException):
    """
    Exception raised when user settings are requested but not yet in the database
    """

    def __init__(self) -> None:
        super().__init__(
            message="No user settings were found.",
            error_code="user_settings_not_found",
            http_status=http.HTTPStatus.NO_CONTENT,
        )


class NoMediaInProjectException(GetiBaseException):
    """
    Exception raised when thumbnail is prompted for the project but there is no media in the project

    """

    http_status = http.HTTPStatus.NO_CONTENT

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="media_not_found",
            http_status=self.http_status,
        )


class EvaluationResultNotFoundException(GetiBaseException):
    """
    This error is raised when a request is made that depends on a EvaluationResult,
    but it is not (yet) available in the Repo.

    :param message: str containing a custom error message
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="evaluation_result_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
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


class FailedHealthCheck(RuntimeError):
    pass


class CodeDeploymentNotFoundException(GetiBaseException):
    """
    Error raised when the client requests for a code deployment for that does not exist.
    """

    def __init__(self, code_deployment_id: ID) -> None:
        super().__init__(
            message=f"Cannot find the requested code deployment. "
            f"Please trigger a new code deployment request. "
            f"Code Deployment ID: `{code_deployment_id}`.",
            error_code="code_deployment_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )


class ExportableCodeNotInitializedException(GetiBaseException):
    """
    Error raised when a model does not have an initialized exportable code.
    """

    def __init__(self, model_id: ID) -> None:
        super().__init__(
            message=f"Cannot find exportable code for the requested model. "
            f"Please trigger a new export request. "
            f"Model ID: `{model_id}`.",
            error_code="exportable_code_not_found",
            http_status=http.HTTPStatus.NOT_FOUND,
        )

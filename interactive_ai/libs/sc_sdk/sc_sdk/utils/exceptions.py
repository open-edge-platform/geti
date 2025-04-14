# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Exceptions raised within the project builder"""

from sc_sdk.entities.model_template import TaskType

from geti_types import ID


class InvalidProjectDataException(Exception):
    """
    Exception raised for errors in project data.

    :param message: str message providing short description of error
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class EmptyProjectNameException(InvalidProjectDataException):
    """Error raised when project data contains an empty project name"""

    def __init__(self) -> None:
        message = "The project name cannot be empty."
        super().__init__(message=message)


class NoTasksInProjectException(InvalidProjectDataException):
    """
    Error raised when project data contains a project without any task
    """

    def __init__(self) -> None:
        message = "Cannot operate over a project without tasks."
        super().__init__(
            message=message,
        )


class NoTasksConnectionsException(InvalidProjectDataException):
    """
    Error raised when project data contains no task connection
    """

    def __init__(self) -> None:
        message = "Cannot operate over a project without task connections."
        super().__init__(
            message=message,
        )


class BadNumberOfConnectionsException(InvalidProjectDataException):
    """
    Error raised when project data contains wrong task connections number
    """

    def __init__(self) -> None:
        message = "Cannot operate over a project with wrong task connections number."
        super().__init__(
            message=message,
        )


class TooManySourceTasksException(InvalidProjectDataException):
    """
    Error raised when project data contains too many task outcomming connections
    """

    def __init__(self) -> None:
        message = "Cannot operate over a project with too many outcomming task connections."
        super().__init__(
            message=message,
        )


class TooManySinkTasksException(InvalidProjectDataException):
    """
    Error raised when project data contains too many task incoming connections
    """

    def __init__(self) -> None:
        message = "Cannot operate over a project with too many incoming task connections."
        super().__init__(
            message=message,
        )


class UnconnectedTasksException(InvalidProjectDataException):
    """
    Error raised when project data contains unconnected tasks
    """

    def __init__(self) -> None:
        message = "Cannot operate over a project with unconnected tasks."
        super().__init__(
            message=message,
        )


class DuplicateTaskNamesException(InvalidProjectDataException):
    """Error raised when project data contains tasks with duplicate names"""

    def __init__(self) -> None:
        message = "Task titles must be unique"
        super().__init__(
            message=message,
        )


class BadNumberOfLabelsException(InvalidProjectDataException):
    """
    Error raised when project data contains a task with a wrong number of labels

    :param task_name: Name of the task
    :param num_labels: Number of labels found in the task REST description
    :param expected_num_labels_str: Human-readable string to explain the expected
        number of labels
    """

    def __init__(self, task_name: str, num_labels: int, expected_num_labels_str: str) -> None:
        message = (
            f"Wrong number of labels provided for task `{task_name}`; "
            f"found {num_labels}, expected {expected_num_labels_str}."
        )
        super().__init__(
            message=message,
        )


class DuplicateLabelNamesException(InvalidProjectDataException):
    """Error raised when project data contains labels with duplicate names"""

    def __init__(self) -> None:
        super().__init__(message="Label names must be unique")


class DuplicateHotkeysException(InvalidProjectDataException):
    """Error raised when project data contains labels with duplicate hotkeys"""

    def __init__(self) -> None:
        super().__init__(message="Label hotkeys must be unique")


class DuplicateLabelColorsException(InvalidProjectDataException):
    """Error raised when project data contains labels with duplicate colors"""

    def __init__(self) -> None:
        super().__init__(message="Label colors must be unique")


class MultiTaskLabelGroupException(InvalidProjectDataException):
    """
    Error raised when project data contains a label group that spans across multiple tasks

    :param group_name: Name of the label group
    """

    def __init__(self, group_name: str) -> None:
        message = (
            f"The label group '{group_name}' is used in multiple tasks, but "
            f"label groups can only apply to a single task."
        )
        super().__init__(
            message=message,
        )


class MismatchingParentsInLabelGroupException(InvalidProjectDataException):
    """
    Error raised when project data contains a label group where two or more labels
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
        )


class ReservedLabelNameException(InvalidProjectDataException):
    """
    Error raised when project data contains a user-defined label with a reserved name.
    """

    def __init__(self, label_name: str) -> None:
        message = f"The label name or group '{label_name}' is a reserved name and cannot be assigned manually."
        super().__init__(
            message=message,
        )


class UnsupportedHierarchicalLabelsException(InvalidProjectDataException):
    """
    Error raised when project data contains hierarchical labels in a task that does
    not support them.

    :param task_type: Type of the task containing the labels
    """

    def __init__(self, task_type: TaskType) -> None:
        message = f"Labels for task of type `{task_type}` cannot be hierarchical"
        super().__init__(
            message=message,
        )


class SelfReferencingParentLabelException(InvalidProjectDataException):
    """Error raised when project data contains a label whose parent is the label itself."""

    def __init__(self) -> None:
        message = "The parent of a label cannot be the label itself"
        super().__init__(
            message=message,
        )


class ParentLabelNotFoundException(InvalidProjectDataException):
    """
    Error raised when project data contains a label whose parent can not be found.

    :param task_name: Name of the task containing labels with absent parents
    :param parent_id: ID or name of the parent label
    """

    def __init__(self, task_name: str, parent_id: str) -> None:
        message = f"Could not locate the parent of labels in task `{task_name}`. Parent Label ID `{parent_id}`."
        super().__init__(
            message=message,
        )


class InvalidLabelDeletedException(InvalidProjectDataException):
    """
    Error raised when project data tries to delete a label which does not adhere to the
    label restrictions of a project.
    """

    def __init__(self, reason: str) -> None:
        message = f"One or more labels can not be deleted because of the following reason: {reason}"
        super().__init__(
            message=message,
        )


class UnsupportedTaskTypeForLabelAdditionException(InvalidProjectDataException):
    """
    Error raised when  project data attempts to add a new label for a task
    of a type that does not support such kind of operation.

    :param label_name: Name of the new label
    :param task_type: Type of the task for which the label addition is requested
    """

    def __init__(self, label_name: str, task_type: TaskType) -> None:
        supported_types = [tt for tt in TaskType if tt.is_trainable and not tt.is_anomaly]
        message = (
            f"Cannot add a new label `{label_name}` to a task node of type {task_type}. "
            f"The supported types are: {supported_types}"
        )
        super().__init__(
            message=message,
        )


class LocalGlobalLabelAdditionException(InvalidProjectDataException):
    """
    Error raised when  project data attempts to add a new label to a local task
    followed by a global one.

    :param label_name: Name of the new label
    :param task_title: Name of the task where the local label is added
    :param next_task_title: Name of the global task following the local one
    """

    def __init__(self, label_name: str, task_title: str, next_task_title: str) -> None:
        message = (
            f"Cannot add new label `{label_name}` to task `{task_title}` "
            f"because it is a local task followed by a global one ({next_task_title}) "
            f"and such an operation is not supported yet."
        )
        super().__init__(
            message=message,
        )


class PurgeOptimizedModelException(Exception):
    """
    Error raised when a purge operation is attempted on an optimized model.
    """

    def __init__(self) -> None:
        super().__init__(
            "Archiving an optimized model is not allowed. The archive operation is only allowed on base models.",
        )


class PurgeActiveModelException(Exception):
    """
    Error raised when a purge operation is attempted on the active model.
    """

    def __init__(self) -> None:
        super().__init__(
            "Archiving the active model is not allowed.",
        )


class PurgeLatestModelException(Exception):
    """
    Error raised when a purge operation is attempted on the latest model in a model group.
    """

    def __init__(self) -> None:
        super().__init__(
            "Archiving the latest model in a model group is not allowed.",
        )


class SDKModelNotFoundException(Exception):
    """
    Error raised when a model couldn't be found.
    """

    def __init__(self, id_: ID) -> None:
        super().__init__(
            f"Model with ID {id_} could not be found.",
        )


class WrongNumberOfNodesException(Exception):
    """
    Error raised a graph edge is made with wrong number of nodes (other than 2).
    """

    def __init__(self) -> None:
        super().__init__(
            "One of the edges of the graph has a wrong number of nodes.",
        )


class DuplicateEdgeInGraphException(Exception):
    """
    Error raised when a graph edge is made with duplicate edges.
    """

    def __init__(self) -> None:
        super().__init__(
            "The provided graph contains a duplicate edge.",
        )


class IncorrectNodeNameInGraphException(Exception):
    """
    Error raised when a graph edge has an incorrect node name.
    """

    def __init__(self) -> None:
        super().__init__("One of the edges of the graph has an incorrect name.")


class NodeNameNotInLabelsException(Exception):
    """
    Error raised when a node name is not in the list of labels
    """

    def __init__(self) -> None:
        super().__init__("One of the node names is not in the list of labels.")


class NodePositionIsOutOfBoundsException(Exception):
    """
    Error raised when a node's position is out of bounds.
    """

    def __init__(self) -> None:
        super().__init__("One of the node's position is out of bounds.")

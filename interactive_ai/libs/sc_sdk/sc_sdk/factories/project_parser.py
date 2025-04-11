# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

"""Parser interfaces to build/update projects"""

from abc import ABCMeta, abstractmethod

from sc_sdk.entities.label import Domain
from sc_sdk.entities.model_template import TaskType

from geti_types import ID

DOMAINS_WITH_EMPTY_LABEL = [
    Domain.CLASSIFICATION,
    Domain.DETECTION,
    Domain.SEGMENTATION,
    Domain.INSTANCE_SEGMENTATION,
    Domain.ROTATED_DETECTION,
]

DOMAIN_TO_EMPTY_LABEL_NAME = {
    Domain.CLASSIFICATION: "No class",
    Domain.DETECTION: "No object",
    Domain.SEGMENTATION: "Empty",
    Domain.INSTANCE_SEGMENTATION: "Empty",
    Domain.ROTATED_DETECTION: "No object",
}


class ProjectParser(metaclass=ABCMeta):
    """
    Interface for parsers that can read and decode the information necessary to create
    a project from a specific data source and format.

    Parsers enable access to such information in a framework-agnostic way, that
    abstracts away the internal structure and details of different formats.
    """

    @abstractmethod
    def get_project_name(self) -> str:
        """
        Get the name of the project.

        :return: Project name as a string
        """

    @abstractmethod
    def get_connections(self) -> tuple[tuple[str, str], ...]:
        """
        Get the list of connections that determine the topology of the task chain.

        :return: Tuple of tuples (<from>, <to>), where <from> are <to> the names of
        the connected source and destination task nodes, respectively
        """

    @abstractmethod
    def get_tasks_names(self) -> tuple[str, ...]:
        """
        Get the names of the task nodes that compose the project.

        The names can be arbitrary, but must be consistent with the input of other
        methods such as get_task_type_by_name().
        Dataset and flow control tasks must be included where applicable.

        :return: Tuple (unordered) of names of the task nodes in the project
        """

    @abstractmethod
    def get_task_type_by_name(self, task_name: str) -> TaskType:
        """
        Get the type of a task node in the project given its name.

        The method should only be called on existing tasks; else behavior is unspecified

        :param task_name: Name of the task node
        :return: Type of the task node
        """

    @abstractmethod
    def get_custom_labels_names_by_task(self, task_name: str) -> tuple[str, ...]:
        """
        Get the names of the labels defined in a task node.

        This method should only return the names of custom labels (e.g. explicitly
        created by the user), NOT the ones that can be automatically determined
        by the task/group type information (empty labels, anomaly labels, ...).

        The method should only be called on existing tasks; else behavior is unspecified

        :param task_name: Name of the task node
        :return: Tuple (unordered) of names of the custom labels defined in a task
        """

    @abstractmethod
    def get_label_group_by_name(self, task_name: str, label_name: str) -> str:
        """
        Get the name of the label group that contains a certain label.

        If the input data source does not have a notion of groups as in Geti, the
        method should return an arbitrary default name.
        In any case, labels in the same task node and with the same group name will
        be considered to be mutually exclusive (multiclass).
        Conversely, multilabel relations are modeled with different groups.

        The method should only be called on existing tasks and labels; else the
        behavior is unspecified.

        :param task_name: Name of the task where the label is defined
        :param label_name: Name of the label
        :return: Name of the group containing the label
        """

    @abstractmethod
    def get_label_hotkey_by_name(self, task_name: str, label_name: str) -> str:
        """
        Get the hotkey to associate with a certain label.

        If the label is not mapped to a hotkey, or such information is unknown, the
        method shall return an empty string.

        The method should only be called on existing tasks and labels; else the
        behavior is unspecified.

        :param task_name: Name of the task where the label is defined
        :param label_name: Name of the label
        :return: Hotkey of the label, if any, or an empty string
        """

    @abstractmethod
    def get_label_color_by_name(self, task_name: str, label_name: str) -> str:
        """
        Get the hex color (e.g. '#f3c3ed') to use for a certain label in the UI.

        If the label is not mapped to a color, or such information is unknown, the
        method shall return an empty string.

        The method should only be called on existing tasks and labels; else the
        behavior is unspecified.

        :param task_name: Name of the task where the label is defined
        :param label_name: Name of the label
        :return: Color of the label (hex string), if any, or an empty string
        """

    @abstractmethod
    def get_label_parent_by_name(self, task_name: str, label_name: str) -> str:
        """
        Get the name of the parent label for a given label.

        If the label does not have a parent, the method shall return an empty string.
        The parent label can exist either in the same task (e.g. in the case of
        intra-task hierarchical labels) or in the immediately previous vision task
        (e.g. in the case of task-chain projects).

        The method should only be called on existing tasks and labels; else the
        behavior is unspecified.

        :param task_name: Name of the task where the label is defined
        :param label_name: Name of the label
        :return: Name of the parent label, if any, or an empty string
        """

    @abstractmethod
    def get_keypoint_structure_data(self, task_name: str) -> dict[str, list]:
        """
        Get the keypoint structure from the project pipeline. It is found in the task dictionary.
        The data contains the fields:
        - edges
        - positions

        This method should only be for the keypoint detection task, otherwise the behavior is unspecified.

        :param task_name: Name of the task node
        :return: A dictionary defining the structure of the keypoints
        """


class ProjectUpdateParser(ProjectParser, metaclass=ABCMeta):
    """
    Interface for parsers that can read and decode the information necessary to update
    a project from a specific data source and format.

    Parsers enable access to such information in a framework-agnostic way, that
    abstracts away the internal structure and details of different formats.
    """

    @abstractmethod
    def get_connections(self) -> tuple[tuple[ID, ID], ...]:
        """
        Get the list of connections that determine the topology of the task chain.

        :return: Tuple of tuples (<from>, <to>), where <from> are <to> the IDs of
        the connected source and destination task nodes, respectively
        """

    @abstractmethod
    def get_task_id_by_name(self, task_name: str) -> ID:
        """
        Get the ID of a task node given its name

        :return: ID of the task node
        """

    @abstractmethod
    def get_label_id_by_name(self, task_name: str, label_name: str) -> ID | None:
        """
        Get the ID of a label given its name and the one of its task.

        If the label does not have an ID (e.g. because new) the method returns None.

        :param task_name: Name of the task where the label is defined
        :param label_name: Name of the label
        :return: ID of the label, if any, or None
        """

    @abstractmethod
    def get_added_labels_names_by_task(self, task_name: str) -> tuple[str, ...]:
        """
        Get the names of the labels to add to a given task in the update operation.

        The method should only be called on existing tasks; else behavior is unspecified

        :param task_name: Name of the task node
        :return: Names of the labels to add to the task
        """

    @abstractmethod
    def get_deleted_labels_names_by_task(self, task_name: str) -> tuple[str, ...]:
        """
        Get the names of the labels to delete from a given task in the update operation.

        The returned labels should already exist in the task.

        The method should only be called on existing tasks; else behavior is unspecified

        :param task_name: Name of the task node
        :return: Names of the labels to delete from the task
        """

    @abstractmethod
    def get_revisit_state_by_label_name(self, task_name: str, label_name: str) -> bool:
        """
        Get the 'revisit state' of an added label, that is whether the user should
        re-review previously annotated media that may also contain the new label.

        The method should only be called for labels added in this update operation;
        the behavior is otherwise unspecified.

        :param task_name: Name of the task node
        :param label_name: Name of the added label
        :return: True if existing annotations should be revisited, False otherwise
        """

    @abstractmethod
    def get_keypoint_structure_data(self, task_name: str) -> dict[str, list]:
        """
        Get the keypoint structure from the project pipeline. It is found in the task dictionary.
        The data contains the fields:
        - edges
        - positions

        This method should only be for the keypoint detection task, otherwise the behavior is unspecified.

        :param task_name: Name of the task node
        :return: A dictionary defining the structure of the keypoints
        """


class ProjectParserInternalError(RuntimeError):
    """
    Exception that can be raised if an error occurs while parsing already validated
    project data, and the root cause is likely a defect in the parser logic.
    """

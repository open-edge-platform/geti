# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines the format agnostic project creation and update validators."""

import abc
from abc import abstractmethod
from collections import defaultdict
from typing import TYPE_CHECKING, Generic, TypeVar

from iai_core.entities.model_template import TaskType
from iai_core.factories.project_parser import DOMAIN_TO_EMPTY_LABEL_NAME, ProjectParser, ProjectUpdateParser
from iai_core.utils.exceptions import (
    BadNumberOfConnectionsException,
    BadNumberOfLabelsException,
    DuplicateEdgeInGraphException,
    DuplicateHotkeysException,
    DuplicateLabelNamesException,
    DuplicateTaskNamesException,
    EmptyProjectNameException,
    IncorrectNodeNameInGraphException,
    InvalidLabelDeletedException,
    LocalGlobalLabelAdditionException,
    MismatchingParentsInLabelGroupException,
    MultiTaskLabelGroupException,
    NodeNameNotInLabelsException,
    NodePositionIsOutOfBoundsException,
    NoTasksConnectionsException,
    NoTasksInProjectException,
    ParentLabelNotFoundException,
    ReservedLabelNameException,
    SelfReferencingParentLabelException,
    TooManySinkTasksException,
    TooManySourceTasksException,
    UnconnectedTasksException,
    UnsupportedHierarchicalLabelsException,
    UnsupportedTaskTypeForLabelAdditionException,
    WrongNumberOfNodesException,
)

if TYPE_CHECKING:
    from iai_core.entities.label import Domain


ParserT = TypeVar("ParserT", bound=ProjectParser)


class ProjectValidator(Generic[ParserT], metaclass=abc.ABCMeta):
    """
    Base class for ProjectCreationValidator and ProjectUpdateValidator.
    """

    def validate(self, parser: ParserT) -> None:
        """
        Validate project data against specific constraints on certain
        properties (no duplicate task titles or label names, valid pipeline
        connections, valid relations between labels, etc.)

        :param parser: A parser instance that can read and decode the information necessary to create/update a project
        """
        if not parser.get_project_name().strip():
            raise EmptyProjectNameException

        if not parser.get_tasks_names():
            raise NoTasksInProjectException

        self._validate_task_names(parser)

        self._validate_connections(parser)

        self._validate_labels_number(parser)
        self._validate_label_uniqueness(parser)
        self._validate_parent_labels(parser)
        self._validate_label_groups(parser)
        self._validate_empty_labels(parser)
        self._validate_keypoint_structure(parser)

    @classmethod
    def _validate_task_names(cls, parser: ParserT) -> None:
        """
        Verifies that the project data contains valid task names

        :param parser: A parser instance that can read and decode the information necessary to create a project
        :raises DuplicateTaskNamesException: In case the pipeline contains duplicate task titles
        """
        task_names = parser.get_tasks_names()

        if len(task_names) > len(set(task_names)):
            raise DuplicateTaskNamesException

    @classmethod
    def _validate_label_groups(cls, parser: ParserT) -> None:
        """
        Validates the label groups

        Checks:
        - all the labels in the same group belong to the same task
        - all the labels in the same group have the same parent
          (equivalently, an ancestor label can't be in the same group of any descendant)

        Does not check:
        - each group contains at most one empty label
          (ProjectParser does not return empty labels, should be validated in format-specific parsers)

        NOTE: This hinges on the assumption that task_titles are unique.

        :param parser: A parser instance that can read and decode the information necessary to create a project
        :raises MultiTaskLabelGroupException: if any group is used across multiple tasks
        :raises MismatchingParentsInLabelGroupException: if there is any pair of label
            within the same group with different parents
        """
        unique_task_names_by_group_name: dict[str, set[str]] = defaultdict(set)
        unique_label_parents_by_group_name: dict[str, set[str]] = defaultdict(set)
        for task_name in parser.get_tasks_names():
            for label_name in parser.get_custom_labels_names_by_task(task_name=task_name):
                group_name = parser.get_label_group_by_name(task_name, label_name)
                parent_id = parser.get_label_parent_by_name(task_name, label_name)
                unique_task_names_by_group_name[group_name].add(task_name)
                if parent_id:
                    unique_label_parents_by_group_name[group_name].add(parent_id)

        for group_name, _ in unique_task_names_by_group_name.items():
            if len(unique_task_names_by_group_name[group_name]) > 1:
                raise MultiTaskLabelGroupException(group_name=group_name)

            if len(unique_label_parents_by_group_name[group_name]) > 1:
                raise MismatchingParentsInLabelGroupException(group_name=group_name)

    @classmethod
    def _validate_empty_labels(cls, parser: ParserT) -> None:
        """
        Validates that user defined label names do not include the name of the empty
        label for that domain

        :param parser: A parser instance that can read and decode the information necessary to create a project
        :raises ReservedLabelNameException: if any label has the same name of the label
            of the empty one for the same domain
        """
        for task_name in parser.get_tasks_names():
            task_domain: Domain = parser.get_task_type_by_name(task_name).domain
            empty_label_name = DOMAIN_TO_EMPTY_LABEL_NAME.get(task_domain, None)
            if empty_label_name is None:
                continue
            for label_name in parser.get_custom_labels_names_by_task(task_name=task_name):
                if empty_label_name in (label_name, parser.get_label_group_by_name(task_name, label_name)):
                    raise ReservedLabelNameException(label_name=empty_label_name)

    @classmethod
    @abstractmethod
    def _validate_keypoint_structure(cls, parser: ParserT) -> None:
        """
        Validates that a user defined label graph edge has exactly 2 nodes, node names match with existing labels,
        and has no duplicate edges

        This method must be run after labels validation since it assumes that its labels param is valid.

        :param parser: A parser instance that can read and decode the information necessary to create a project
        :raises WrongNumberOfNodesException: if an edge does not have 2 vertices
        :raises IncorrectNodeNameInGraphException: if an edge has an incorrect name
        :raises DuplicateEdgeInGraphException: if the graph contains a duplicate edge
        :raises NodeNameNotInLabelsException: if a node name does not match any of the label names
        :raises NodePositionIsOutOfBoundsException: if a node is out of bounds (not in the range [0.0, 1.0])
        """

    @classmethod
    @abstractmethod
    def _validate_connections(cls, parser: ParserT) -> None:
        """
        Verifies that the project data contains valid connections
        between the tasks.

        Checks:
        - the number of edges must be the same as the number of nodes minus one
        - there must be exactly one source node
        - there must be exactly one sink node
        - all the tasks must have at least one connection

        :param parser: A parser instance that can read and decode the information necessary to create a project
        :raises NoTasksConnectionsException: if there are no connections
        :raises BadNumberOfConnectionsException: if the number of connections is wrong
        :raises TooManySourceTasksException: if there are too many tasks that are
            source nodes in the graph
        :raises TooManySinkTasksException: if there are too many tasks that are
            sink nodes in the graph
        :raises UnconnectedTasksException: if there are tasks that are isolated nodes
            in the graph
        """

    @classmethod
    @abstractmethod
    def _validate_labels_number(cls, parser: ParserT) -> None:
        """
        Validates that each task has a proper number of labels.

        No labels should be provided for dataset and flow control tasks.
        On creation for anomaly tasks, no labels should be provided (two labels, i.e. anomalous
        and non-anomalous, are created automatically).
        On update for anomaly tasks, two labels (anomalous and normal) should be provided.
        Local vision tasks need at least one label to be explicitly provided (an empty
        one will be added automatically).
        Global vision tasks need at least two top-level labels; the empty label of
        binary classification (if any) must be defined by the user like the normal one.

        :param parser: A parser instance that can read and decode the information necessary to create a project
        :raises BadNumberOfLabelsException: if any task does not have
            a proper number of labels
        """

    @classmethod
    @abstractmethod
    def _validate_label_uniqueness(cls, parser: ParserT) -> None:
        """
        Validates that certain label properties are unique across all labels

        Checks:
        - The label names must be unique
        - The label hotkeys must be unique
        - The label colors must be unique

        :param parser: A parser instance that can read and decode the information necessary to create a project
        """

    @classmethod
    @abstractmethod
    def _validate_parent_labels(cls, parser: ParserT) -> None:
        """
        Validates that the `parent_id` property of each label is valid

        Checks:
        - The parent can be only non-null for classification tasks
        - The parent label cannot be the label itself (i.e. must be a different label)
        - The parent label exists in the same tasks or the parent task

        Does not check:
        - The parent label is not empty: empty labels are not accessible from the parser

        :param parser: A parser instance that can read and decode the information necessary to create a project
        :raises UnsupportedHierarchicalLabelsException: if hierarchical labels are
            present and the task does not support it
        :raises ParentLabelNotFoundException: if the parent label cannot be found
            neither in the same task nor the parent task
        """


class ProjectCreationValidator(ProjectValidator[ProjectParser]):
    @classmethod
    def _validate_connections(cls, parser: ProjectParser) -> None:
        connections = parser.get_connections()
        to_list = {connection[0] for connection in connections}
        from_list = {connection[1] for connection in connections}
        task_names = parser.get_tasks_names()
        num_tasks = len(task_names)

        if len(connections) == 0:
            raise NoTasksConnectionsException

        if not len(connections) == num_tasks - 1:
            raise BadNumberOfConnectionsException

        if not len(to_list) == num_tasks - 1:
            raise TooManySourceTasksException

        if not len(from_list) == num_tasks - 1:
            raise TooManySinkTasksException

        # tasks are referred by name
        if to_list | from_list != set(task_names):
            raise UnconnectedTasksException

    @classmethod
    def _validate_labels_number(cls, parser: ProjectParser) -> None:
        task_names = parser.get_tasks_names()
        for task_name in task_names:
            task_type: TaskType = parser.get_task_type_by_name(task_name)
            label_names: set[str] = set(parser.get_custom_labels_names_by_task(task_name))
            num_labels = len(label_names)
            if task_type.is_trainable:
                if task_type.is_anomaly:  # vision anomaly
                    expected_num_labels = 0
                    if num_labels != expected_num_labels:
                        raise BadNumberOfLabelsException(
                            task_name=task_name,
                            num_labels=num_labels,
                            expected_num_labels_str=str(expected_num_labels),
                        )
                elif task_type.is_global:  # vision global, non-anomaly
                    # Global tasks can have internal hierarchies; we must ensure that
                    # the top-level contains at least two labels. Top-level labels
                    # are the ones whose parent is in another task or missing.
                    num_top_level_labels = sum(
                        parser.get_label_parent_by_name(task_name, label_name) not in label_names
                        for label_name in label_names
                    )
                    if num_top_level_labels < 2:
                        raise BadNumberOfLabelsException(
                            task_name=task_name,
                            num_labels=num_top_level_labels,
                            expected_num_labels_str="at least two top-level ones",
                        )
                # vision local, non-anomaly
                elif num_labels < 1:
                    raise BadNumberOfLabelsException(
                        task_name=task_name,
                        num_labels=num_labels,
                        expected_num_labels_str="at least one",
                    )
            # dataset/flow
            elif num_labels > 0:
                raise BadNumberOfLabelsException(
                    task_name=task_name,
                    num_labels=num_labels,
                    expected_num_labels_str="none",
                )

    @classmethod
    def _validate_label_uniqueness(cls, parser: ProjectParser) -> None:
        label_names: list[str] = []
        label_hotkeys: list[str] = []
        label_colors: list[str] = []
        for task_name in parser.get_tasks_names():
            label_names_for_task = parser.get_custom_labels_names_by_task(task_name=task_name)
            label_names.extend(label_names_for_task)
            for label_name in label_names_for_task:
                hotkey = parser.get_label_hotkey_by_name(task_name, label_name)
                color = parser.get_label_color_by_name(task_name, label_name)
                if hotkey:
                    label_hotkeys.append(hotkey)
                if color:
                    label_colors.append(color)

        if len(label_names) > len(set(label_names)):
            raise DuplicateLabelNamesException
        if len(label_hotkeys) > len(set(label_hotkeys)):
            raise DuplicateHotkeysException

    @classmethod
    def _validate_parent_labels(cls, parser: ProjectParser) -> None:
        unique_external_parent_labels_by_task_name: dict[str, set[str]] = defaultdict(set)
        for task_name in parser.get_tasks_names():
            task_type: TaskType = parser.get_task_type_by_name(task_name)
            task_label_names_set: set[str] = set(parser.get_custom_labels_names_by_task(task_name))
            for label_name in task_label_names_set:
                parent_label_name = parser.get_label_parent_by_name(task_name, label_name)
                if parent_label_name:
                    # It is not allowed to specify a parent for tasks other than classification
                    if task_type != TaskType.CLASSIFICATION:
                        raise UnsupportedHierarchicalLabelsException(task_type=task_type)
                    # The parent must be a different label
                    if parent_label_name == label_name:
                        raise SelfReferencingParentLabelException
                    if parent_label_name in task_label_names_set:
                        # Parent label found in the current task
                        continue
                    unique_external_parent_labels_by_task_name[task_name].add(parent_label_name)

        # Find parent labels in parent tasks
        cls.__validate_parent_labels_in_parent_task(parser, unique_external_parent_labels_by_task_name)

    @classmethod
    def __validate_parent_labels_in_parent_task(
        cls, parser: ProjectParser, unique_external_parent_labels_by_task_name: dict[str, set[str]]
    ) -> None:
        """
        Verifies that the parent labels (not found in the same task)
        can be found in a parent task.

        Note: the difference between the 'previous' task, i.e. the immediate ancestor, and the 'parent' task,
        which is the first ancestor vision task with labels.

        :param parser: A parser instance that can read and decode the information necessary to create a project
        :raises ParentLabelNotFoundException: if the parent label is an empty one
        """
        prev_task_dict = {conn[1]: conn[0] for conn in parser.get_connections()}
        for task_name, parent_labels_set in unique_external_parent_labels_by_task_name.items():
            parent_labels_found = [False] * len(parent_labels_set)
            previous_task_name = prev_task_dict.get(task_name, "")
            # find parent task with labels
            while previous_task_name:
                previous_task_label_names: set[str] = set(parser.get_custom_labels_names_by_task(previous_task_name))
                if previous_task_label_names:
                    # If there are labels in the parent task
                    # we check that all the external parent labels are among them.
                    for i, parent_label_name in enumerate(parent_labels_set):
                        if parent_label_name in previous_task_label_names:
                            parent_labels_found[i] = True
                    break
                previous_task_name = prev_task_dict.get(previous_task_name, "")
            if not all(parent_labels_found):
                raise ParentLabelNotFoundException(
                    task_name=task_name,
                    parent_id=next(
                        parent_label_name
                        for parent_label_name, is_found in zip(parent_labels_set, parent_labels_found)
                        if not is_found
                    ),
                )

    @classmethod
    def _validate_keypoint_structure(cls, parser: ProjectParser) -> None:
        """
        Validates that a user defined label graph edge has exactly 2 nodes, node names match with existing labels,
        and has no duplicate edges

        This method must be run after labels validation since it assumes that its labels param is valid.

        :param parser: A parser instance that can read and decode the information necessary to create a project
        :raises WrongNumberOfNodesException: if an edge does not have 2 vertices
        :raises IncorrectNodeNameInGraphException: if an edge has an incorrect name
        :raises DuplicateEdgeInGraphException: if the graph contains a duplicate edge
        :raises NodeNameNotInLabelsException: if a node name does not match any of the label names
        :raises NodePositionIsOutOfBoundsException: if a node is out of bounds (not in the range [0.0, 1.0])
        """
        duplicate_list = []
        for task_name in parser.get_tasks_names():
            keypoint_structure = parser.get_keypoint_structure_data(task_name=task_name)
            if not keypoint_structure:
                continue
            label_names = parser.get_custom_labels_names_by_task(task_name=task_name)
            edges = keypoint_structure["edges"]
            for edge in edges:
                nodes = edge["nodes"]
                if len(nodes) != 2:
                    raise WrongNumberOfNodesException
                if nodes[0] not in label_names or nodes[1] not in label_names:
                    raise IncorrectNodeNameInGraphException
                if set(nodes) in duplicate_list:
                    raise DuplicateEdgeInGraphException
                duplicate_list.append(set(nodes))

            positions = keypoint_structure["positions"]
            for position in positions:
                if position["label"] not in label_names:
                    raise NodeNameNotInLabelsException
                if not 0 <= position["x"] <= 1 or not 0 <= position["y"] <= 1:
                    raise NodePositionIsOutOfBoundsException


class ProjectUpdateValidator(ProjectValidator[ProjectUpdateParser]):
    def validate(self, parser: ProjectUpdateParser) -> None:
        """
        Validate project update data against specific constraints on certain
        properties (no duplicate task titles or label names, valid pipeline
        connections, valid relations between labels, etc.)

        :param parser: A parser instance that can read and decode the information necessary to update a project
        :raises InvalidProjectDataException: In case of a missing data, name
            collisions for certain properties, a malformed/invalid task relations or
            invalid label relations
        """
        super().validate(parser)
        self._validate_label_deletion(parser)
        self._validate_label_data_for_addition(parser)

    @classmethod
    def _validate_connections(cls, parser: ProjectUpdateParser) -> None:
        connections = parser.get_connections()
        to_list = {connection[0] for connection in connections}
        from_list = {connection[1] for connection in connections}
        task_names = parser.get_tasks_names()
        num_tasks = len(task_names)

        if len(connections) == 0:
            raise NoTasksConnectionsException

        if not len(connections) == num_tasks - 1:
            raise BadNumberOfConnectionsException

        if not len(to_list) == num_tasks - 1:
            raise TooManySourceTasksException

        if not len(from_list) == num_tasks - 1:
            raise TooManySinkTasksException

        # tasks are referred by id
        task_ids = [parser.get_task_id_by_name(task_name) for task_name in task_names]
        if to_list | from_list != set(task_ids):
            raise UnconnectedTasksException

    @classmethod
    def _validate_labels_number(cls, parser: ProjectUpdateParser) -> None:
        task_names = parser.get_tasks_names()
        for task_name in task_names:
            task_type: TaskType = parser.get_task_type_by_name(task_name)
            label_names: set[str] = set(parser.get_custom_labels_names_by_task(task_name))
            deleted_labels: set[str] = set(parser.get_deleted_labels_names_by_task(task_name))
            num_labels = len(label_names)
            if task_type.is_trainable:
                if task_type.is_anomaly:  # vision anomaly
                    expected_num_labels = 2
                    if num_labels != expected_num_labels:
                        raise BadNumberOfLabelsException(
                            task_name=task_name,
                            num_labels=num_labels,
                            expected_num_labels_str=str(expected_num_labels),
                        )
                elif task_type.is_global:  # vision global, non-anomaly
                    # Global tasks can have internal hierarchies; we must ensure that
                    # the top-level contains at least two labels. Top-level labels
                    # are the ones whose parent is in another task or missing.
                    task_label_ids: set[str | None] = {
                        parser.get_label_id_by_name(task_name, label_name) for label_name in label_names
                    }
                    task_label_names_and_ids = label_names | task_label_ids
                    num_top_level_labels = sum(
                        parser.get_label_parent_by_name(task_name, label_name) not in task_label_names_and_ids
                        for label_name in label_names
                        if label_name not in deleted_labels
                    )
                    if num_top_level_labels < 2:
                        raise BadNumberOfLabelsException(
                            task_name=task_name,
                            num_labels=num_top_level_labels,
                            expected_num_labels_str="at least two top-level ones",
                        )
                # vision local, non-anomaly
                elif num_labels < 1:
                    raise BadNumberOfLabelsException(
                        task_name=task_name,
                        num_labels=num_labels,
                        expected_num_labels_str="at least one",
                    )
            # dataset/flow
            elif num_labels > 0:
                raise BadNumberOfLabelsException(
                    task_name=task_name,
                    num_labels=num_labels,
                    expected_num_labels_str="none",
                )

    @classmethod
    def _validate_label_uniqueness(cls, parser: ProjectUpdateParser) -> None:
        label_names: list[str] = []
        label_hotkeys: list[str] = []
        label_colors: list[str] = []
        for task_name in parser.get_tasks_names():
            label_names_for_task = parser.get_custom_labels_names_by_task(task_name=task_name)
            deleted_label_names: set[str] = set(parser.get_deleted_labels_names_by_task(task_name))
            label_names.extend(
                [label_name for label_name in label_names_for_task if label_name not in deleted_label_names]
            )
            for label_name in label_names_for_task:
                hotkey = parser.get_label_hotkey_by_name(task_name, label_name)
                color = parser.get_label_color_by_name(task_name, label_name)
                if hotkey and label_name not in deleted_label_names:
                    label_hotkeys.append(hotkey)
                if color and label_name not in deleted_label_names:
                    label_colors.append(color)

        if len(label_names) > len(set(label_names)):
            raise DuplicateLabelNamesException
        if len(label_hotkeys) > len(set(label_hotkeys)):
            raise DuplicateHotkeysException

    @classmethod
    def _validate_parent_labels(cls, parser: ProjectUpdateParser) -> None:
        unique_external_parent_labels_by_task_id: dict[str, set[str]] = defaultdict(set)
        for task_name in parser.get_tasks_names():
            # In case of update parser the task connections are returned as task IDs
            task_id = parser.get_task_id_by_name(task_name)
            task_type: TaskType = parser.get_task_type_by_name(task_name)
            task_label_names_set: set[str] = set(parser.get_custom_labels_names_by_task(task_name))

            # This block introduces task_label_names_and_ids_set
            # to check label parents against it due to RestProjectUpdateParser
            # returning parents label ids instead of names from the `get_label_parent_by_name` method
            task_label_ids_set = {
                parser.get_label_id_by_name(task_name, label_name) for label_name in task_label_names_set
            }
            task_label_names_and_ids_set = task_label_names_set | task_label_ids_set

            for label_name in task_label_names_set:
                label_id = parser.get_label_id_by_name(task_name, label_name)
                parent_label_name = parser.get_label_parent_by_name(task_name, label_name)
                if parent_label_name:
                    # It is not allowed to specify a parent for tasks other than classification
                    if task_type != TaskType.CLASSIFICATION:
                        raise UnsupportedHierarchicalLabelsException(task_type=task_type)
                    # The parent must be a different label
                    if parent_label_name in (label_name, label_id):
                        raise SelfReferencingParentLabelException
                    if parent_label_name in task_label_names_and_ids_set:
                        # Parent label found in the current task
                        continue
                    unique_external_parent_labels_by_task_id[task_id].add(parent_label_name)

        # Find parent labels in parent tasks
        cls.__validate_parent_labels_in_parent_task(parser, unique_external_parent_labels_by_task_id)  # type: ignore

    @classmethod
    def _validate_label_deletion(cls, parser: ProjectUpdateParser) -> None:
        """
        Validates that in case of label deletion the label constraints are not violated.

        :param parser: A parser instance that can read and decode the information necessary to update a project
        :raises InvalidLabelDeletedException: if label deletion produces an invalid label
        group for the task
        """
        for task_name in parser.get_tasks_names():
            existing_labels: set[str] = set(parser.get_custom_labels_names_by_task(task_name))
            deleted_labels: set[str] = set(parser.get_deleted_labels_names_by_task(task_name))
            if not existing_labels or not deleted_labels:
                continue
            task_type: TaskType = parser.get_task_type_by_name(task_name)
            if deleted_labels and task_type.is_anomaly:
                raise InvalidLabelDeletedException(reason="Can not delete labels in an anomaly project.")
            if existing_labels == deleted_labels:
                raise InvalidLabelDeletedException(reason="Can not delete all labels.")

    @classmethod
    def _validate_label_data_for_addition(cls, parser: ProjectUpdateParser) -> None:
        """
        Validates that in case of label addition the label constraints are not violated.

        :param parser: A parser instance that can read and decode the information necessary to update a project
        :raises InvalidLabelAddedException: if label addition produces an invalid label
        group for the task
        """
        for task_name in parser.get_tasks_names():
            added_labels = parser.get_added_labels_names_by_task(task_name)
            if not added_labels:
                continue
            # The group, if specified, must not belong to other tasks
            for group_name in {parser.get_label_group_by_name(task_name, label_name) for label_name in added_labels}:
                cls._validate_group_belongs_to_task(task_name, group_name, parser)
            # The task must be compatible with label addition
            cls._validate_task_supports_label_addition(added_labels[0], task_name, parser)

    @classmethod
    def _validate_group_belongs_to_task(cls, task_name: str, group_name: str, parser: ProjectUpdateParser) -> None:
        """
        Check that the group specified in the label belongs to the label task node

        :param parser: A parser instance that can read and decode the information necessary to update a project
        :raises MultiTaskLabelGroupException: if the label group belongs to another task
        """
        for other_task_name in parser.get_tasks_names():
            if other_task_name == task_name:
                continue
            for label_name in parser.get_custom_labels_names_by_task(other_task_name):
                label_group_name = parser.get_label_group_by_name(other_task_name, label_name)
                if label_group_name == group_name:
                    raise MultiTaskLabelGroupException(group_name=group_name)

    @classmethod
    def _validate_task_supports_label_addition(
        cls, label_name: str, task_name: str, parser: ProjectUpdateParser
    ) -> None:
        """
        Check that the task is compatible with label addition

        Checks:
        - the task type must support label addition
        - the task cannot be a local one followed by a global one

        :param parser: A parser instance that can read and decode the information necessary to update a project
        :raises UnsupportedTaskTypeForLabelAddition: if task does not support addition
        :raises LocalGlobalLabelAdditionException: if label addition is attempted on
            a local task followed by a global one
        """
        task_type: TaskType = parser.get_task_type_by_name(task_name)
        # Check the TaskType (must be trainable and non-anomaly)
        if not task_type.is_trainable or task_type.is_anomaly:
            raise UnsupportedTaskTypeForLabelAdditionException(
                label_name=label_name,
                task_type=task_type,
            )

        # Adding labels to a local task followed by global one is not supported
        if task_type.is_local:
            task_name_by_task_id = {
                parser.get_task_id_by_name(task_name): task_name for task_name in parser.get_tasks_names()
            }
            next_task_dict = {
                task_name_by_task_id[conn[0]]: task_name_by_task_id[conn[1]] for conn in parser.get_connections()
            }
            next_task_type: TaskType = TaskType.NULL
            while not next_task_type.is_trainable:
                task_name = next_task_dict.get(task_name, "")
                if task_name:
                    next_task_type = parser.get_task_type_by_name(task_name)
                else:
                    next_task_type = TaskType.NULL
                if next_task_type == next_task_type.NULL:
                    break

            if next_task_type.is_global:
                raise LocalGlobalLabelAdditionException(
                    label_name=label_name,
                    task_title=task_type.name,
                    next_task_title=next_task_type.name,
                )

    @classmethod
    def __validate_parent_labels_in_parent_task(
        cls, parser: ProjectUpdateParser, unique_external_parent_labels_by_task_id: dict[str, set[str]]
    ) -> None:
        """
        Verifies that the parent labels (not found in the same task)
        can be found in a parent task.

        Note: the difference between the 'previous' task, i.e. the immediate ancestor, and the 'parent' task,
        which is the first ancestor vision task with labels.

        :param parser: A parser instance that can read and decode the information necessary to create a project
        :raises ParentLabelNotFoundException: if the parent label is an empty one
        """
        prev_task_dict = {conn[1]: conn[0] for conn in parser.get_connections()}  # IDs in case of ProjectUpdate
        task_id_to_task_name = {
            parser.get_task_id_by_name(task_name): task_name for task_name in parser.get_tasks_names()
        }
        for task_id, parent_label_set in unique_external_parent_labels_by_task_id.items():
            parent_labels_found = [False] * len(parent_label_set)
            previous_task_id = prev_task_dict.get(task_id, "")  # type: ignore[call-overload]
            # find parent task with labels
            while previous_task_id:
                previous_task_label_names: set[str] = set(
                    parser.get_custom_labels_names_by_task(task_id_to_task_name[previous_task_id])
                )

                if previous_task_label_names:
                    # If there are labels in the parent task
                    # we check that all the external parent labels are among them.

                    # This block introduces prev_task_label_names_and_ids_set
                    # to check label parents against it due to RestProjectUpdateParser
                    # returning parents label ids instead of names from the `get_label_parent_by_name` method
                    previous_task_label_ids_set = {
                        parser.get_label_id_by_name(task_id_to_task_name[previous_task_id], label_name)
                        for label_name in previous_task_label_names
                    }
                    prev_task_label_names_and_ids_set = previous_task_label_names | previous_task_label_ids_set
                    for i, parent_label_name in enumerate(parent_label_set):
                        if parent_label_name in prev_task_label_names_and_ids_set:
                            parent_labels_found[i] = True
                    break
                previous_task_id = prev_task_dict.get(previous_task_id, "")
            if not all(parent_labels_found):
                raise ParentLabelNotFoundException(
                    task_name=task_id_to_task_name[task_id],  # type: ignore[index]
                    parent_id=next(
                        parent_label_name
                        for parent_label_name, is_found in zip(parent_label_set, parent_labels_found)
                        if not is_found
                    ),
                )

    @classmethod
    def _validate_keypoint_structure(cls, parser: ProjectUpdateParser) -> None:
        """
        Validates that a user defined label graph edge has exactly 2 nodes, node names match with existing labels,
        and has no duplicate edges

        This method must be run after labels validation since it assumes that its labels param is valid.

        :param parser: A parser instance that can read and decode the information necessary to create a project
        :raises WrongNumberOfNodesException: if an edge does not have 2 vertices
        :raises IncorrectNodeNameInGraphException: if an edge has an incorrect name
        :raises DuplicateEdgeInGraphException: if the graph contains a duplicate edge
        :raises NodeNameNotInLabelsException: if a node name does not match any of the label names
        :raises NodePositionIsOutOfBoundsException: if a node is out of bounds (not in the range [0.0, 1.0])
        """
        duplicate_list = []
        for task_name in parser.get_tasks_names():
            keypoint_structure = parser.get_keypoint_structure_data(task_name=task_name)
            if not keypoint_structure:
                continue
            label_names = list(parser.get_custom_labels_names_by_task(task_name=task_name))
            label_ids = [
                str(parser.get_label_id_by_name(task_name=task_name, label_name=label_name))
                for label_name in label_names
            ]
            labels = label_names + label_ids
            edges = keypoint_structure["edges"]
            for edge in edges:
                nodes = edge["nodes"]
                if len(nodes) != 2:
                    raise WrongNumberOfNodesException
                if nodes[0] not in labels or nodes[1] not in labels:
                    raise IncorrectNodeNameInGraphException
                if set(nodes) in duplicate_list:
                    raise DuplicateEdgeInGraphException
                duplicate_list.append(set(nodes))

            positions = keypoint_structure["positions"]
            for position in positions:
                if position["label"] not in labels:
                    raise NodeNameNotInLabelsException
                if not 0 <= position["x"] <= 1 or not 0 <= position["y"] <= 1:
                    raise NodePositionIsOutOfBoundsException

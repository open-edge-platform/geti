# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the ProjectRestValidator class"""

import logging
import os
from collections.abc import Sequence
from dataclasses import dataclass, fields
from enum import Enum
from typing import Any

import jsonschema

from communication.constants import MAX_NUMBER_OF_CONNECTIONS_IN_CHAIN, MAX_NUMBER_OF_LABELS
from communication.exceptions import (
    BadNumberOfConnectionsException,
    BadNumberOfLabelsException,
    DuplicateEdgeInGraphException,
    DuplicateHotkeysException,
    DuplicateLabelColorsException,
    DuplicateLabelNamesException,
    DuplicateTaskNamesException,
    EmptyParentLabelException,
    EmptyProjectNameException,
    IncorrectNodeNameInGraphException,
    InvalidLabelDeletedException,
    InvalidTaskTypeException,
    MismatchingParentsInLabelGroupException,
    MultipleEmptyLabelsException,
    MultiTaskLabelGroupException,
    NodeNameNotInLabelsException,
    NodePositionIsOutOfBoundsException,
    NoTasksConnectionsException,
    NoTasksInProjectException,
    ParentLabelNotFoundException,
    ReservedLabelNameException,
    SelfReferencingParentLabelException,
    TooManyLabelsException,
    TooManySinkTasksException,
    TooManySourceTasksException,
    TooManyTasksException,
    UnconnectedTasksException,
    UnsupportedHierarchicalLabelsException,
    WrongNumberOfNodesException,
)
from features.feature_flags import FeatureFlag

from geti_fastapi_tools.validation import RestApiValidator
from geti_feature_tools import FeatureFlagProvider
from geti_telemetry_tools import unified_tracing
from iai_core.entities.color import Color
from iai_core.entities.label import Domain
from iai_core.entities.model_template import TaskType
from iai_core.factories.project_parser import DOMAIN_TO_EMPTY_LABEL_NAME

CONNECTIONS = "connections"
EDGES = "edges"
FROM = "from"
GROUP = "group"
ID_ = "id"
IS_EMPTY = "is_empty"
IS_DELETED = "is_deleted"
LABEL = "label"
LABELS = "labels"
KEYPOINT_STRUCTURE = "keypoint_structure"
NAME = "name"
NODES = "nodes"
POSITIONS = "positions"
PARENT_ID = "parent_id"
PIPELINE = "pipeline"
TASK_TYPE = "task_type"
TASKS = "tasks"
TITLE = "title"
TO = "to"

logger = logging.getLogger(__name__)


class OperationType(Enum):
    """
    This Enum represents a type of operation that can be performed on a project
    """

    CREATE = "create"
    UPDATE = "update"


@dataclass
class LabelProperties:
    """
    Class representing those properties of a label (inferred from its REST
    representation) that are subject to additional data validation

    :var name: Name of the label
    :var task_title: Title of the task to which the label belongs
    :var domain: Domain to which the label applies
    :var color: Color of the label
    :var id_: Unique database ID of the label
    :var group: Name of the label group to which the label belongs
    :var is_empty: True if the label represents an empty label, False otherwise
    :var parent_id: Optional name of the parent label, if any
    :var revisit_affected_annotations: Optional, whether to mark the existing
        annotations containing that label as 'to revisit'
    :var is_deleted: whether a label is deleted or not
    """

    name: str
    task_title: str
    domain: Domain
    group: str | None = None
    is_empty: bool = False
    hotkey: str = ""
    color: str = ""
    id: str | None = None
    parent_id: str | None = None
    revisit_affected_annotations: bool | None = None
    is_deleted: bool = False

    @classmethod
    def from_rest_and_task_details(
        cls, data_dict: dict[str, Any], task_title: str, task_type: TaskType
    ) -> "LabelProperties":
        """
        Instantiates a LabelProperties object from a dictionary `data_dict`.
        `data_dict` should contain the REST representation of a Label

        :param data_dict: Dictionary holding the REST representation of the label
        :param task_title: Title of the task to which the label belongs
        :param task_type: Type of the task to which the label belongs
        """
        property_dict: dict[str, Any] = {}
        # We only consider those label properties that are defined in this dataclass,
        # other properties are discarded
        for key, value in data_dict.items():
            if key in [field.name for field in fields(cls)]:
                property_dict[key] = value
        return cls(
            **property_dict,
            task_title=task_title,
            domain=task_type.domain,
        )


class ProjectRestValidator(RestApiValidator):
    def __init__(self) -> None:
        base_dir = os.path.dirname(__file__) + "/../../../../api/schemas/"
        self.create_project_schema = self.load_schema_file_as_dict(base_dir + "projects/requests/post/project.yaml")
        self.update_project_schema = self.load_schema_file_as_dict(base_dir + "projects/requests/put/project.yaml")

    # Static validation
    #
    # These checks are stateless, i.e. they neither involve entities nor data
    # fetched from the repo. They can be performed immediately when a request is received.

    @unified_tracing
    def validate_update_data_statically(self, data: dict) -> None:
        """
        Validate project json data for adherence to the json schema for the
        'update project' endpoint.

        In addition, the data is validated against specific constraints on certain
        properties (no duplicate task titles or label names, valid pipeline
        connections, valid relations between labels, etc.)

        :param data: project json data
        :raises BadRequestException: in case of constraint violations
        :raises jsonschema.exceptions.ValidationError: when data doesn't correspond
            with yaml schema
        """
        jsonschema.validate(data, self.update_project_schema)
        self.validate_all_static_constraints(data, operation=OperationType.UPDATE)

    @unified_tracing
    def validate_creation_data_statically(self, data: dict) -> None:
        """
        Validate project json data for adherence to the json schema for the
        'create project' endpoint.

        In addition, the data is validated against specific constraints on certain
        properties (no duplicate task titles or label names, valid pipeline
        connections, valid relations between labels, etc.)

        :param data: project json data
        :raises BadRequestException: in case of constraint violations
        :raises jsonschema.exceptions.ValidationError: when data doesn't correspond
            with yaml schema
        """
        jsonschema.validate(data, self.create_project_schema)
        self.validate_all_static_constraints(data, operation=OperationType.CREATE)

    @staticmethod
    def validate_all_static_constraints(data: dict[str, Any], operation: OperationType) -> None:
        """
        Performs validation against all available constraints on the pipeline data,
        including the task_titles, connections and label properties.

        :param data: REST request data representing a
        :param operation: The type of operation to be done on the project, for which
            the constraints have to be validated
        :raises BadRequestException: In case of a request with missing data, name
            collisions for certain properties, a malformed/invalid pipeline or
            invalid label relations
        """
        if not data[NAME].strip():
            raise EmptyProjectNameException

        if len(data[PIPELINE][TASKS]) <= 0:
            raise NoTasksInProjectException(operation=operation.name)

        ProjectRestValidator._validate_tasks(data=data)

        ProjectRestValidator._validate_connections(data=data, operation=operation)

        labels = ProjectRestValidator._get_labels_from_rest(data=data)
        if len(labels) > MAX_NUMBER_OF_LABELS:
            raise TooManyLabelsException(MAX_NUMBER_OF_LABELS)
        ProjectRestValidator._validate_labels_number(data=data, operation=operation)
        ProjectRestValidator._validate_label_uniqueness(labels=labels)
        ProjectRestValidator._validate_parent_labels(data=data)
        ProjectRestValidator._validate_label_groups(labels=labels)
        ProjectRestValidator._validate_empty_labels(labels=labels)
        ProjectRestValidator._validate_label_deletion(data=data)
        if FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_KEYPOINT_DETECTION):
            ProjectRestValidator._validate_keypoint_structure(data=data, labels=labels)

    @staticmethod
    def _validate_label_deletion(data: dict[str, Any]) -> None:
        """
        Validates that in case of label deletion the label constraints are not violated.

        :param data: REST request data representing a project
        """
        pipeline_data = data[PIPELINE]
        for task_data in pipeline_data[TASKS]:
            if LABELS not in task_data or len(task_data[LABELS]) == 0:
                continue
            ProjectRestValidator.__validate_task_labels_for_label_deletion(
                label_data=task_data[LABELS], task_type_str=task_data[TASK_TYPE]
            )

    @staticmethod
    def _validate_tasks(data: dict[str, Any]) -> None:
        """
        Verifies that the pipeline in the request data contains valid task titles and task types

        :param data: REST request data representing a project
        :raises DuplicateTaskNamesException: In case the pipeline contains duplicate task titles
        :raises InvalidTaskTypeException: In case the pipeline contains an invalid task type
        """
        task_titles = [task[TITLE] for task in data[PIPELINE][TASKS]]
        task_types = [task[TASK_TYPE].upper() for task in data[PIPELINE][TASKS]]

        if len(task_titles) > len(set(task_titles)):
            raise DuplicateTaskNamesException

        is_keypoint_detection_enabled = FeatureFlagProvider.is_enabled(FeatureFlag.FEATURE_FLAG_KEYPOINT_DETECTION)
        if not is_keypoint_detection_enabled and "KEYPOINT_DETECTION" in task_types:
            raise InvalidTaskTypeException(task_type="KEYPOINT_DETECTION")

    @staticmethod
    def _validate_connections(data: dict[str, Any], operation: OperationType) -> None:
        """
        Verifies that the pipeline in the request data contains valid connections
        between the tasks.

        Note: on creation, the connections refer to the tasks by name. Instead, on
        update the tasks are referred by ID.

        Checks:
        - the number of edges must be the same as the number of nodes minus one
        - there must be exactly one source node
        - there must be exactly one sink node
        - all the tasks must have at least one connection

        :param data: REST request data representing a project
        :param operation: The type of operation to be done on the project, for which
            the constraints have to be validated
        :raises NoTasksConnectionsException: if there are no connections
        :raises BadNumberOfConnectionsException: if the number of connections is wrong
        :raises TooManySourceTasksException: if there are too many tasks that are
            source nodes in the graph
        :raises TooManySinkTasksException: if there are too many tasks that are
            sink nodes in the graph
        :raises UnconnectedTasksException: if there are tasks that are isolated nodes
            in the graph
        """
        connections = data[PIPELINE][CONNECTIONS]
        to_list = [connection["to"] for connection in connections]
        from_list = [connection["from"] for connection in connections]
        num_tasks = len(data[PIPELINE][TASKS])

        if len(connections) == 0:
            raise NoTasksConnectionsException

        if len(connections) > MAX_NUMBER_OF_CONNECTIONS_IN_CHAIN:
            raise TooManyTasksException

        if not len(connections) == num_tasks - 1:
            raise BadNumberOfConnectionsException

        if not len(to_list) == num_tasks - 1:
            raise TooManySourceTasksException

        if not len(from_list) == num_tasks - 1:
            raise TooManySinkTasksException

        if operation == OperationType.CREATE:  # tasks are referred by name
            task_titles = [task[TITLE] for task in data[PIPELINE][TASKS]]
            if set(to_list + from_list) != set(task_titles):
                raise UnconnectedTasksException
        elif operation == OperationType.UPDATE:  # tasks are referred by id
            task_ids = [task[ID_] for task in data[PIPELINE][TASKS]]
            if set(to_list + from_list) != set(task_ids):
                raise UnconnectedTasksException
        else:
            raise NotImplementedError(f"Cannot validate task connections on {operation.name}")

    @staticmethod
    def _validate_label_uniqueness(labels: list[LabelProperties]) -> None:
        """
        Validates that certain label properties are unique across all labels

        Checks:
        - The label names must be unique
        - The label hotkeys must be unique
        - The label colors must be unique

        :param labels: List of LabelProperties, each entry representing the properties
            for a single label that are up for validation
        """

        ProjectRestValidator.__validate_label_name_uniqueness(labels=labels)
        ProjectRestValidator.__validate_label_hotkey_uniqueness(labels=labels)
        # TODO color uniqueness check temporarily disabled (ref CVS-86062)
        # ProjectRestValidator.__validate_label_color_uniqueness(labels=labels)

    @staticmethod
    def __validate_label_name_uniqueness(labels: Sequence[LabelProperties]) -> None:
        """
        Checks if all label names  are unique

        :param labels: List of LabelProperties, each entry representing the properties
        for a single label that are up for validation
        :raises DuplicateLabelNamesException: if there are duplicate label names
        """
        label_names = [label.name for label in labels if not label.is_empty and not label.is_deleted]
        if len(label_names) > len(set(label_names)):
            raise DuplicateLabelNamesException

    @staticmethod
    def __validate_label_hotkey_uniqueness(labels: Sequence[LabelProperties]) -> None:
        """
        Checks if all label hotkeys  are unique

        :param labels: List of LabelProperties, each entry representing the properties
        for a single label that are up for validation
        :raises DuplicateHotkeysException: if there are duplicate label hotkeys
        """
        label_hotkeys = [label.hotkey for label in labels if label.hotkey and not label.is_deleted]
        if len(label_hotkeys) > len(set(label_hotkeys)):
            raise DuplicateHotkeysException

    @staticmethod
    def __validate_label_color_uniqueness(labels: Sequence[LabelProperties]) -> None:
        """
        Checks if all label colors are unique

        :param labels: List of LabelProperties, each entry representing the properties
        for a single label that are up for validation
        :raises DuplicateLabelColorsException: if there are duplicate label colors
        """
        label_colors = [Color.from_hex_str(label.color).hex_str for label in labels if label.color]
        if len(label_colors) > len(set(label_colors)):
            raise DuplicateLabelColorsException

    @staticmethod
    def _validate_labels_number(data: dict[str, Any], operation: OperationType) -> None:
        """
        Validates that each task has a proper number of labels in the request.

        No labels should be provided for dataset and flow control tasks.
        On creation for anomaly tasks, no labels should be provided (two labels, i.e. anomalous
        and non-anomalous, are created automatically).
        On update for anomaly tasks, two labels (anomalous and normal) should be provided.
        Local vision tasks need at least one label to be explicitly provided (an empty
        one will be added automatically).
        Global vision tasks need at least two top-level labels; the empty label of
        binary classification (if any) must be defined by the user like the normal one.

        :param data: REST request data representing a project
        :raises BadNumberOfLabelsException: if any task does not have
            a proper number of labels
        """
        pipeline_data = data[PIPELINE]
        for task_data in pipeline_data[TASKS]:
            task_title = task_data[TITLE]
            task_type = TaskType[task_data[TASK_TYPE].upper()]
            labels: Sequence = task_data.get(LABELS, [])
            num_labels = len(labels)
            if task_type.is_trainable:
                if task_type.is_anomaly:  # vision anomaly
                    expected_num_labels = 0 if operation == OperationType.CREATE else 2
                    if num_labels != expected_num_labels:
                        raise BadNumberOfLabelsException(
                            task_title=task_title,
                            num_labels=num_labels,
                            expected_num_labels_str=str(expected_num_labels),
                        )
                elif task_type.is_global:  # vision global, non-anomaly
                    # Global tasks can have internal hierarchies; we must ensure that
                    # the top-level contains at least two labels. Top-level labels
                    # are the ones whose parent is in another task or missing.
                    task_label_names: set[str] = {lbl[NAME] for lbl in labels if NAME in lbl}
                    task_label_ids: set[str] = {lbl[ID_] for lbl in labels if ID_ in lbl}
                    task_label_names_and_ids = task_label_names | task_label_ids
                    num_top_level_labels = sum(
                        label.get(PARENT_ID) not in task_label_names_and_ids
                        for label in labels
                        if not label.get(IS_DELETED, False)
                    )
                    if num_top_level_labels < 2:
                        raise BadNumberOfLabelsException(
                            task_title=task_title,
                            num_labels=num_top_level_labels,
                            expected_num_labels_str="at least two top-level ones",
                        )
                # vision local, non-anomaly
                elif num_labels < 1:
                    raise BadNumberOfLabelsException(
                        task_title=task_title,
                        num_labels=num_labels,
                        expected_num_labels_str="at least one",
                    )
            # dataset/flow
            elif num_labels > 0:
                raise BadNumberOfLabelsException(
                    task_title=task_title,
                    num_labels=num_labels,
                    expected_num_labels_str="none",
                )

    @staticmethod
    def __validate_task_labels_for_label_deletion(label_data: list[dict[str, Any]], task_type_str: str) -> None:
        """
        Checks that the combination of labels and task type is valid in case of label
        deletion and checks that at least 1 non-empty label remains. Empty labels can
        also not be removed. Further validation in case of hierarchical labels is done
        in the LabelSchema class

        :param label_data: REST data describing the label
        :param task_type_str: task type as a string
        :raises InvalidLabelDeletedException: if label deletion produces an invalid label
        group for the task
        """
        task_type = TaskType[task_type_str.upper()]
        total_label_count = 0
        for label in label_data:
            is_deleted = label.get(IS_DELETED, False)
            is_empty = label.get(IS_EMPTY, False)
            if is_empty and is_deleted:
                raise InvalidLabelDeletedException(reason=f"Can not delete empty label: {label[NAME]}.")
            if is_deleted and task_type.is_anomaly:
                raise InvalidLabelDeletedException(reason="Can not delete labels in an anomaly project.")
            if not is_empty and not is_deleted:
                total_label_count += 1
        if total_label_count == 0:
            raise InvalidLabelDeletedException(reason="Can not delete all labels.")

    @staticmethod
    def __validate_parent_labels(
        label_data: dict[str, Any],
        task_data: dict[str, Any],
        pipeline_data: dict[str, Any],
    ) -> None:
        """
        Check that the parent specified in the label is valid

        The parent id's can either refer to the label name (in case of a newly created
        label) or the label id (in case of an existing label), so we check against both.

        Checks:
        - The parent_id can be only non-null for classification tasks
        - The parent label cannot be the label itself (i.e. must be a different label)
        - The parent label exists in the same tasks or the parent task
        - The parent label is not empty

        :param label_data: REST data describing the label
        :param task_data: REST data describing the task that contains the label
        :param pipeline_data: REST data describing the pipeline that contains the task
        :raises UnsupportedHierarchicalLabelsException: if hierarchical labels are
            present and the task does not support it
        :raises ParentLabelNotFoundException: if the parent label cannot be found
            neither in the same task nor the parent task
        :raises EmptyParentLabelException: if the parent label is an empty one
        """
        task_title = task_data[TITLE]
        task_id = task_data.get(ID_, "")
        task_type = TaskType[task_data[TASK_TYPE].upper()]
        parent_id = label_data.get(PARENT_ID)

        if parent_id is not None:  # it's either the id or name of a label
            # It is not allowed to specify a parent for tasks other than classification
            if task_type != TaskType.CLASSIFICATION:
                raise UnsupportedHierarchicalLabelsException(task_type=task_type)

            # The parent must be a different label
            if parent_id in (label_data.get(NAME), label_data.get(ID_)):
                raise SelfReferencingParentLabelException

            # The parent task must exist either within the same task (hierarchical
            # labels) or in the parent task. Note the difference between the 'previous'
            # task, i.e. the immediate ancestor, and the 'parent' task, which is the
            # first ancestor vision task with labels.
            parent_label_data: dict[str, Any] | None = next(  # search in this task
                (label for label in task_data[LABELS] if parent_id in (label.get(ID_), label.get(NAME))),
                None,
            )
            if parent_label_data is None:  # not found, search in the parent task
                prev_task_dict = {  # map each task ID or title to its previous task
                    conn[TO]: conn[FROM] for conn in pipeline_data[CONNECTIONS]
                }
                task_name_or_id_to_data = {  # map each task title and ID to the data for that task
                    task_data[TITLE]: task_data for task_data in pipeline_data[TASKS]
                }
                task_name_or_id_to_data.update(
                    {task_data[ID_]: task_data for task_data in pipeline_data[TASKS] if ID_ in task_data}
                )
                parent_task_title: str = prev_task_dict.get(task_title, "")
                parent_task_id: str = prev_task_dict.get(task_id, "")
                # parent_task_identifier is either the ID or the title of the task, depending on what was provided.
                parent_task_identifier = parent_task_title if parent_task_title else parent_task_id
                while parent_task_identifier:  # find the parent task title
                    if task_name_or_id_to_data[parent_task_identifier].get(LABELS):
                        break
                    parent_task_identifier = prev_task_dict.get(parent_task_identifier, "")
                if parent_task_identifier and parent_task_identifier not in [
                    task_title,
                    task_id,
                ]:
                    parent_label_data = next(
                        (
                            label
                            for label in task_name_or_id_to_data[parent_task_identifier][LABELS]
                            if parent_id in (label.get(ID_), label.get(NAME))
                        ),
                        None,
                    )
            if not parent_label_data:
                raise ParentLabelNotFoundException(label_name=label_data[NAME], parent_id=parent_id)

            # The parent task must not be empty
            if parent_label_data.get(IS_EMPTY, False):
                raise EmptyParentLabelException(label_name=label_data[NAME])

    @staticmethod
    def _validate_parent_labels(data: dict[str, Any]) -> None:
        """
        Validates that the `parent_id` property of each label is valid

        Check :method:`~__validate_parent_labels` for more details on the checks.

        :param data: REST request data representing a project
        :raises BadRequestException: In case any parent_id of the labels in the list
            does not refer to a valid label
        """
        pipeline_data = data[PIPELINE]
        for task_data in pipeline_data[TASKS]:
            if LABELS not in task_data:
                continue
            for label_data in task_data[LABELS]:
                ProjectRestValidator.__validate_parent_labels(
                    pipeline_data=pipeline_data,
                    task_data=task_data,
                    label_data=label_data,
                )

    @staticmethod
    def _validate_label_groups(labels: Sequence[LabelProperties]) -> None:
        """
        Validates the label groups

        Checks:
        - all the labels groups in the list of labels only belong to a single task
        - each group contains at most one empty label
        - all the labels in the same group have the same parent
          (equivalently, an ancestor label can't be in the same group of any descendant)

        NOTE: This hinges on the assumption that task_titles are unique.

        :param labels: List of LabelProperties, each entry representing the properties
            for a single label that are up for validation
        :raises MultiTaskLabelGroupException: if any group is used across multiple tasks
        :raises MultipleEmptyLabelsException: if any group has more than one empty label
        :raises MismatchingParentsInLabelGroupException: if there is any pair of label
            within the same group with different parents
        """
        group_names = {label.group for label in labels if label.group is not None}
        for group_name in group_names:
            labels_in_group = [label for label in labels if label.group == group_name]
            task_titles = {label.task_title for label in labels_in_group}
            if len(task_titles) > 1:
                raise MultiTaskLabelGroupException(group_name=group_name)

            empty_labels_in_group = [label for label in labels_in_group if label.is_empty]
            if len(empty_labels_in_group) > 1:
                raise MultipleEmptyLabelsException(group_name=group_name)

            parents_in_group = {label.parent_id for label in labels_in_group}
            if len(parents_in_group) > 1:
                raise MismatchingParentsInLabelGroupException(group_name=group_name)

    @staticmethod
    def _validate_empty_labels(labels: list[LabelProperties]) -> None:
        """
        Validates that user defined label names do not include the name of the empty
        label for that domain

        :param labels: List of LabelProperties, each entry representing the properties
            for a single label that are up for validation
        :raises ReservedLabelNameException: if any label has the same name of the label
            of the empty one for the same domain
        """
        for label in labels:
            empty_label_name = DOMAIN_TO_EMPTY_LABEL_NAME.get(label.domain, None)
            if empty_label_name is None:
                continue
            if (empty_label_name in (label.name, label.group)) and not label.is_empty:
                raise ReservedLabelNameException(label_name=empty_label_name)

    @staticmethod
    def _validate_keypoint_structure(data: dict[str, Any], labels: list[LabelProperties]) -> None:
        """
        Validates that a user defined keypoint structure has exactly 2 nodes, node names match with existing labels,
        has no duplicate edges, and position values are in the range [0.0 1.0]]

        This method must be run after labels validation since it assumes that its labels param is valid.

        :param data: REST request data representing a project
        :param labels: List of LabelProperties
        :raises WrongNumberOfNodesException: if an edge does not have 2 vertices
        :raises IncorrectNodeNameInGraphException: if an edge has an incorrect name
        :raises DuplicateEdgeInGraphException: if the graph contains a duplicate edge
        :raises NodeNameNotInLabelsException: if a node name does not match any of the label names
        :raises NodePositionIsOutOfBoundsException: if a node is out of bounds (not in the range [0.0, 1.0])
        """
        existing_labels = [label.name for label in labels] + [str(label.id) for label in labels]
        pipeline_data = data[PIPELINE]
        duplicate_list = []
        for task_data in pipeline_data[TASKS]:
            task_type = TaskType[task_data[TASK_TYPE].upper()]
            if task_type == TaskType.KEYPOINT_DETECTION:
                keypoint_structure = task_data.get(KEYPOINT_STRUCTURE, {})
                edges = keypoint_structure[EDGES]
                for edge in edges:
                    nodes = edge[NODES]
                    if len(nodes) != 2:
                        raise WrongNumberOfNodesException
                    if nodes[0] not in existing_labels or nodes[1] not in existing_labels:
                        raise IncorrectNodeNameInGraphException
                    if set(nodes) in duplicate_list:
                        raise DuplicateEdgeInGraphException
                    duplicate_list.append(set(nodes))

                positions = keypoint_structure[POSITIONS]
                for position in positions:
                    if position[LABEL] not in existing_labels:
                        raise NodeNameNotInLabelsException
                    if not 0 <= position["x"] <= 1 or not 0 <= position["y"] <= 1:
                        raise NodePositionIsOutOfBoundsException

    @staticmethod
    def _get_labels_from_rest(data: dict[str, Any], include_deleted: bool = False) -> list[LabelProperties]:
        """
        Returns a list of the properties of the Labels for all tasks in the
        request data

        :param data: REST request data representing a project
        :param include_deleted: Boolean that includes deleted labels when true
        :return: List of LabelProperties, each entry representing the properties
            for a single label that are up for validation
        """
        labels: list[LabelProperties] = []
        for task in data[PIPELINE][TASKS]:
            task_type = TaskType[task[TASK_TYPE].upper()]
            for label in task.get(LABELS, []):
                label_properties = LabelProperties.from_rest_and_task_details(
                    data_dict=label,
                    task_title=task[TITLE],
                    task_type=task_type,
                )

                if not label_properties.is_deleted or include_deleted:
                    labels.append(label_properties)

        return labels

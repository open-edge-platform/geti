# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the LabelSchema entity"""

import copy
import logging
from collections.abc import Sequence
from enum import Enum
from typing import Any, cast

from bson import ObjectId

from iai_core.entities.graph import MultiDiGraph
from iai_core.entities.label import Label
from iai_core.utils.uid_generator import generate_uid

from geti_types import ID, PersistentEntity

logger = logging.getLogger(__name__)


class InvalidSchemaException(ValueError):
    """Exception thrown if the LabelGroup already exists"""


class RevertLabelDeletionException(NotImplementedError):
    """Exception thrown if an attempt is made to reactivate a deleted label"""


class LabelDeletionException(ValueError):
    """Exception thrown if an attempt is made to delete all labels for a label schema"""


class LabelGroupExistsException(ValueError):
    """Exception thrown if the LabelGroup already exists."""


class LabelGroupDoesNotExistException(ValueError):
    """Exception thrown if the LabelGroup does not exist."""


class LabelGroupType(Enum):
    """Enum to indicate the LabelGroupType."""

    EXCLUSIVE = 1
    EMPTY_LABEL = 2


class LabelGroup:
    """A label group which has exclusive (multiclass) or contains the empty label.

    Non-exclusive (multilabel) relationships are represented by multiple (exclusive)
    label groups.

    The labels have to be from one task.

    Args:
        name (str): Descriptive name of the label group
        labels (Sequence[Label]): Labels that form the group
        group_type (LabelGroupType): EXCLUSIVE or EMPTY_LABEL
        id (ID): ID of the LabelGroup. If no ID is provided, a new ObjectId()
            will be assigned
    """

    def __init__(
        self,
        name: str,
        labels: Sequence[Label],
        group_type: LabelGroupType = LabelGroupType.EXCLUSIVE,
        id: ID | None = None,
    ):
        self.id_ = ID(ObjectId()) if id is None else id

        self.labels = list(labels)
        self.name = name
        self.group_type = group_type

    def remove_label(self, label: Label) -> None:
        """Remove label from label group if it exists in the group.

        Args:
            label (Label): label to remove
        """
        if label in self.labels:
            self.labels.remove(label)

    def is_single_label(self) -> bool:
        """Returns True if the label group only contains one label.

        Returns:
            bool: True if the label group only contains one label.
        """
        return len(self.labels) == 1

    def __eq__(self, other: object):
        """Returns True if the LabelGroup is equal to the other object."""
        if not isinstance(other, LabelGroup):
            return False
        return self.id_ == other.id_ and (set(self.labels) == set(other.labels) and self.group_type == other.group_type)

    def __repr__(self) -> str:
        """Returns the string representation of the LabelGroup."""
        return f"LabelGroup(id={self.id_}, name={self.name}, group_type={self.group_type}, labels={self.labels})"


class LabelTree(MultiDiGraph):
    """Represents a hierarchy of labels in the form a tree.

    The tree is represented by a directed graph
    """

    def __init__(self) -> None:
        super().__init__()

    def add_edge(self, node1: Label, node2: Label, edge_value: Any = None) -> None:
        """Add edge between two nodes in the tree.

        :param node1: first node
        :param node2: second node
        :param edge_value: The value of the new edge. Defaults to None.
        """
        super().add_edge(node1, node2, edge_value)

    def add_node(self, node: Label) -> None:
        """Add node to the tree."""
        super().add_node(node)

    def add_edges(self, edges: Any) -> None:
        """Add edges between Labels."""
        self._graph.add_edges_from(edges)

    def remove_node(self, node: Label) -> None:
        """Remove node from the tree."""
        super().remove_node(node)

    @property
    def num_labels(self) -> int:
        """Return the number of labels in the tree."""
        return self.num_nodes()

    @property
    def type(self) -> str:
        """Returns the type of the LabelTree."""
        return "tree"

    def add_child(self, parent: Label, child: Label) -> None:
        """Add a `child` Label to `parent`."""
        self.add_edge(child, parent)

    def get_parent(self, label: Label) -> Label | None:
        """Returns the parent of `label`"""
        result = self.neighbors(label)
        return result[0] if len(result) > 0 else None

    def get_children(self, parent: Label) -> list[Label]:
        """Returns children of `parent`."""
        if parent not in self._graph.nodes:
            return []
        return list(self._graph.predecessors(parent))  # pylint: disable=no-member

    def get_descendants(self, parent: Label) -> list[Label]:
        """Returns descendants (children and children of children, etc.) of `parent`."""
        return self.descendants(parent)

    def get_siblings(self, label: Label) -> list[Label]:
        """Returns the siblings of a label."""
        parent = self.get_parent(label)
        if parent is None:
            siblings = []
        else:
            siblings = [u for u, v in self._graph.in_edges(parent) if u != label]  # pylint: disable=no-member
        return siblings

    def get_ancestors(self, label: Label) -> list[Label]:
        """Returns ancestors of `label`, including self."""
        result = []
        parent: Label | None = label
        while parent is not None:
            result.append(parent)
            parent = self.get_parent(parent)
        return result

    def subgraph(self, labels: Sequence[Label]) -> "LabelTree":
        """Return the subgraph containing the given labels."""
        new_graph = LabelTree()
        new_graph.set_graph(self.get_graph().subgraph(labels).copy())
        return new_graph

    def __eq__(self, other: object) -> bool:
        """Check if two LabelTrees are equal."""
        if isinstance(other, LabelTree):
            return super().__eq__(other)
        return False


class LabelSchema(PersistentEntity):
    """
    This class represents the relationships of labels.

    This class currently keeps track of the following relationships:

    - parent/child label relationship
    - label group relationships

    :param id_: ID to assign to this schema
    :param label_tree: DAG representing hierarchical relationships between labels
    :param label_groups: List of groups of mutually exclusive labels (multi-class)
    :param previous_schema_revision_id: Optional, ID of the previous schema (if any)
        before the labels changed.
    :param project_id: Optional, ID of the Project this schema refers to
    :param deleted_label_ids: Optional, list of IDs of labels that are deactivated
    """

    def __init__(
        self,
        id_: ID,
        label_tree: LabelTree | None = None,
        label_groups: list[LabelGroup] | None = None,
        previous_schema_revision_id: ID | None = None,
        project_id: ID | None = None,
        deleted_label_ids: Sequence[ID] | None = None,
        ephemeral: bool = True,
    ) -> None:
        PersistentEntity.__init__(self, id_=id_, ephemeral=ephemeral)

        if label_tree is None:
            label_tree = LabelTree()
        self.label_tree = label_tree

        if label_groups is None:
            label_groups = []
        self._groups = label_groups

        self.previous_schema_revision_id = (
            previous_schema_revision_id if previous_schema_revision_id is not None else ID()
        )
        self._project_id = project_id if project_id is not None else ID()
        self.__deleted_label_ids = deleted_label_ids or []

    @property
    def project_id(self) -> ID:
        """
        Get the ID of the Project

        :return: Project ID
        """
        return self._project_id

    @property
    def deleted_label_ids(self) -> tuple[ID, ...]:
        """
        Get the list of IDs of deleted labels

        :return: List of IDs
        """
        return tuple(self.__deleted_label_ids)

    @deleted_label_ids.setter
    def deleted_label_ids(self, label_ids: Sequence[ID]) -> None:
        """
        Set the list of IDs of deleted labels. Will find any child labels and set
        them as deleted too.

        :param label_ids: List of IDs
        """
        label_ids = list(label_ids)
        deleted_child_label_ids: list[ID] = []
        for label_id in label_ids:
            label = self.get_label_by_id(label_id=label_id)
            if label is not None:
                deleted_child_label_ids.extend(label.id_ for label in self.label_tree.get_descendants(parent=label))
        label_ids.extend(deleted_child_label_ids)
        label_ids = list(set(label_ids))
        # For now, only allow deleting labels. Reactivating labels is not allowed.
        if not set(self.__deleted_label_ids).issubset(label_ids):
            raise RevertLabelDeletionException("Reactivating deleted labels is not supported yet.")
        if len(self.get_all_labels()) - 1 <= len(label_ids):
            raise LabelDeletionException("Cannot delete all labels. At least two labels must remain.")
        self.__deleted_label_ids = label_ids

    def get_labels(self, include_empty: bool) -> list[Label]:
        """
        Get the labels in the label schema. Note that this function does not return
        deleted labels

        :param include_empty: flag determining whether to include empty labels
        :return: list of labels in the label schema
        """
        return [
            label
            for group in self._groups
            for label in group.labels
            if (include_empty or not label.is_empty) and label.id_ not in self.deleted_label_ids
        ]

    def get_label_map(self) -> dict[ID, Label]:
        """
        :return: Dictionary with label ids as key and labels as values.
        """
        label_map = {}
        for label in self.get_labels(include_empty=True):
            label_map[label.id_] = label
        return label_map

    def get_empty_labels(self) -> tuple[Label, ...]:
        """
        Get the empty labels in the label schema.
        Note that this function does not return deleted labels

        :return: tuple of empty labels in the label schema
        """
        return tuple(label for label in self.get_labels(include_empty=True) if label.is_empty)

    def get_label_ids(self, include_empty: bool) -> list[ID]:
        """
        Returns a list of label ids that are in the LabelSchema. Removes any deleted
        labels.

        :param include_empty: flag determining whether to include empty labels
        :return: list of label ids in the label schema
        """
        return [label.id_ for label in self.get_labels(include_empty=include_empty)]

    def get_all_labels(self) -> list[Label]:
        """
        Get the labels in the label schema. Note that this includes deleted and empty
        labels

        :return: list of labels in the label schema
        """
        return [label for group in self._groups for label in group.labels]

    def get_groups(self, include_empty: bool = False) -> list[LabelGroup]:
        """
        Get the label groups in the label schema. Removes any deleted labels from the
        groups as well as any groups that only consist of deleted labels.

        :param include_empty: flag determining whether to include empty label groups
        :return: list of all label groups in the label schema
        """
        groups = [group for group in self._groups if group.group_type != LabelGroupType.EMPTY_LABEL or include_empty]
        return self.__remove_deleted_labels_from_groups(groups=groups)

    def add_group(self, label_group: LabelGroup) -> None:
        """Adding a group to label schema.

        :param label_group (LabelGroup): label group to add
        """
        if label_group.name in [group.name for group in self._groups]:
            raise LabelGroupExistsException(
                f"group with '{label_group.name}' exists, use add_labels_to_group_by_group_name instead"
            )
        self.__append_group(label_group)

    def get_exclusive_groups(self) -> list[LabelGroup]:
        """
        Returns exclusive groups in the LabelSchema. Removes any deleted labels from the
        groups as well as any groups that only consist of deleted labels.
        """
        groups = [group for group in self._groups if group.group_type == LabelGroupType.EXCLUSIVE]
        return self.__remove_deleted_labels_from_groups(groups=groups)

    def __remove_deleted_labels_from_groups(self, groups: list[LabelGroup]) -> list[LabelGroup]:
        """
        Removes any deleted labels from the groups as well as any groups that only consist
        of deleted labels.
        """
        groups_without_deleted_labels = []
        for group in groups:
            new_group = copy.deepcopy(group)
            non_deleted_labels = [label for label in new_group.labels if label.id_ not in self.__deleted_label_ids]
            if len(non_deleted_labels) > 0:
                new_group.labels = non_deleted_labels
                groups_without_deleted_labels.append(new_group)

        return groups_without_deleted_labels

    def add_labels_to_group_by_group_name(self, group_name: str, labels: Sequence[Label]) -> None:
        """
        Adds `labels` to group named `group_name`

        :param labels: list of Label
        :param group_name: group name

        :raises LabelGroupDoesNotExistException: This is raised if the group does not
            exist
        """
        for group in self._groups:
            if group.name == group_name:
                group.labels += labels
                break
        else:
            raise LabelGroupDoesNotExistException(f"group with name '{group_name}' does not exist, cannot add")

    def add_groups_for_task(self, label_groups: list[LabelGroup]) -> None:
        """
        Add a list of label groups for a task to the label schema
        This function also contains the following logic:
            - Checks that no duplicate label group names are used across different tasks.
        :param label_groups: List of LabelGroup to add to the label schema
        :return: The updated LabelSchema
        :raises InvalidSchemaException if a label group name appears in more than one task
        """
        existing_group_names = [group.name for group in self.get_groups()]
        for label_group in label_groups:
            if label_group.name in existing_group_names:
                raise InvalidSchemaException(f"Group with name '{label_group.name}' appears in more than one task.")
            self.add_group(label_group)

    def add_label_relations_for_task(
        self,
        child_to_parent_id: dict[Label, str | ID],
        task_labels: list[Label],
        previous_trainable_task_labels: list[Label],
        add_previous_task_label_as_parent: bool,
    ) -> None:
        """
        Create intra-task and inter-task hierarchy relations for the labels of a task.

        Label schema is modified in-place.

        :param child_to_parent_id: Dictionary that maps each label to the name or ID of the
         parent label.
        :param task_labels: List of all labels in the task
        :param previous_trainable_task_labels: List of all labels in the previous task
        :param add_previous_task_label_as_parent: Whether to create additional
            inter-task relations between the top-level labels of this task (children)
            and the first label of the previous task (parent).
        :raises InvalidSchemaException: When a parent name is specified that doesn't exist
        :return: The updated LabelSchema
        """
        for child_label, parent_id in child_to_parent_id.items():
            parent_label = next(
                (
                    label
                    for label in previous_trainable_task_labels + task_labels
                    if parent_id in (label.id_, label.name)
                ),
                None,
            )
            if parent_label is None:
                raise InvalidSchemaException(
                    f"parent_id `{parent_id}` was specified for label with name {child_label.name},"
                    f" but there is no such parent label in the previous task."
                )
            self.add_child(parent_label, child_label)

        if add_previous_task_label_as_parent:
            task_top_level_labels = set(task_labels) - set(child_to_parent_id.keys())
            for label in task_top_level_labels:
                self.add_child(previous_trainable_task_labels[0], label)

    def get_label_by_id(self, label_id: ID) -> Label | None:
        """
        Find the Label with the given ID within the schema.

        :param label_id: ID of the label to search
        :return: Label if found, None otherwise
        """
        label = next(
            (cast("Label", label) for label in self.get_all_labels() if label.id_ == label_id),
            None,
        )
        if label is None:
            logger.warning(f"Label with ID {label_id} not found in label schema.")
        return label

    def get_label_by_name(self, label_name: str) -> Label | None:
        """
        Find the Label with the given name within the schema.

        :param label_name: Name of the label to search
        :return: Label if found, None otherwise
        """
        return next(
            (cast("Label", label) for label in self.get_labels(include_empty=True) if label.name == label_name),
            None,
        )

    def get_label_group_by_name(self, group_name: str) -> LabelGroup | None:
        """
        Get the label group by the passed group_name. Hides deleted labels in group
        :param group_name: name of the label group to find
        :return: LabelGroup if match is found. None otherwise.
        """
        for label_group in self._groups:
            if group_name == label_group.name:
                group = self.__remove_deleted_labels_from_groups(groups=[label_group])
                return group[0] if len(group) == 1 else None
        return None

    def get_group_containing_label(self, label: Label) -> LabelGroup | None:
        """
        Returns the label group which contains the label. Hides deleted labels in group

        :param label: the query label
        :return:
        """
        for label_group in self._groups:
            if label in label_group.labels:
                group = self.__remove_deleted_labels_from_groups(groups=[label_group])
                return group[0] if len(group) == 1 else None
        return None

    def add_child(self, parent: Label, child: Label) -> None:
        """Add a `child` Label to `parent`."""
        self.label_tree.add_child(parent, child)

    def get_parent(self, label: Label) -> Label | None:
        """
        Returns the parent of `label`.
        """
        return self.label_tree.get_parent(label)

    def __append_group(self, label_group: LabelGroup):
        """Convenience function for appending `label_group` to the necessary internal data structures.

        :param label_group (LabelGroup): label group to append
        """
        if label_group not in self._groups:
            self._groups.append(label_group)

    def get_children(self, parent: Label) -> list[Label]:
        """Return a list of the children of the passed parent Label."""
        return self.label_tree.get_children(parent)

    def get_siblings_in_group(self, label: Label) -> list[Label]:
        """Return a list of the 'siblings', which are all labels within the same group as a label."""
        containing_group = self.get_group_containing_label(label)
        if containing_group is None:
            return []
        return [label_iter for label_iter in containing_group.labels if label_iter != label]

    def get_descendants(self, parent: Label) -> list[Label]:
        """Returns descendants (children and children of children, etc.) of `parent`."""
        return self.label_tree.get_descendants(parent)

    def get_ancestors(self, label: Label) -> list[Label]:
        """Returns ancestors of `label`, including self."""
        return self.label_tree.get_ancestors(label)

    @classmethod
    def from_labels(cls, labels: Sequence[Label]) -> "LabelSchema":
        """Create LabelSchema from a list of exclusive labels (only used in tests)"""
        label_group = LabelGroup(name="from_label_list", labels=labels)
        return LabelSchema(id_=ID("test_only"), label_groups=[label_group])

    def __repr__(self) -> str:
        return (
            f"LabelSchema(id_={self.id_}, "
            f"project_id={self.project_id}, "
            f"prev_schema_id={self.previous_schema_revision_id}, "
            f"label_groups={self._groups})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LabelSchema):
            return False
        return (
            self.id_ == other.id_
            and self.project_id == other.project_id
            and self.previous_schema_revision_id == other.previous_schema_revision_id
            and self.label_tree == other.label_tree
            and self.get_groups(include_empty=True) == other.get_groups(include_empty=True)
            and self.deleted_label_ids == other.deleted_label_ids
        )


class NullLabelSchema(LabelSchema):
    """Representation of a label schema not found'"""

    def __init__(self) -> None:
        super().__init__(id_=ID())

    def __repr__(self) -> str:
        return "NullLabelSchema()"


class LabelSchemaView(LabelSchema):
    """Represents a restricted view of LabelSchema"""

    def __init__(
        self,
        label_schema: LabelSchema,
        id_: ID,
        label_tree: LabelTree | None = None,
        label_groups: list[LabelGroup] | None = None,
        previous_schema_revision_id: ID | None = None,
        task_node_id: ID | None = None,
        deleted_label_ids: Sequence[ID] | None = None,
    ) -> None:
        super().__init__(
            id_=id_,
            label_tree=label_tree,
            label_groups=label_groups,
            previous_schema_revision_id=previous_schema_revision_id,
            project_id=label_schema.project_id,
            deleted_label_ids=deleted_label_ids,
        )
        self.parent_schema = label_schema
        self._task_node_id = task_node_id if task_node_id is not None else ID()

    @property
    def task_node_id(self) -> ID:
        """
        Get the ID of the TaskNode

        :return: TaskNode ID
        """
        return self._task_node_id

    @classmethod
    def from_parent(
        cls,
        parent_schema: LabelSchema,
        id_: ID,
        labels: Sequence[Label],
        previous_schema_revision_id: ID | None = None,
        task_node_id: ID | None = None,
        deleted_label_ids: list[ID] | None = None,
    ):
        """
        Create LabelSchemaView from a parent schema and a list of labels

        :param parent_schema: Parent label schema
        :param id_: ID to assign to the LabelSchemaView instance
        :param labels: List of labels significant to the desired LabelSchemaView
        :param previous_schema_revision_id: Optional, ID of the previous schema view
            (if any) before the labels changed.
        :param task_node_id: Optional, ID of the TaskNode this schema refers to
        :param deleted_label_ids: Optional, list of IDs of labels that are deactivated
        :return: LabelSchemaView from the given labels and the parent schema
        """
        label_tree = parent_schema.label_tree.subgraph(labels)

        set_of_labels = set(labels)

        label_groups = []

        for parent_group in parent_schema.get_groups(include_empty=True):
            group_labels = list(set(parent_group.labels).intersection(set_of_labels))
            if len(group_labels) > 0:
                label_groups.append(
                    LabelGroup(
                        parent_group.name,
                        group_labels,
                        parent_group.group_type,
                        parent_group.id_,
                    )
                )

        return cls(
            label_schema=parent_schema,
            id_=id_,
            label_groups=label_groups,
            label_tree=label_tree,
            previous_schema_revision_id=previous_schema_revision_id,
            task_node_id=task_node_id,
            deleted_label_ids=deleted_label_ids,
        )

    @classmethod
    def from_labels(  # type: ignore
        cls,
        labels: Sequence[Label],
        previous_schema_revision_id: ID = ID(),
        task_node_id: ID = ID(),
    ):
        """
        Create LabelSchemaView from a list of labels

        :param labels: list of labels
        :param previous_schema_revision_id: Optional, ID of the previous schema view
            (if any) before the labels changed.
        :param task_node_id: Optional, ID of the TaskNode this schema refers to
        :return: LabelSchemaView from the given labels
        """
        label_group = LabelGroup(name="from_label_list", labels=labels)
        # Note: This method is only used in tests, so we generate the id_ on the fly
        parent_schema = LabelSchema(id_=generate_uid(), label_groups=[label_group])
        return cls.from_parent(
            parent_schema=parent_schema,
            id_=generate_uid(),
            labels=labels,
            previous_schema_revision_id=previous_schema_revision_id,
            task_node_id=task_node_id,
        )

    def __repr__(self) -> str:
        return (
            f"LabelSchemaView(id_={self.id_}, "
            f"project_id={self.project_id}, "
            f"task_id={self.task_node_id}, "
            f"parent_schema={self.parent_schema}, "
            f"prev_schema_id={self.previous_schema_revision_id}, "
            f"label_groups={self.get_groups(include_empty=True)})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LabelSchemaView):
            return False
        return (
            self.parent_schema == other.parent_schema
            and self.task_node_id == other.task_node_id
            and self.previous_schema_revision_id == other.previous_schema_revision_id
            and self.label_tree == other.label_tree
            and self.get_groups(include_empty=True) == other.get_groups(include_empty=True)
        )

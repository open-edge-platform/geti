# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import contextlib
from typing import Any
from unittest.mock import patch

import pytest

from iai_core.factories.project_validator import ProjectCreationValidator, ProjectUpdateValidator
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
from tests.tools.custom_project_parser import CustomTestProjectParser, CustomTestProjectUpdateParser


class TestProjectValidator:
    # fmt: off
    @pytest.mark.parametrize(
        "lazyfxt_project_data, expected_exception",
        (
            ("fxt_binary_classification_project_data", None),
            ("fxt_detection_classification_project_data", None),
            ("fxt_hierarchy_classification_project_data_2", None),
            ("fxt_label_hierarchy_task_chain_project_data", None),
            ("fxt_anomaly_classification_project_data", None),
            ("fxt_keypoint_detection_project_data", None),
            ("fxt_invalid_anomaly_classification_project_data", BadNumberOfLabelsException),
            ("fxt_invalid_project_data_label_in_non_trainable_task", BadNumberOfLabelsException),
            ("fxt_invalid_project_data_no_tasks", NoTasksInProjectException),
            ("fxt_invalid_project_data_no_empty_name", EmptyProjectNameException),
            ("fxt_invalid_project_data_classification_one_label", BadNumberOfLabelsException),
            ("fxt_invalid_project_data_hierarchical_cls_one_top_label", BadNumberOfLabelsException),
            ("fxt_invalid_project_data_duplicate_label_hotkeys", DuplicateHotkeysException),
            ("fxt_invalid_project_data_missing_parent_label", ParentLabelNotFoundException),
            ("fxt_invalid_project_data_local_task_with_hierarchy", UnsupportedHierarchicalLabelsException),
            ("fxt_invalid_project_data_self_referencing_parent", SelfReferencingParentLabelException),
            ("fxt_invalid_project_data_label_group_in_multiple_tasks", MultiTaskLabelGroupException),
            ("fxt_invalid_project_data_same_group_hierarchical_labels", MismatchingParentsInLabelGroupException),
            ("fxt_invalid_project_data_empty_label_name_conflict", ReservedLabelNameException),
            ("fxt_keypoint_detection_duplicate_edge_project_data", DuplicateEdgeInGraphException),
            ("fxt_keypoint_detection_too_many_nodes_project_data", WrongNumberOfNodesException),
            ("fxt_keypoint_detection_invalid_node_name_project_data", IncorrectNodeNameInGraphException),
        ),
        ids=[
            "valid single task project",
            "valid multi task project",
            "valid project with a deep hierarchy of labels",
            "valid chained project with a deep hierarchy of labels",
            "valid anomaly project",
            "valid keypoint detection project",
            "invalid anomaly due to unexpected labels",
            "invalid due to a label in a non trainable task",
            "invalid due to missing mandatory fields (no tasks)",
            "invalid due to empty name (no valid characters)",
            "invalid classification due to insufficient labels",
            "invalid hier. class. due to insufficient labels in the top level",
            "invalid task due to duplicate label hotkeys in a task",
            "invalid due to parent_id pointing to a non-existing label",
            "invalid due to a local task with label with non-null parent",
            "invalid due to parent_id pointing to the label itself",
            "invalid due to duplicate label group across tasks",
            "invalid due to hierarchical labels having the same group",
            "invalid due to a label with the same name of the empty one",
            "invalid due to duplicate edge in keypoint graph",
            "invalid due to incorrect number of nodes in graph",
            "invalid due to incorrect node name in keypoint graph",
        ],
    )
    # fmt: on
    def test_validate_creation_data_statically(
        self, lazyfxt_project_data, expected_exception, request: pytest.FixtureRequest
    ) -> None:
        # Arrange
        fxt_project_data = request.getfixturevalue(lazyfxt_project_data)
        parser = CustomTestProjectParser(**fxt_project_data)
        context: Any = contextlib.nullcontext()
        if expected_exception is not None:
            context = pytest.raises(expected_exception)

        # Act
        with context:
            ProjectCreationValidator().validate(parser)

    # fmt: off
    @pytest.mark.parametrize(
        "lazyfxt_project_data, expected_exception",
        (
            ("fxt_binary_classification_project_update_data", None),
            ("fxt_detection_classification_project_update_data", None),
            ("fxt_label_hierarchy_task_chain_project_update_data", None),
            ("fxt_update_hierarchy_classification_project_data_2", None),
            ("fxt_update_anomaly_classification_project_data", None),
            ("fxt_update_valid_detection_classification_data", None),
            ("fxt_keypoint_detection_valid_update_project_data", None),
            ("fxt_update_invalid_project_anomaly_task_without_labels", BadNumberOfLabelsException),
            ("fxt_update_invalid_project_data_no_tasks", NoTasksInProjectException),
            ("fxt_update_invalid_project_data_no_empty_name", EmptyProjectNameException),
            ("fxt_update_invalid_project_data_classification_one_label", BadNumberOfLabelsException),
            ("fxt_update_invalid_project_data_hierarchical_cls_one_top_label", BadNumberOfLabelsException),
            ("fxt_update_invalid_project_data_duplicate_label_hotkeys", DuplicateHotkeysException),
            ("fxt_update_invalid_project_data_missing_parent_label", ParentLabelNotFoundException),
            ("fxt_update_invalid_project_data_self_referencing_parent", SelfReferencingParentLabelException),
            ("fxt_update_invalid_project_data_local_task_with_hierarchy", UnsupportedHierarchicalLabelsException),
            ("fxt_update_invalid_project_data_label_group_in_multiple_tasks", MultiTaskLabelGroupException),
            ("fxt_update_invalid_project_data_same_group_hierarchical_labels", MismatchingParentsInLabelGroupException),
            ("fxt_update_invalid_project_data_empty_label_name_conflict", ReservedLabelNameException),
            ("fxt_update_invalid_detection_classification_project_data_label_addition", ParentLabelNotFoundException),
            ("fxt_update_invalid_anomaly_label_addition", UnsupportedTaskTypeForLabelAdditionException),
            ("fxt_update_invalid_detection_classification_label_addition", LocalGlobalLabelAdditionException),
            ("fxt_update_invalid_anomaly_label_deletion", InvalidLabelDeletedException),
            ("fxt_update_invalid_all_labels_deletion", InvalidLabelDeletedException),
            ("fxt_update_hotkey_of_deleted_label_reused", None),
        ),
        ids=[
            "valid single task project",
            "valid multi task project",
            "valid multitask project with a deep hierarchy of labels",
            "valid project with a deep hierarchy of labels",
            "valid anomaly project",
            "valid detection classification project update",
            "valid keypoint detection project update",
            "invalid anomaly due to missing labels",
            "invalid due to empty tasks list",
            "invalid due to empty name (no valid characters)",
            "invalid classification due to insufficient labels",
            "invalid hier. class. due to insufficient labels in the top level",
            "invalid task due to duplicate label hotkeys in a task",
            "invalid due to parent_id pointing to a non-existing label",
            "invalid due to parent_id pointing to the label itself",
            "invalid due to a local task with label with non-null parent",
            "invalid due to duplicate label group across tasks",
            "invalid due to hierarchical labels having the same group",
            "invalid due to a label with the same name of the empty one",
            "invalid due to a label addition with parent_id pointing to a non-existing label",
            "invalid due to a label addition to anomaly task",
            "invalid due to a label addition to a local task followed by global",
            "invalid due to deleted a label in anomaly task",
            "invalid due to deleted all labels",
            "valid where the hotkey of a deleted label gets reused",
        ],
    )
    # fmt: on
    def test_validate_update_data_statically(
        self, lazyfxt_project_data, expected_exception, request: pytest.FixtureRequest
    ) -> None:
        # Arrange
        fxt_project_data = request.getfixturevalue(lazyfxt_project_data)
        update_parser = CustomTestProjectUpdateParser(**fxt_project_data)
        context: Any = contextlib.nullcontext()
        if expected_exception is not None:
            context = pytest.raises(expected_exception)

        # Act
        with context:
            ProjectUpdateValidator().validate(update_parser)

    def test_validate_duplicate_task_names(
        self, fxt_binary_classification_project_data, fxt_binary_classification_project_update_data
    ):
        parser = CustomTestProjectParser(**fxt_binary_classification_project_data)
        update_parser = CustomTestProjectUpdateParser(**fxt_binary_classification_project_update_data)

        # Act
        with patch.object(parser, "get_tasks_names", side_effect=[("Dataset", "Dataset")]):
            with pytest.raises(DuplicateTaskNamesException):
                ProjectCreationValidator()._validate_task_names(parser)
        with patch.object(update_parser, "get_tasks_names", side_effect=[("Dataset", "Dataset")]):
            with pytest.raises(DuplicateTaskNamesException):
                ProjectUpdateValidator()._validate_task_names(update_parser)

    def test_validate_duplicate_labels(
        self, fxt_binary_classification_project_data, fxt_binary_classification_project_update_data
    ):
        parser = CustomTestProjectParser(**fxt_binary_classification_project_data)
        update_parser = CustomTestProjectUpdateParser(**fxt_binary_classification_project_update_data)

        # Act
        with patch.object(parser, "get_custom_labels_names_by_task", side_effect=[(), ("small", "small")]):
            with pytest.raises(DuplicateLabelNamesException):
                ProjectCreationValidator()._validate_label_uniqueness(parser)
        with patch.object(
            update_parser,
            "get_custom_labels_names_by_task",
            side_effect=[(), (), ("small", "small"), ("small", "small?")],
        ):
            with pytest.raises(DuplicateLabelNamesException):
                ProjectUpdateValidator()._validate_label_uniqueness(update_parser)

    def test_validate_duplicate_labels_across_tasks(
        self, fxt_invalid_project_data_label_duplication, fxt_update_invalid_project_data_label_duplication
    ):
        parser = CustomTestProjectParser(**fxt_invalid_project_data_label_duplication)
        update_parser = CustomTestProjectUpdateParser(**fxt_update_invalid_project_data_label_duplication)

        with pytest.raises(DuplicateLabelNamesException):
            ProjectCreationValidator()._validate_label_uniqueness(parser)
        with pytest.raises(DuplicateLabelNamesException):
            ProjectUpdateValidator()._validate_label_uniqueness(update_parser)

    def test_validate_connection_number(
        self, fxt_binary_classification_project_data, fxt_binary_classification_project_update_data
    ):
        parser = CustomTestProjectParser(**fxt_binary_classification_project_data)
        update_parser = CustomTestProjectUpdateParser(**fxt_binary_classification_project_update_data)

        # Act
        # No connections
        with patch.object(parser, "get_connections", side_effect=[()]):
            with pytest.raises(NoTasksConnectionsException):
                ProjectCreationValidator()._validate_connections(parser)
        with patch.object(update_parser, "get_connections", side_effect=[()]):
            with pytest.raises(NoTasksConnectionsException):
                ProjectUpdateValidator()._validate_connections(update_parser)
        # More connections than tasks
        with patch.object(
            parser,
            "get_connections",
            side_effect=[(("Dataset", "Classification task"), ("Classification task", "Crop"))],
        ):
            with pytest.raises(BadNumberOfConnectionsException):
                ProjectCreationValidator()._validate_connections(parser)
        with patch.object(
            update_parser,
            "get_connections",
            side_effect=[(("Dataset", "Classification task"), ("Classification task", "Crop"))],
        ):
            with pytest.raises(BadNumberOfConnectionsException):
                ProjectUpdateValidator()._validate_connections(update_parser)
        # Unconnected tasks
        with patch.object(parser, "get_connections", side_effect=[(("task_a", "task_b"),)]):
            with pytest.raises(UnconnectedTasksException):
                ProjectCreationValidator()._validate_connections(parser)
        with patch.object(update_parser, "get_connections", side_effect=[(("task_a", "task_b"),)]):
            with pytest.raises(UnconnectedTasksException):
                ProjectUpdateValidator()._validate_connections(update_parser)
        # Too many source tasks tasks
        with (
            patch.object(parser, "get_tasks_names", return_value=("Dataset", "Classification task", "Crop")),
            patch.object(
                parser, "get_connections", side_effect=[(("Dataset", "Classification task"), ("Dataset", "Crop"))]
            ),
        ):
            with pytest.raises(TooManySourceTasksException):
                ProjectCreationValidator()._validate_connections(parser)
        with (
            patch.object(update_parser, "get_tasks_names", return_value=("Dataset", "Classification task", "Crop")),
            patch.object(
                update_parser,
                "get_connections",
                side_effect=[(("Dataset", "Classification task"), ("Dataset", "Crop"))],
            ),
        ):
            with pytest.raises(TooManySourceTasksException):
                ProjectUpdateValidator()._validate_connections(update_parser)
        # Too many sink tasks tasks
        with (
            patch.object(parser, "get_tasks_names", return_value=("Dataset", "Classification task", "Crop")),
            patch.object(
                parser,
                "get_connections",
                side_effect=[(("Dataset", "Classification task"), ("Crop", "Classification task"))],
            ),
        ):
            with pytest.raises(TooManySinkTasksException):
                ProjectCreationValidator()._validate_connections(parser)
        with (
            patch.object(update_parser, "get_tasks_names", return_value=("Dataset", "Classification task", "Crop")),
            patch.object(
                update_parser,
                "get_connections",
                side_effect=[(("Dataset", "Classification task"), ("Crop", "Classification task"))],
            ),
        ):
            with pytest.raises(TooManySinkTasksException):
                ProjectUpdateValidator()._validate_connections(update_parser)

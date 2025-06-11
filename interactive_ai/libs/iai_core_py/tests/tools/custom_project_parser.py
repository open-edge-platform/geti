# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
This module defines custom project parser to test project builder
"""

from typing import Any

from iai_core.entities.model_template import TaskType
from iai_core.factories.project_parser import ProjectParser, ProjectParserInternalError, ProjectUpdateParser

from geti_types import ID


class CustomTestProjectParser(ProjectParser):
    """
    Parser that can read and decode the information necessary to create
    a project from the custom test oriented data format.

    :param test_data: custom dict input data
    """

    def __init__(self, name: str, tasks_dict: dict[str, Any]) -> None:
        self.project_name = name
        self.tasks_dict = tasks_dict
        self.tasks_names = tuple(self.tasks_dict.keys())

    def get_project_name(self) -> str:
        return self.project_name

    def get_connections(self) -> tuple[tuple[str, str], ...]:
        return tuple(zip(self.tasks_names[:-1], self.tasks_names[1:]))

    def get_tasks_names(self) -> tuple[str, ...]:
        return self.tasks_names

    def _get_task_dict(self, task_name: str) -> dict[str, Any]:
        try:
            return self.tasks_dict[task_name]
        except StopIteration as ex:
            if task_name not in self.get_tasks_names():
                raise ValueError(f"Task with name '{task_name}' not found") from ex
            raise ProjectParserInternalError(f"Error while fetching data for task with name '{task_name}'") from ex

    def get_task_type_by_name(self, task_name: str) -> TaskType:
        task_dict = self._get_task_dict(task_name)
        return TaskType[task_dict["task_type"].upper()]

    def get_custom_labels_names_by_task(self, task_name: str) -> tuple[str, ...]:
        task_dict = self._get_task_dict(task_name)
        return tuple(task_dict.get("labels", {}).keys())

    def _get_label_dict(self, task_name: str, label_name: str) -> dict[str, Any]:
        try:
            task_dict = self._get_task_dict(task_name)
            return task_dict.get("labels", {})[label_name]
        except StopIteration as ex:
            if label_name not in self.get_custom_labels_names_by_task(task_name=task_name):
                raise ValueError(f"Label with name '{label_name}' not found in task '{task_name}'") from ex
            raise ProjectParserInternalError(
                f"Error while fetching data for label with name '{label_name}' in task '{task_name}'"
            ) from ex

    def get_label_group_by_name(self, task_name: str, label_name: str) -> str:
        label_dict = self._get_label_dict(task_name=task_name, label_name=label_name)
        return label_dict.get("group", "")

    def get_label_hotkey_by_name(self, task_name: str, label_name: str) -> str:
        label_dict = self._get_label_dict(task_name=task_name, label_name=label_name)
        hotkey = label_dict.get("hotkey", "")
        return hotkey if hotkey else ""

    def get_label_color_by_name(self, task_name: str, label_name: str) -> str:
        label_dict = self._get_label_dict(task_name=task_name, label_name=label_name)
        color = label_dict.get("color", "")
        return color if color else ""

    def get_label_parent_by_name(self, task_name: str, label_name: str) -> str:
        label_dict = self._get_label_dict(task_name=task_name, label_name=label_name)
        parent = label_dict.get("parent_id", "")
        return parent if parent else ""

    def get_keypoint_structure_data(self, task_name: str) -> dict:
        task_dict = self._get_task_dict(task_name=task_name)
        return task_dict.get("keypoint_structure", {})


class CustomTestProjectUpdateParser(CustomTestProjectParser, ProjectUpdateParser):
    def __init__(self, name: str, id: str, tasks_dict: dict[str, Any]) -> None:
        super().__init__(name=name, tasks_dict=tasks_dict)
        self.project_id = id

    def get_connections(self) -> tuple[tuple[ID, ID], ...]:
        connections = []
        tasks_names = tuple(self.tasks_dict.keys())
        for task_from, task_to in tuple(zip(tasks_names[:-1], tasks_names[1:])):
            connections.append((ID(self.tasks_dict[task_from]["id"]), ID(self.tasks_dict[task_to]["id"])))
        return tuple(connections)

    def get_task_id_by_name(self, task_name: str) -> ID:
        return ID(self.tasks_dict[task_name]["id"])

    def get_label_id_by_name(self, task_name: str, label_name: str) -> ID | None:
        label_dict = self.tasks_dict[task_name]["labels"][label_name]
        return ID(label_dict["id"]) if "id" in label_dict else None

    def get_added_labels_names_by_task(self, task_name: str) -> tuple[str, ...]:
        # Added labels can be identified by their lack of id field
        label_names = self.get_custom_labels_names_by_task(task_name=task_name)
        return tuple(
            label_name
            for label_name in label_names
            if self.get_label_id_by_name(task_name=task_name, label_name=label_name) is None
        )

    def get_deleted_labels_names_by_task(self, task_name: str) -> tuple[str, ...]:
        # Deleted labels are marked with `is_deleted` field in the test data format
        label_names = self.get_custom_labels_names_by_task(task_name=task_name)
        return tuple(
            label_name
            for label_name in label_names
            if self.tasks_dict[task_name]["labels"][label_name].get("is_deleted", False)
        )

    def get_revisit_state_by_label_name(self, task_name: str, label_name: str) -> bool:
        # Labels requiring revisit are marked with `do_revisit` field in the test data format
        return self.tasks_dict[task_name]["labels"][label_name].get("do_revisit", False)

    def get_keypoint_structure_data(self, task_name: str) -> dict:
        task_dict = self._get_task_dict(task_name=task_name)
        return task_dict.get("keypoint_structure", {})

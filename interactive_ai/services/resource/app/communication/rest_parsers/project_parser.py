# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Parsers to create/update projects from REST representation"""

import os
from functools import lru_cache
from typing import Any

import jsonschema

from communication.rest_data_validator import ProjectRestValidator

from geti_types import ID
from iai_core.entities.model_template import TaskType
from iai_core.factories import ProjectParser, ProjectParserInternalError, ProjectUpdateParser

COLOR = "color"
CONNECTIONS = "connections"
FROM = "from"
GROUP = "group"
HOTKEY = "hotkey"
ID_ = "id"
IS_DELETED = "is_deleted"
IS_EMPTY = "is_empty"
LABELS = "labels"
NAME = "name"
PARENT_ID = "parent_id"
PIPELINE = "pipeline"
REVISIT_AFFECTED_ANNOTATIONS = "revisit_affected_annotations"
TASK_TYPE = "task_type"
TASKS = "tasks"
TITLE = "title"
TO = "to"


__all__ = [
    "RestProjectParser",
    "RestProjectUpdateParser",
]


class RestProjectParser(ProjectParser):
    """
    Parser that can read and decode the information necessary to create
    a project from the JSON-like dictionary of the project creation endpoint.

    :param rest_data: JSON-like dict input data as from the project creation endpoint
    """

    base_dir = os.path.dirname(__file__) + "/../../../../api/schemas/"
    json_schema = ProjectRestValidator().load_schema_file_as_dict(base_dir + "projects/requests/post/project.yaml")

    def __init__(self, rest_data: dict[str, Any]) -> None:
        self.__rest_data = rest_data
        # JSON-schema validation
        jsonschema.validate(rest_data, self.json_schema)

    def get_project_name(self) -> str:
        return self.__rest_data[NAME]

    def _get_connections_rest(self) -> list[dict]:
        return self.__rest_data[PIPELINE][CONNECTIONS]

    def get_connections(self) -> tuple[tuple[str, str], ...]:
        connections_rest = self._get_connections_rest()
        return tuple((conn_rest[FROM], conn_rest[TO]) for conn_rest in connections_rest)

    def _get_tasks_rest(self) -> list[dict]:
        return self.__rest_data[PIPELINE][TASKS]

    def get_tasks_names(self) -> tuple[str, ...]:
        return tuple(task_rest[TITLE] for task_rest in self._get_tasks_rest())

    @lru_cache(maxsize=4)
    def _get_task_rest(self, task_name: str) -> dict[str, Any]:
        try:
            return next(task_rest for task_rest in self._get_tasks_rest() if task_rest[TITLE] == task_name)
        except StopIteration as ex:
            if task_name not in self.get_tasks_names():
                raise ValueError(f"Task with name '{task_name}' not found") from ex
            raise ProjectParserInternalError(f"Error while fetching data for task with name '{task_name}'") from ex

    def get_task_type_by_name(self, task_name: str) -> TaskType:
        task_rest = self._get_task_rest(task_name=task_name)
        return TaskType[task_rest[TASK_TYPE].upper()]

    def get_custom_labels_names_by_task(self, task_name: str) -> tuple[str, ...]:
        task_rest = self._get_task_rest(task_name=task_name)
        return tuple(
            label_rest[NAME] for label_rest in task_rest.get("labels", []) if not label_rest.get(IS_EMPTY, False)
        )

    @lru_cache(maxsize=32)
    def _get_label_rest(self, task_name: str, label_name: str) -> dict[str, Any]:
        try:
            return next(
                label_rest
                for label_rest in self._get_task_rest(task_name=task_name)[LABELS]
                if label_rest[NAME] == label_name
            )
        except StopIteration as ex:
            if label_name not in self.get_custom_labels_names_by_task(task_name=task_name):
                raise ValueError(f"Label with name '{label_name}' not found in task '{task_name}'") from ex
            raise ProjectParserInternalError(
                f"Error while fetching data for label with name '{label_name}' in task '{task_name}'"
            ) from ex

    def get_label_group_by_name(self, task_name: str, label_name: str) -> str:
        label_rest = self._get_label_rest(task_name=task_name, label_name=label_name)
        return label_rest[GROUP]

    def get_label_hotkey_by_name(self, task_name: str, label_name: str) -> str:
        label_rest = self._get_label_rest(task_name=task_name, label_name=label_name)
        hotkey = label_rest.get(HOTKEY, "")
        return hotkey if hotkey else ""

    def get_label_color_by_name(self, task_name: str, label_name: str) -> str:
        label_rest = self._get_label_rest(task_name=task_name, label_name=label_name)
        color = label_rest.get(COLOR, "")
        return color if color else ""

    def get_label_parent_by_name(self, task_name: str, label_name: str) -> str:
        label_rest = self._get_label_rest(task_name=task_name, label_name=label_name)
        parent = label_rest.get(PARENT_ID, "")
        return parent if parent else ""

    def get_keypoint_structure_data(self, task_name: str) -> dict[str, list]:
        task_data = self._get_task_rest(task_name=task_name)
        return task_data.get("keypoint_structure", {})


class RestProjectUpdateParser(RestProjectParser, ProjectUpdateParser):
    """
    Parser that can read and decode the information necessary to update an existing
    project from the JSON-like dictionary of the project update endpoint.

    :param rest_data: JSON-like dict input data as from the project update endpoint
    """

    base_dir = os.path.dirname(__file__) + "/../../../../api/schemas/"
    json_schema = ProjectRestValidator().load_schema_file_as_dict(base_dir + "projects/requests/put/project.yaml")

    def __init__(self, rest_data: dict[str, Any]) -> None:
        super().__init__(rest_data=rest_data)

    def get_connections(self) -> tuple[tuple[ID, ID], ...]:
        connections_rest = self._get_connections_rest()
        return tuple((ID(conn_rest[FROM]), ID(conn_rest[TO])) for conn_rest in connections_rest)

    @lru_cache(maxsize=4)
    def get_task_id_by_name(self, task_name: str) -> ID:
        task_rest = self._get_task_rest(task_name=task_name)
        return task_rest[ID_]

    @lru_cache(maxsize=32)
    def get_label_id_by_name(self, task_name: str, label_name: str) -> ID | None:
        label_rest = self._get_label_rest(task_name=task_name, label_name=label_name)
        return label_rest.get(ID_)

    def get_added_labels_names_by_task(self, task_name: str) -> tuple[str, ...]:
        # Added labels can be identified by their lack of id field
        label_names = self.get_custom_labels_names_by_task(task_name=task_name)
        return tuple(
            label_name
            for label_name in label_names
            if self.get_label_id_by_name(task_name=task_name, label_name=label_name) is None
        )

    def get_deleted_labels_names_by_task(self, task_name: str) -> tuple[str, ...]:
        # Deleted labels have a field 'is_deleted=true'
        label_names = self.get_custom_labels_names_by_task(task_name=task_name)
        return tuple(
            label_name
            for label_name in label_names
            if self._get_label_rest(task_name=task_name, label_name=label_name).get(IS_DELETED, False)
        )

    def get_revisit_state_by_label_name(self, task_name: str, label_name: str) -> bool:
        label_rest = self._get_label_rest(task_name=task_name, label_name=label_name)
        return label_rest.get(REVISIT_AFFECTED_ANNOTATIONS, False)

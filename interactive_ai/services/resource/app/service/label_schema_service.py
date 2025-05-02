# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from geti_telemetry_tools import unified_tracing
from geti_types import ID, ProjectIdentifier
from iai_core_py.entities.label import Label
from iai_core_py.entities.label_schema import LabelSchema, LabelSchemaView, NullLabelSchema
from iai_core_py.repos import LabelSchemaRepo


class LabelSchemaService:
    @staticmethod
    @unified_tracing
    def get_latest_label_schema_for_project(
        project_identifier: ProjectIdentifier,
    ) -> LabelSchema:
        """
        Get the latest LabelSchema for a given project.

        The schema is loaded from the repo.

        :param project_identifier: Identifier of the project relative to the label schema
        :raises: RuntimeError if no schema is found in the repo for the project
        :return: LabelSchema object
        """
        latest_schema = LabelSchemaRepo(project_identifier).get_latest()
        if isinstance(latest_schema, NullLabelSchema):
            raise RuntimeError(f"Could not find LabelSchema for `{project_identifier}`")
        return latest_schema

    @staticmethod
    @unified_tracing
    def get_latest_label_schema_for_task(project_identifier: ProjectIdentifier, task_node_id: ID) -> LabelSchemaView:
        """
        Get the latest LabelSchemaView for a given task node.

        The schema is loaded from the repo.

        :param project_identifier: Identifier of the project relative to the label schema
        :param task_node_id: ID of the task linked with the label schema view to retrieve
        :raises: RuntimeError if no schema view is found in the repo for the task
        :return: LabelSchemaView object
        """
        latest_schema_view = LabelSchemaRepo(project_identifier).get_latest_view_by_task(task_node_id=task_node_id)
        if isinstance(latest_schema_view, NullLabelSchema):
            raise RuntimeError(
                f"Could not find LabelSchemaView for task with ID {task_node_id} of project `{project_identifier}`",
            )
        return latest_schema_view

    @staticmethod
    @unified_tracing
    def get_latest_labels_for_task(
        project_identifier: ProjectIdentifier, task_node_id: ID, include_empty: bool = False
    ) -> list[Label]:
        """
        Get the labels from the latest label schema of the given task node.

        :param project_identifier: Identifier of the project containing the task
        :param task_node_id: ID of the task linked with the label schema view from which to retrieve the labels
        :param include_empty: bool indicating whether the empty label should be included in the result
        :raises: RuntimeError if no schema view is found in the repo for the task
        :return: List of Label objects
        """
        latest_schema = LabelSchemaService.get_latest_label_schema_for_task(
            project_identifier=project_identifier, task_node_id=task_node_id
        )
        return latest_schema.get_labels(include_empty=include_empty)

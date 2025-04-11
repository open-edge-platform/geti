# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
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

from geti_telemetry_tools import unified_tracing
from geti_types import ID, ProjectIdentifier
from sc_sdk.entities.label import Label
from sc_sdk.entities.label_schema import LabelSchema, LabelSchemaView, NullLabelSchema
from sc_sdk.repos import LabelSchemaRepo


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

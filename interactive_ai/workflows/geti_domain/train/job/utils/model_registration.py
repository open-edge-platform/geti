# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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

"""Utilities to convert entities to model registration protobufs"""

from geti_types import ID
from grpc_interfaces.model_registration.pb.service_pb2 import Connection, Label, Model, Pipeline, Project, Task
from sc_sdk.entities.label import Label as SdkLabel
from sc_sdk.entities.label_schema import LabelGroup as SdkLabelGroup
from sc_sdk.entities.model import Model as SdkModel
from sc_sdk.entities.project import Project as SdkProject
from sc_sdk.entities.task_node import TaskNode as SdkTask
from sc_sdk.repos import LabelSchemaRepo


class ProjectMapper:
    @staticmethod
    def forward(project: SdkProject) -> Project:
        return Project(
            id=str(project.id_),
            name=project.name,
            pipeline=Pipeline(
                tasks=[TaskMapper.forward(task, project) for task in project.tasks],
                connections=[
                    ConnectionMapper.forward(project.tasks[i].id_, project.tasks[i + 1].id_)
                    for i, task in enumerate(project.tasks[1:])
                ],
            ),
        )


class TaskMapper:
    @staticmethod
    def forward(task: SdkTask, project: SdkProject) -> Task:
        if task.task_properties.is_trainable:
            label_schema_view = LabelSchemaRepo(project.identifier).get_latest_view_by_task(task.id_)
            label_groups = label_schema_view.get_groups(include_empty=True)
            labels = []
            for group in label_groups:
                for label in group.labels:
                    labels.append(LabelMapper.forward(label, group))  # type: ignore
            grpc_task = Task(
                id=str(task.id_), title=task.title, task_type=task.task_properties.task_type.name, labels=labels
            )
        else:
            grpc_task = Task(
                id=str(task.id_),
                title=task.title,
                task_type=task.task_properties.task_type.name,
            )
        return grpc_task


class LabelMapper:
    @staticmethod
    def forward(label: SdkLabel, group: SdkLabelGroup) -> Label:
        return Label(
            id=str(label.id_),
            name=label.name,
            is_anomalous=label.is_anomalous,
            is_empty=label.is_empty,
            group=group.name,
        )


class ConnectionMapper:
    @staticmethod
    def forward(from_connection: ID, to_id: ID) -> Connection:
        return Connection(from_id=str(from_connection), to_id=str(to_id))


class ModelMapper:
    @staticmethod
    def forward(
        model: SdkModel, project_id: ID, workspace_id: ID, optimized_model_id: ID, task_id: ID, organization_id: ID
    ) -> Model:
        return Model(
            workspace_id=str(workspace_id),
            project_id=str(project_id),
            model_group_id=str(model.model_storage.id_),
            model_id=str(model.id_),
            optimized_model_id=str(optimized_model_id),
            task_id=str(task_id),
            organization_id=str(organization_id),
        )

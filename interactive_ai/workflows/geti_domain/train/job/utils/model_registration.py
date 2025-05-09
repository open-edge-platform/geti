# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Utilities to convert entities to model registration protobufs"""

from geti_types import ID
from grpc_interfaces.model_registration.pb.service_pb2 import Connection, Label, Model, Pipeline, Project, Task
from iai_core.entities.label import Label as SdkLabel
from iai_core.entities.label_schema import LabelGroup as SdkLabelGroup
from iai_core.entities.model import Model as SdkModel
from iai_core.entities.project import Project as SdkProject
from iai_core.entities.task_node import TaskNode as SdkTask
from iai_core.repos import LabelSchemaRepo


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
                id=str(task.id_),
                title=task.title,
                task_type=task.task_properties.task_type.name,
                labels=labels,
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
        model: SdkModel,
        project_id: ID,
        workspace_id: ID,
        optimized_model_id: ID,
        task_id: ID,
        organization_id: ID,
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

# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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
from unittest.mock import patch

import pytest
from grpc_interfaces.model_registration.pb.service_pb2 import Connection, Model, Pipeline, Project, Task
from sc_sdk.repos import LabelSchemaRepo

from job.utils.model_registration import LabelMapper, ModelMapper, ProjectMapper


@pytest.mark.JobsSdkComponent
class TestModelRegistrationProtoMapper:
    def test_grpc_project_mapper(self, fxt_detection_project, fxt_label_schema):
        project = fxt_detection_project
        label_groups = fxt_label_schema.get_groups(include_empty=True)
        expected_labels = []
        for group in label_groups:
            for label in group.labels:
                expected_labels.append(LabelMapper.forward(label, group))  # type: ignore
        expected_project = Project(
            id=str(project.id_),
            name=str(project.name),
            pipeline=Pipeline(
                tasks=[
                    Task(
                        id=str(project.tasks[0].id_),
                        title=project.tasks[0].title,
                        task_type=project.tasks[0].task_properties.task_type.name,
                        labels=expected_labels,
                    ),
                    Task(
                        id=str(project.tasks[1].id_),
                        title=project.tasks[1].title,
                        task_type=project.tasks[1].task_properties.task_type.name,
                        labels=expected_labels,
                    ),
                ],
                connections=[Connection(from_id=str(project.tasks[0].id_), to_id=str(project.tasks[1].id_))],
            ),
        )

        with patch.object(LabelSchemaRepo, "get_latest_view_by_task", return_value=fxt_label_schema):
            mapped_project = ProjectMapper.forward(project=project)
        assert mapped_project == expected_project

    def test_grpc_model_mapper(self, fxt_model, fxt_mongo_id):
        mapped_model = ModelMapper.forward(
            model=fxt_model,
            project_id=fxt_mongo_id(1),
            workspace_id=fxt_mongo_id(2),
            optimized_model_id=fxt_mongo_id(3),
            task_id=fxt_mongo_id(4),
            organization_id=fxt_mongo_id(5),
        )
        expected_model = Model(
            workspace_id=str(fxt_mongo_id(2)),
            project_id=str(fxt_mongo_id(1)),
            model_group_id=str(fxt_model.model_storage.id_),
            model_id=str(fxt_model.id_),
            optimized_model_id=str(fxt_mongo_id(3)),
            task_id=fxt_mongo_id(4),
            organization_id=fxt_mongo_id(5),
        )

        assert mapped_model == expected_model

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
from grpc_interfaces.model_registration.client import ModelRegistrationClient
from grpc_interfaces.model_registration.pb.service_pb2 import (
    Chunk,
    Connection,
    DownloadGraphRequest,
    Label,
    Model,
    Pipeline,
    Project,
    PurgeProjectRequest,
    PurgeProjectResponse,
    RegisterRequest,
    StatusResponse,
    Task,
)


def do_nothing(*args, **kwargs):
    pass


@pytest.fixture
def fxt_grpc_client():
    client = ModelRegistrationClient(metadata_getter=lambda: (("key", "value"),))
    client.model_registration_stub = MagicMock()
    yield client


@pytest.fixture
def fxt_proto_project():
    yield Project(
        id="project_id",
        name="project_name",
        pipeline=Pipeline(
            tasks=[
                Task(id="task_id_1", title="dataset_task", task_type="dataset", labels=None),
                Task(
                    id="task_id_2",
                    title="detection_task",
                    task_type="detection",
                    labels=[
                        Label(
                            id="label_id",
                            name="object",
                            group="group",
                            is_empty=False,
                            is_anomalous=False,
                            parent_id="parent_id",
                        )
                    ],
                ),
            ],
            connections=[Connection(from_id="task_id_1", to_id="task_id_2")],
        ),
    )


@pytest.fixture
def fxt_proto_model():
    yield Model(
        organization_id="organization_id",
        workspace_id="workspace_id",
        project_id="project_id",
        model_group_id="model_group_id",
        model_id="model_id",
        optimized_model_id="optimized_model_id",
        task_id="task_id",
    )


class TestModelRegistrationClient:
    def test_register(self, fxt_grpc_client, fxt_proto_project, fxt_proto_model) -> None:
        # Arrange
        response = StatusResponse(status="CREATED")
        expected_grpc_message = RegisterRequest(
            name="dummy-active", project=fxt_proto_project, model=[fxt_proto_model], override=True
        )
        with patch.object(
            fxt_grpc_client.model_registration_stub, "register_new_pipelines", return_value=response
        ) as mocked_register:
            # Act
            fxt_grpc_client.register(
                name="dummy-active",
                project=fxt_proto_project,
                models=[fxt_proto_model],
                override=True,
            )

        # Assert
        mocked_register.assert_called_once_with(expected_grpc_message, metadata=(("key", "value"),))

    def test_register_sporadic_failure(self, fxt_grpc_client, fxt_proto_project, fxt_proto_model) -> None:
        # Arrange
        success_response = StatusResponse(status="CREATED")
        failure_response = StatusResponse(status="FAILED")
        expected_grpc_message = RegisterRequest(
            name="dummy-active", project=fxt_proto_project, model=[fxt_proto_model], override=True
        )
        with (
            patch.object(
                fxt_grpc_client.model_registration_stub,
                "register_new_pipelines",
                side_effect=[failure_response, success_response],
            ) as mocked_register,
            patch("time.sleep", return_value=None),
        ):
            # Act
            fxt_grpc_client.register(
                name="dummy-active",
                project=fxt_proto_project,
                models=[fxt_proto_model],
                override=True,
            )

        # Assert
        expected_calls = [call(expected_grpc_message, metadata=(("key", "value"),)) for _ in range(2)]
        mocked_register.assert_has_calls(expected_calls)

    def test_register_permanent_failure(self, fxt_grpc_client, fxt_proto_project, fxt_proto_model) -> None:
        # Arrange
        failure_response = StatusResponse(status="FAILED")
        expected_grpc_message = RegisterRequest(
            name="dummy-active", project=fxt_proto_project, model=[fxt_proto_model], override=True
        )
        with (
            patch.object(
                fxt_grpc_client.model_registration_stub, "register_new_pipelines", return_value=failure_response
            ) as mocked_register,
            patch("time.sleep", return_value=None),
            pytest.raises(RuntimeError),
        ):
            # Act
            fxt_grpc_client.register(
                name="dummy-active",
                project=fxt_proto_project,
                models=[fxt_proto_model],
                override=True,
            )

        # Assert
        expected_calls = [
            call(expected_grpc_message, metadata=(("key", "value"),))
            for _ in range(ModelRegistrationClient.RETRY_MAX_ATTEMPTS)
        ]
        mocked_register.assert_has_calls(expected_calls)

    def test_delete_project_pipelines(self, fxt_grpc_client) -> None:
        # Arrange
        success_response = PurgeProjectResponse(success=True)
        expected_grpc_message = PurgeProjectRequest(project_id="project_id")
        with patch.object(
            fxt_grpc_client.model_registration_stub, "delete_project_pipelines", return_value=success_response
        ) as mocked_delete:
            # Act
            fxt_grpc_client.delete_project_pipelines("project_id")

        # Assert
        mocked_delete.assert_called_once_with(expected_grpc_message, metadata=(("key", "value"),))

    def test_download_graph(self, fxt_grpc_client, fxt_proto_project, fxt_proto_model) -> None:
        # Arrange
        expected_grpc_message = DownloadGraphRequest(project=fxt_proto_project, models=[fxt_proto_model])
        with (
            patch.object(
                fxt_grpc_client.model_registration_stub,
                "download_graph",
                return_value=[Chunk(buffer=b"test1"), Chunk(buffer=b"test2")],
            ) as mocked_download_graph,
            tempfile.TemporaryDirectory() as tmp_dir,
        ):
            output_path = Path(tmp_dir) / "test_graph"
            # Act
            fxt_grpc_client.download_graph(project=fxt_proto_project, models=[fxt_proto_model], output_path=output_path)
            # Assert
            mocked_download_graph.assert_called_once_with(expected_grpc_message, metadata=(("key", "value"),))
            with open(output_path) as output_file:
                assert output_file.readline() == "test1test2"

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from grpc.aio import ServicerContext
from grpc_interfaces.model_registration.pb.service_pb2 import (
    ActiveRequest,
    DeregisterRequest,
    ListRequest,
    PurgeProjectRequest,
    RecoverRequest,
    RegisterRequest,
)
from kubernetes_asyncio.client.rest import ApiException

from service.config import MODELMESH_NAMESPACE, S3_STORAGE
from service.model_registration import ModelRegistration
from service.responses import Responses


@pytest.fixture
def servicer_context():
    return AsyncMock(spec=ServicerContext)


@pytest.fixture
def s3_client(mocker):
    return mocker.patch("service.model_registration.S3Client")


@pytest.fixture
def converter(mocker):
    return mocker.patch("service.model_registration.ModelConverter")


@pytest.fixture
def model_registration(s3_client, converter):
    return ModelRegistration()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name, override, expected_response",
    [
        ("test", True, Responses.Created),
        ("test", False, Responses.AlreadyRegistered),
        ("new", False, Responses.Created),
    ],
)
@patch("service.model_registration.InferenceManager.create_inference")
@patch("service.model_registration.InferenceManager.get_inference")
@patch("service.model_registration.InferenceManager.remove_inference")
async def test_register_new_pipelines(
    remove_inference,
    get_inference,
    create_inference,
    model_registration,
    converter,
    servicer_context,
    name,
    override,
    expected_response,
):
    pipeline = MagicMock()
    get_inference.side_effect = AsyncMock(return_value=pipeline if name == "test" else None)
    create_inference.side_effect = AsyncMock()
    remove_inference.side_effect = AsyncMock()

    req = RegisterRequest(name=name, override=override)
    response = await model_registration.register_new_pipelines(req, servicer_context)

    assert response.status == expected_response
    get_inference.assert_awaited_once()
    if override:
        remove_inference.assert_awaited_once()
    if expected_response == Responses.Created:
        converter.assert_called_once()
        create_inference.assert_awaited_once_with(
            name=name, namespace=MODELMESH_NAMESPACE, storage_name=S3_STORAGE, path=name
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "reason, expected_response",
    [
        ("Conflict", Responses.AlreadyRegistered),
        ("SomethingElse", Responses.Failed),
    ],
)
@patch("service.model_registration.InferenceManager.get_inference")
async def test_register_new_pipelines_failed(
    get_inference, model_registration, servicer_context, reason, expected_response
):
    get_inference.side_effect = ApiException(reason=reason)
    req = RegisterRequest(name="test", override=False)
    response = await model_registration.register_new_pipelines(req, servicer_context)
    assert response.status == expected_response


@pytest.mark.asyncio
@patch("service.model_registration.InferenceManager.get_inference")
async def test_register_new_pipelines_error(get_inference, model_registration, servicer_context):
    get_inference.side_effect = RuntimeError()
    req = RegisterRequest(name="test", override=False)
    response = await model_registration.register_new_pipelines(req, servicer_context)
    assert response.status == Responses.Failed


@pytest.mark.asyncio
@patch("service.model_registration.InferenceManager.remove_inference")
async def test_deregister_pipeline(remove_inference, model_registration, servicer_context):
    remove_inference.side_effect = AsyncMock()

    req = DeregisterRequest(name="test")
    response = await model_registration.deregister_pipeline(req, servicer_context)

    assert response.status == "REMOVED"
    remove_inference.assert_awaited_once()


@pytest.mark.asyncio
@patch("service.model_registration.InferenceManager.remove_inference")
async def test_deregister_pipeline_faile(remove_inference, model_registration, servicer_context):
    remove_inference.side_effect = ApiException()

    req = DeregisterRequest(name="test")
    response = await model_registration.deregister_pipeline(req, servicer_context)

    assert response.status == "FAILED"
    remove_inference.assert_awaited_once()


@pytest.mark.asyncio
async def test_register_active_pipeline(model_registration, servicer_context):
    req = ActiveRequest()
    response = await model_registration.register_active_pipeline(req, servicer_context)
    assert response.status == "NOT_IMPLEMENTED"


@pytest.mark.asyncio
@patch("service.model_registration.InferenceManager.list_inference")
async def test_list_pipeline(list_inference, model_registration, servicer_context):
    pipeline1 = MagicMock()
    pipeline1.name = "model1"
    pipeline2 = MagicMock()
    pipeline2.name = "model2"
    list_inference.side_effect = AsyncMock(return_value=[pipeline1, pipeline2])

    req = ListRequest()
    response = await model_registration.list_pipelines(req, servicer_context)

    assert response.pipelines == ["model1", "model2"]
    list_inference.assert_awaited_once()


@pytest.mark.asyncio
@patch("service.model_registration.InferenceManager.list_inference")
async def test_list_pipeline_fail(list_inference, model_registration, servicer_context):
    list_inference.side_effect = ApiException()
    req = ListRequest()
    response = await model_registration.list_pipelines(req, servicer_context)
    assert response.pipelines == []


@pytest.mark.asyncio
@patch("service.model_registration.InferenceManager.list_inference")
async def test_recover_pipelines_registered(list_inference, model_registration, servicer_context):
    pipeline = MagicMock()
    pipeline.name = "test"
    list_inference.side_effect = AsyncMock(return_value=[pipeline])

    req = RecoverRequest(name="test")
    response = await model_registration.recover_pipeline(req, servicer_context)

    assert response.success is True
    list_inference.assert_awaited_once()


@pytest.mark.asyncio
@patch("service.model_registration.InferenceManager.list_inference")
@patch("service.model_registration.InferenceManager.create_inference")
async def test_recover_pipelines_notregistered(create_inference, list_inference, model_registration, servicer_context):
    list_inference.side_effect = AsyncMock()
    create_inference.side_effect = AsyncMock()

    req = RecoverRequest(name="test")
    response = await model_registration.recover_pipeline(req, servicer_context)

    assert response.success is True
    list_inference.assert_awaited_once()
    create_inference.assert_awaited_once()


@pytest.mark.asyncio
@patch("service.model_registration.InferenceManager.list_inference")
async def test_recover_pipelines_no_recover(list_inference, model_registration, servicer_context, s3_client):
    list_inference.side_effect = AsyncMock()
    s3_client.return_value.check_folder_exists.return_value = False

    req = RecoverRequest(name="test")
    response = await model_registration.recover_pipeline(req, servicer_context)

    assert response.success is False
    list_inference.assert_awaited_once()


@pytest.mark.asyncio
@patch("service.model_registration.InferenceManager.list_inference")
@patch("service.model_registration.InferenceManager.remove_inference")
async def test_delete_project_pipelines(
    remove_inference, list_inference, model_registration, servicer_context, s3_client
):
    pipeline = MagicMock()
    pipeline.name = "test-test"
    list_inference.side_effect = AsyncMock(return_value=[pipeline])
    s3_client.return_value.list_folders.return_value = ["test-"]

    req = PurgeProjectRequest(project_id="test")
    response = await model_registration.delete_project_pipelines(req, servicer_context)

    assert response.success is True
    list_inference.assert_awaited_once()
    remove_inference.assert_awaited_once()
    s3_client.return_value.list_folders.assert_called_once()
    s3_client.return_value.delete_folder.assert_called() == 2


@pytest.mark.asyncio
@patch("service.model_registration.InferenceManager.list_inference")
@patch("service.model_registration.InferenceManager.remove_inference")
async def test_delete_project_pipelines_remove_fail(
    remove_inference, list_inference, model_registration, servicer_context, s3_client
):
    pipeline = MagicMock()
    pipeline.name = "test-test"
    list_inference.side_effect = AsyncMock(return_value=[pipeline])
    remove_inference.side_effect = RuntimeError()

    req = PurgeProjectRequest(project_id="test")
    response = await model_registration.delete_project_pipelines(req, servicer_context)

    assert response.success is False
    list_inference.assert_awaited_once()
    remove_inference.assert_awaited_once()
    s3_client.return_value.list_folders.assert_called_once()
    s3_client.return_value.delete_folder.assert_not_called()


@pytest.mark.asyncio
@patch("service.model_registration.InferenceManager.list_inference")
async def test_delete_project_pipelines_delete_failed(list_inference, model_registration, servicer_context, s3_client):
    s3_client.return_value.list_folders.return_value = ["test-"]
    s3_client.return_value.delete_folder.side_effect = ClientError(
        {"Error": {"Code": 500, "Message": "Error"}}, "get_object"
    )

    req = PurgeProjectRequest(project_id="test")
    response = await model_registration.delete_project_pipelines(req, servicer_context)

    assert response.success is False
    list_inference.assert_awaited_once()
    s3_client.return_value.list_folders.assert_called_once()
    s3_client.return_value.delete_folder.assert_called_once()

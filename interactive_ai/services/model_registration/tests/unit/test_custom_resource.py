# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

import http
from unittest.mock import MagicMock

import pytest
from asynctest import CoroutineMock

from service.custom_resource import ApiException, CustomObjectsApi, CustomResource


class FakeCR(CustomResource):
    api_group_name = "test.test"
    crd_plural_name = "tests"
    crd_version = "v1"


@pytest.fixture(autouse=True)
def mock_k8s_api_client(mocker):
    api_mock = MagicMock()
    api_mock.list_namespaced_custom_object = CoroutineMock()
    return mocker.patch("service.custom_resource.K8SApiClient.get", return_value=api_mock)


@pytest.fixture(autouse=True)
def mock_cr_api_client(mocker):
    custom_objects_api_mock: CustomObjectsApi = MagicMock(spec=CustomObjectsApi)  # type: ignore
    mocker.patch(
        "service.custom_resource.CustomResourceApiClient.thread_local_storage.k8s_custom_object_api",
        custom_objects_api_mock,
    )

    custom_objects_api_mock.list_cluster_custom_object = CoroutineMock()
    custom_objects_api_mock.list_namespaced_custom_object = CoroutineMock()
    custom_objects_api_mock.get_cluster_custom_object = CoroutineMock()
    custom_objects_api_mock.get_namespaced_custom_object = CoroutineMock()
    custom_objects_api_mock.patch_namespaced_custom_object = CoroutineMock()
    custom_objects_api_mock.create_namespaced_custom_object = CoroutineMock()
    custom_objects_api_mock.delete_namespaced_custom_object = CoroutineMock()
    custom_objects_api_mock.delete_cluster_custom_object = CoroutineMock()
    return custom_objects_api_mock


def test_from_k8s_response_dict():
    name = "test"
    namespace = "test-namespace"
    test_field_value = "foo"

    cr = FakeCR.from_k8s_response_dict(
        {
            "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
            "kind": FakeCR.__name__,
            "metadata": {"name": name, "namespace": namespace},
            "spec": {"testField": test_field_value},
        }
    )

    assert cr.name == name
    assert cr.namespace == namespace
    assert cr.body["spec"]["testField"] == test_field_value


def test_from_yaml(tmpdir):
    name = "test"
    namespace = "test-namespace"
    test_field_value = "foo"

    yaml_file_path = tmpdir.join("test.yaml")
    yaml_content = f"""
---
apiVersion: test.test/v1
kind: TestCR
metadata:
  name: {name}
  namespace: {namespace}
spec:
  testField: {test_field_value}
"""
    with open(yaml_file_path, mode="w") as yaml_file:
        yaml_file.write(yaml_content)

    cr = FakeCR.from_yaml(yaml_file_path)

    assert cr.name == name
    assert cr.namespace == namespace
    assert cr.body["spec"]["testField"] == test_field_value


@pytest.mark.asyncio
async def test_get(mock_cr_api_client: CustomObjectsApi):
    test_cr = FakeCR(
        body={
            "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
            "kind": FakeCR.__name__,
            "metadata": {"name": "test-1", "namespace": "test-namespace"},
            "spec": {"testField": "foo"},
        }
    )

    mock_cr_api_client.get_namespaced_custom_object.return_value = {
        "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
        "kind": FakeCR.__name__,
        "metadata": {"name": test_cr.name, "namespace": test_cr.namespace},
        "spec": {"testField": test_cr.body["spec"]["testField"]},
    }

    assert await FakeCR.get(name=test_cr.name, namespace=test_cr.namespace) == test_cr


@pytest.mark.asyncio
async def test_list_namespace(mock_cr_api_client: CustomObjectsApi):
    test_crs = [
        FakeCR(
            body={
                "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
                "kind": FakeCR.__name__,
                "metadata": {"name": "test-1", "namespace": "test-namespace"},
                "spec": {"testField": "foo"},
            }
        ),
        FakeCR(
            body={
                "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
                "kind": FakeCR.__name__,
                "metadata": {"name": "test-2", "namespace": "test-namespace"},
                "spec": {"testField": "bar"},
            }
        ),
    ]

    mock_cr_api_client.list_namespaced_custom_object.return_value = {
        "items": [
            {
                "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
                "kind": FakeCR.__name__,
                "metadata": {"name": cr.name, "namespace": cr.namespace},
                "spec": {"testField": cr.body["spec"]["testField"]},
            }
            for cr in test_crs
        ]
    }

    assert await FakeCR.list(namespace="test-namespace") == test_crs


@pytest.mark.asyncio
async def test_iterate(mock_cr_api_client: CustomObjectsApi):
    test_crs = [
        FakeCR(
            body={
                "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
                "kind": FakeCR.__name__,
                "metadata": {"name": "test-1", "namespace": "test-namespace"},
                "spec": {"testField": "foo"},
            }
        ),
        FakeCR(
            body={
                "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
                "kind": FakeCR.__name__,
                "metadata": {"name": "test-2", "namespace": "test-namespace"},
                "spec": {"testField": "bar"},
            }
        ),
    ]

    mock_cr_api_client.list_namespaced_custom_object.side_effect = [
        {
            "items": [
                {
                    "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
                    "kind": FakeCR.__name__,
                    "metadata": {"name": test_crs[0].name, "namespace": test_crs[0].namespace},
                    "spec": {"testField": test_crs[0].body["spec"]["testField"]},
                }
            ],
            "metadata": {"continue": "bla"},
        },
        {
            "items": [
                {
                    "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
                    "kind": FakeCR.__name__,
                    "metadata": {"name": test_crs[1].name, "namespace": test_crs[1].namespace},
                    "spec": {"testField": test_crs[1].body["spec"]["testField"]},
                }
            ],
            "metadata": {"continue": None},
        },
    ]

    assert [fake_cr async for fake_cr in FakeCR.iterate(limit=1, namespace="test-namespace")] == test_crs
    assert mock_cr_api_client.list_namespaced_custom_object.call_count == 2


@pytest.mark.asyncio
async def test_list_clusterwide(mock_cr_api_client: CustomObjectsApi):
    test_crs = [
        FakeCR(
            body={
                "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
                "kind": FakeCR.__name__,
                "metadata": {"name": "test-1", "namespace": "test-namespace-1"},
                "spec": {"testField": "foo"},
            }
        ),
        FakeCR(
            body={
                "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
                "kind": FakeCR.__name__,
                "metadata": {"name": "test-2", "namespace": "test-namespace-2"},
                "spec": {"testField": "bar"},
            }
        ),
    ]

    mock_cr_api_client.list_cluster_custom_object.return_value = {
        "items": [
            {
                "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
                "kind": FakeCR.__name__,
                "metadata": {"name": cr.name, "namespace": cr.namespace},
                "spec": {"testField": cr.body["spec"]["testField"]},
            }
            for cr in test_crs
        ]
    }

    assert await FakeCR.list() == test_crs


@pytest.mark.asyncio
async def test_create(mock_cr_api_client: CustomObjectsApi):
    name = "test"
    namespace = "test-namespace"
    test_field_value = "foo"

    body = {
        "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
        "kind": FakeCR.__name__,
        "metadata": {"name": name, "namespace": namespace},
        "spec": {"testField": test_field_value},
    }

    test_cr = FakeCR(body=body)

    mock_cr_api_client.create_namespaced_custom_object.return_value = body

    assert await test_cr.create() == body


@pytest.mark.asyncio
async def test_create_fail(mock_cr_api_client: CustomObjectsApi):
    name = "test"
    namespace = "test-namespace"
    test_field_value = "foo"

    body = {
        "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
        "kind": FakeCR.__name__,
        "metadata": {"name": name, "namespace": namespace},
        "spec": {"testField": test_field_value},
    }

    test_cr = FakeCR(body=body)

    mock_cr_api_client.create_namespaced_custom_object.side_effect = ApiException

    with pytest.raises(ApiException):
        await test_cr.create()


@pytest.mark.asyncio
async def test_delete(mock_cr_api_client: CustomObjectsApi):
    name = "test"
    namespace = "test-namespace"
    test_field_value = "foo"

    body = {
        "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
        "kind": FakeCR.__name__,
        "metadata": {"name": name, "namespace": namespace},
        "spec": {"testField": test_field_value},
    }

    test_cr = FakeCR(body=body)

    await test_cr.delete()
    assert mock_cr_api_client.delete_namespaced_custom_object.call_count == 1


@pytest.mark.asyncio
async def test_delete_clusterwide(mock_cr_api_client: CustomObjectsApi):
    name = "test"
    test_field_value = "foo"

    body = {
        "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
        "kind": FakeCR.__name__,
        "metadata": {"name": name},
        "spec": {"testField": test_field_value},
    }

    test_cr = FakeCR(body=body)

    await test_cr.delete()
    assert mock_cr_api_client.delete_cluster_custom_object.call_count == 1


@pytest.mark.asyncio
async def test_delete_not_found(mock_cr_api_client: CustomObjectsApi):
    name = "test"
    namespace = "test-namespace"
    test_field_value = "foo"

    body = {
        "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
        "kind": FakeCR.__name__,
        "metadata": {"name": name, "namespace": namespace},
        "spec": {"testField": test_field_value},
    }

    test_cr = FakeCR(body=body)

    mock_cr_api_client.delete_namespaced_custom_object.return_value = ApiException(status=http.HTTPStatus.NOT_FOUND)

    await test_cr.delete()
    assert mock_cr_api_client.delete_namespaced_custom_object.call_count == 1


@pytest.mark.asyncio
async def test_delete_fail(mock_cr_api_client: CustomObjectsApi):
    name = "test"
    namespace = "test-namespace"
    test_field_value = "foo"

    body = {
        "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
        "kind": FakeCR.__name__,
        "metadata": {"name": name, "namespace": namespace},
        "spec": {"testField": test_field_value},
    }

    test_cr = FakeCR(body=body)

    mock_cr_api_client.delete_namespaced_custom_object.side_effect = ApiException(
        status=http.HTTPStatus.INTERNAL_SERVER_ERROR
    )

    with pytest.raises(ApiException):
        await test_cr.delete()


@pytest.mark.asyncio
async def test_patch_single_field(mock_cr_api_client: CustomObjectsApi):
    name = "test"
    namespace = "test-namespace"
    test_field_value = "foo"

    body = {
        "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
        "kind": FakeCR.__name__,
        "metadata": {"name": name, "namespace": namespace},
        "spec": {"testField": test_field_value},
    }

    test_cr = FakeCR(body=body)
    test_cr.labels = {"test-label": "test-value"}
    await test_cr.patch()

    expected_patch_arguments = {
        "group": FakeCR.api_group_name,
        "namespace": test_cr.namespace,
        "plural": FakeCR.crd_plural_name,
        "version": FakeCR.crd_version,
        "name": test_cr.name,
        "body": {"metadata": {"labels": test_cr.labels}},
        "_content_type": "application/merge-patch+json",
    }
    mock_cr_api_client.patch_namespaced_custom_object.assert_called_once_with(**expected_patch_arguments)


@pytest.mark.asyncio
async def test_patch_multiple_fields(mock_cr_api_client: CustomObjectsApi):
    name = "test"
    namespace = "test-namespace"
    test_field_value = "foo"

    body = {
        "apiVersion": f"{FakeCR.api_group_name}/{FakeCR.crd_version}",
        "kind": FakeCR.__name__,
        "metadata": {"name": name, "namespace": namespace},
        "spec": {"testField": test_field_value},
    }

    test_cr = FakeCR(body=body)
    test_cr.labels = {"test-label": "test-value"}
    test_cr.owner_references = [{"owner": "foo"}]
    test_cr.annotations = {"bla": "ble"}
    test_cr.status = {"status": "CREATING", "message": "OK"}
    await test_cr.patch()

    expected_patch_arguments = {
        "group": FakeCR.api_group_name,
        "namespace": test_cr.namespace,
        "plural": FakeCR.crd_plural_name,
        "version": FakeCR.crd_version,
        "name": test_cr.name,
        "body": {
            "metadata": {
                "labels": test_cr.labels,
                "ownerReferences": test_cr.owner_references,
                "annotations": test_cr.annotations,
            },
            "status": test_cr.status,
        },
        "_content_type": "application/merge-patch+json",
    }
    mock_cr_api_client.patch_namespaced_custom_object.assert_called_once_with(**expected_patch_arguments)

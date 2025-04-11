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

import threading

import pytest
from asynctest import CoroutineMock

from service.custom_resource import CustomResourceApiClient, K8SApiClient


@pytest.fixture()
def load_kube_config_mock(mocker):
    return mocker.patch("service.custom_resource.config.load_kube_config", new=CoroutineMock())


@pytest.fixture()
def load_incluster_config_mock(mocker):
    return mocker.patch("service.custom_resource.config.load_incluster_config")


@pytest.fixture(autouse=True)
def kubernetes_client_mock(mocker):
    return mocker.patch("service.custom_resource.client")


@pytest.mark.asyncio
async def test_k8s_api_client_incluster(load_kube_config_mock, load_incluster_config_mock):
    load_kube_config_mock.side_effect = FileNotFoundError
    K8SApiClient.thread_local_storage = threading.local()
    await K8SApiClient.get()

    assert load_kube_config_mock.call_count == 1
    assert load_incluster_config_mock.call_count == 1


@pytest.mark.asyncio
async def test_k8s_api_client_kubeconfig(load_kube_config_mock, load_incluster_config_mock):
    load_kube_config_mock.side_effect = None
    K8SApiClient.thread_local_storage = threading.local()
    await K8SApiClient.get()

    assert load_kube_config_mock.call_count == 1
    assert load_incluster_config_mock.call_count == 0


@pytest.mark.asyncio
async def test_k8s_api_client_failure(load_kube_config_mock, load_incluster_config_mock):
    load_kube_config_mock.side_effect = RuntimeError
    K8SApiClient.thread_local_storage = threading.local()
    with pytest.raises(RuntimeError):
        await K8SApiClient.get()


@pytest.mark.asyncio
async def test_k8s_api_client_get_twice(load_kube_config_mock, load_incluster_config_mock):
    load_kube_config_mock.side_effect = None
    K8SApiClient.thread_local_storage = threading.local()
    await K8SApiClient.get()

    assert load_kube_config_mock.call_count == 1
    assert load_incluster_config_mock.call_count == 0

    await K8SApiClient.get()

    assert load_kube_config_mock.call_count == 1
    assert load_incluster_config_mock.call_count == 0


@pytest.mark.asyncio
async def test_custom_resource_client_incluster(load_kube_config_mock, load_incluster_config_mock):
    load_kube_config_mock.side_effect = FileNotFoundError
    CustomResourceApiClient.thread_local_storage = threading.local()
    await CustomResourceApiClient.get()

    assert load_kube_config_mock.call_count == 1
    assert load_incluster_config_mock.call_count == 1


@pytest.mark.asyncio
async def test_custom_resource_api_client_kubeconfig(load_kube_config_mock, load_incluster_config_mock):
    load_kube_config_mock.side_effect = None
    CustomResourceApiClient.thread_local_storage = threading.local()
    await CustomResourceApiClient.get()

    assert load_kube_config_mock.call_count == 1
    assert load_incluster_config_mock.call_count == 0


@pytest.mark.asyncio
async def test_custom_resource_api_client_failure(load_kube_config_mock, load_incluster_config_mock):
    load_kube_config_mock.side_effect = RuntimeError
    CustomResourceApiClient.thread_local_storage = threading.local()
    with pytest.raises(RuntimeError):
        await CustomResourceApiClient.get()


@pytest.mark.asyncio
async def test_custom_resource_api_client_get_twice(load_kube_config_mock, load_incluster_config_mock):
    load_kube_config_mock.side_effect = None
    CustomResourceApiClient.thread_local_storage = threading.local()
    await CustomResourceApiClient.get()

    assert load_kube_config_mock.call_count == 1
    assert load_incluster_config_mock.call_count == 0

    await CustomResourceApiClient.get()

    assert load_kube_config_mock.call_count == 1
    assert load_incluster_config_mock.call_count == 0

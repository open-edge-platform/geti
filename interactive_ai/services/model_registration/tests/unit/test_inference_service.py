# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from service.inference_service import InferenceService


def test_inferenceservice():
    name = "test"
    namespace = "test_ns"
    apiVersion = "v1"
    body = {"metadata": {"name": name, "namespace": namespace}, "apiVersion": apiVersion}

    service = InferenceService(name, namespace, body=body)

    assert service.name == name
    assert service.namespace == namespace
    assert service.body == body
    assert service.body["apiVersion"] == apiVersion


def test_inferenceservice_no_body():
    name = "test"
    namespace = "test_ns"
    storage_name = "storage"
    path = "test_path"

    service = InferenceService(name, namespace, storage_name=storage_name, path=path)

    assert service.name == name
    assert service.namespace == namespace
    assert service.body is not None
    assert service.body["apiVersion"] == f"{InferenceService.api_group_name}/{InferenceService.crd_version}"
    assert service.body["kind"] == f"{InferenceService.__name__}"

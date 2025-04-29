"""Tests the inference service module."""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

import inference_services


@pytest.mark.parametrize(
    "current_date,infservice_timestamp,max_hours,expected_result",
    [
        ("2024-10-21T10:00:00", "2024-08-21T10:00:00Z", 48, True),
        ("2024-10-21T10:00:00", "2024-10-20T10:00:00Z", 48, False),
        ("2024-10-21T10:00:00", "2024-10-21T10:00:00Z", 48, False),
    ],
)
def test_is_inference_service_older_than_threshold(
    mocker, current_date, infservice_timestamp, max_hours, expected_result
):
    get_utc_now_mock = mocker.patch("inference_services.get_utc_now")

    get_utc_now_mock.return_value = datetime.datetime.fromisoformat(current_date).replace(tzinfo=datetime.timezone.utc)

    inference_service_metadata = {"creationTimestamp": infservice_timestamp}

    assert (
        inference_services.is_inference_service_older_than_threshold(
            inference_service_metadata=inference_service_metadata, max_age_hours=max_hours
        )
        == expected_result
    )


@pytest.mark.asyncio
async def test_cleanup_inference_services_older_than_threshold(mocker):
    mocker.patch("inference_services.ApiClient")
    custom_object_api_client_mock = mocker.patch("inference_services.client.CustomObjectsApi")
    custom_object_api_instance_mock = custom_object_api_client_mock.return_value

    list_object_mock = AsyncMock()
    inf_serv_1 = MagicMock()
    inf_serv_1.metadata = {"name": "inf_serv_1", "creationTimestamp": "placeholder"}
    inf_serv_2 = MagicMock()
    inf_serv_2.metadata = {"name": "inf_serv_2", "creationTimestamp": "placeholder"}
    list_object_mock.return_value = {"items": [inf_serv_1, inf_serv_2]}
    custom_object_api_instance_mock.list_namespaced_custom_object = list_object_mock

    delete_object_mock = AsyncMock()
    custom_object_api_instance_mock.delete_namespaced_custom_object = delete_object_mock

    is_inference_service_older_than_threshold_mock = mocker.patch(
        "inference_services.is_inference_service_older_than_threshold"
    )
    is_inference_service_older_than_threshold_mock.side_effect = [False, True]

    await inference_services.cleanup_inference_services_older_than_threshold(namespace="test")

    assert is_inference_service_older_than_threshold_mock.call_count == 2
    assert list_object_mock.call_count == 1
    assert delete_object_mock.call_count == 1

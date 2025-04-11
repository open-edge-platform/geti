# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock, patch

import pytest
from fastapi import status

from dependencies import get_session
from exceptions.custom_exception_handler import custom_exception_handler
from main import app
from utils.enums import AggregatesKey, CreditSystemTimeBoundaries


def patched_session():
    return MagicMock()


@pytest.fixture
def mock_transaction_service():
    with patch("rest.endpoints.transactions.get_aggregates.TransactionService") as mock_transaction_service:
        yield mock_transaction_service


@pytest.fixture
def aggregate_endpoint(organization_id, endpoint_url):
    resource_path = "transactions/aggregates"
    return endpoint_url(organization_id, resource_path)


def _prepare_params_dict(key_parameter: list, from_date: list[int] | None, to_date: list[int] | None, project_id: list):
    params = {"key": key_parameter}
    if from_date is not None:
        params["from_date"] = from_date
    if to_date is not None:
        params["to_date"] = to_date
    if project_id is not None:
        params["project_id"] = project_id
    return params


@pytest.mark.parametrize(
    "key_parameter, from_date, to_date, project_id, expected_status_code",
    [
        ([AggregatesKey.PROJECT.value], None, None, None, status.HTTP_200_OK),
        ([AggregatesKey.SERVICE_NAME.value], 1715810400000, None, None, status.HTTP_200_OK),
        ([AggregatesKey.DATE.value], None, None, [], status.HTTP_200_OK),
        (
            [AggregatesKey.PROJECT.value, AggregatesKey.DATE.value],
            1715810400000,
            None,
            ["some_project"],
            status.HTTP_200_OK,
        ),
        (
            [AggregatesKey.PROJECT.value, AggregatesKey.SERVICE_NAME.value],
            None,
            None,
            ["some_project"],
            status.HTTP_200_OK,
        ),
        ([AggregatesKey.DATE.value, AggregatesKey.SERVICE_NAME.value], 1715810400000, None, [], status.HTTP_200_OK),
        (
            [AggregatesKey.PROJECT.value, AggregatesKey.SERVICE_NAME.value, AggregatesKey.DATE.value],
            None,
            None,
            [],
            status.HTTP_200_OK,
        ),
    ],
)
def test_get_aggregates_success(
    mock_transaction_service,
    aggregate_endpoint,
    client,
    aggregate_response,
    key_parameter,
    from_date,
    to_date,
    project_id,
    expected_status_code,
):
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    params = _prepare_params_dict(
        key_parameter=key_parameter, from_date=from_date, to_date=to_date, project_id=project_id
    )

    transaction_service = MagicMock()
    transaction_service.aggregate_transactions.return_value = aggregate_response
    mock_transaction_service.return_value = transaction_service

    response = client.get(aggregate_endpoint, params=params)

    if expected_status_code == status.HTTP_200_OK:
        mock_transaction_service.assert_called_once()
        transaction_service.aggregate_transactions.assert_called_once()
    assert response.status_code == expected_status_code


def test_get_aggregates_failure(mock_transaction_service, client, aggregate_endpoint):
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    app.add_exception_handler(Exception, custom_exception_handler)

    transaction_service = MagicMock()
    transaction_service.aggregate_transactions.side_effect = ValueError
    mock_transaction_service.return_value = transaction_service

    with pytest.raises(ValueError):
        response = client.get(aggregate_endpoint, params={"key": [AggregatesKey.PROJECT.value]})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    mock_transaction_service.assert_called_once()
    transaction_service.aggregate_transactions.assert_called_once()


@pytest.mark.parametrize(
    "key_parameter, from_date, to_date, project_id",
    [
        ([], CreditSystemTimeBoundaries.START.value, CreditSystemTimeBoundaries.END.value, None),
    ],
)
def test_get_aggregates_wrong_parameters_values(
    client,
    aggregate_endpoint,
    key_parameter,
    from_date,
    to_date,
    project_id,
):
    app.dependency_overrides[get_session] = patched_session  # type: ignore
    app.add_exception_handler(Exception, custom_exception_handler)

    params = _prepare_params_dict(
        key_parameter=key_parameter, from_date=from_date, to_date=to_date, project_id=project_id
    )

    with pytest.raises(Exception):
        response = client.get(aggregate_endpoint, params=params)
        response.status_code == status.HTTP_400_BAD_REQUEST

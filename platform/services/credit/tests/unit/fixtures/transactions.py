# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from collections.abc import Sequence
from unittest.mock import MagicMock

import pytest
from sqlalchemy.engine.row import Row

from rest.schema.transactions import AggregateItem, AggregatesResponse, AggregatesResult, GroupItem, ResourcesAmount


@pytest.fixture
def group_item():
    return GroupItem(key="project", value="some_project")


@pytest.fixture
def resource_amount():
    return ResourcesAmount(images=10, frames=5)


@pytest.fixture
def aggregate_result(resource_amount):
    return AggregatesResult(credits=23, resources=resource_amount)


@pytest.fixture
def aggregate_item(group_item, aggregate_result):
    return AggregateItem(group=[group_item], result=aggregate_result)


@pytest.fixture
def aggregate_response(aggregate_item):
    return AggregatesResponse(aggregates=[aggregate_item])


def create_mock_row(data, keys):
    mock_row = MagicMock(spec=Row)
    mock_row._mapping = dict(zip(keys, data))

    for key, value in zip(keys, data):
        setattr(mock_row, key, value)
    return mock_row


@pytest.fixture
def aggregate_result_fixture():
    def _mock_query_result(optional_keys: list, row_data_list: list[Sequence]) -> list[dict]:
        mandatory_keys = ["resources", "credits"]
        all_keys = optional_keys + mandatory_keys

        mock_rows = [create_mock_row(row_data, all_keys) for row_data in row_data_list]

        return mock_rows

    return _mock_query_result

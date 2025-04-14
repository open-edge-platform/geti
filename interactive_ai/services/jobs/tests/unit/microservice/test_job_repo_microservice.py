# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import Any
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from microservice.job_repo import WorkspaceBasedMicroserviceJobRepo

from geti_types import ID
from sc_sdk.repos.base.session_repo import QueryAccessMode

project_id = ID("project")

collection = MagicMock()


@pytest.mark.parametrize("num_updated_docs, expected_updated", [(0, False), (1, True)])
def test_update(request, num_updated_docs, expected_updated) -> None:
    # Arrange
    id = ID("test_id")
    update = {"state": 2}
    collection.update_one().modified_count = num_updated_docs
    job_repo = WorkspaceBasedMicroserviceJobRepo()
    query_filter = job_repo.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
    query_filter.update({"_id": "test_id"})

    # Act
    with patch.object(
        WorkspaceBasedMicroserviceJobRepo, "_collection", new_callable=PropertyMock, return_value=collection
    ):
        updated = job_repo.update(id, update)

    # Assert
    collection.update_one.assert_called_with(
        filter=query_filter,
        update=update,
        array_filters=None,
        upsert=False,
        session=None,
    )
    assert updated == expected_updated


def test_update_many(request) -> None:
    # Arrange
    job_filter: dict[str, Any] = {"state": 1}
    update = {"state": 2}
    job_repo = WorkspaceBasedMicroserviceJobRepo()
    query_filter = job_repo.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
    query_filter.update(job_filter)

    # Act
    with patch.object(
        WorkspaceBasedMicroserviceJobRepo, "_collection", new_callable=PropertyMock, return_value=collection
    ):
        job_repo.update_many(job_filter, update)

    # Assert
    collection.update_many.assert_called_once_with(filter=query_filter, update=update, upsert=False, session=None)

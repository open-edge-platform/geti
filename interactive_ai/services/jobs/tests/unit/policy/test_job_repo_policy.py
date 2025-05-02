# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import Any
from unittest.mock import MagicMock, PropertyMock, patch

from policies.job_repo import SessionBasedPolicyJobRepo

from geti_types import ID
from iai_core_py.repos.base.session_repo import QueryAccessMode

project_id = ID("project")

collection = MagicMock()


def test_update_many(request) -> None:
    # Arrange
    job_filter: dict[str, Any] = {"state": 1}
    update = {"state": 2}
    job_repo = SessionBasedPolicyJobRepo()
    query_filter = job_repo.preliminary_query_match_filter(access_mode=QueryAccessMode.WRITE)
    query_filter.update(job_filter)

    # Act
    with patch.object(SessionBasedPolicyJobRepo, "_collection", new_callable=PropertyMock, return_value=collection):
        job_repo.update_many(job_filter, update)

    # Assert
    collection.update_many.assert_called_once_with(filter=query_filter, update=update, upsert=False, session=None)

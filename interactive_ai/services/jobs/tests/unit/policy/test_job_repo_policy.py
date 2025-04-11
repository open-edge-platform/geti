# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

from typing import Any
from unittest.mock import MagicMock, PropertyMock, patch

from policies.job_repo import SessionBasedPolicyJobRepo

from geti_types import ID
from sc_sdk.repos.base.session_repo import QueryAccessMode

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

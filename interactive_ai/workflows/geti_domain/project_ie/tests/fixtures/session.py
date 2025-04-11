#  INTEL CONFIDENTIAL
#
#  Copyright (C) 2024 Intel Corporation
#
#  This software and the related documents are Intel copyrighted materials, and
#  your use of them is governed by the express license under which they were provided to
#  you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
#  publish, distribute, disclose or transmit this software or the related documents
#  without Intel's prior written permission.
#
#  This software and the related documents are provided as is,
#  with no express or implied warranties, other than those that are expressly stated
#  in the License.
import pytest
from geti_types import ID, make_session, session_context


@pytest.fixture
def fxt_organization_id():
    yield ID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def fxt_workspace_id():
    return ID("00000000-0000-0000-0000-000000000002")


@pytest.fixture(autouse=True)
def fxt_session_ctx(fxt_organization_id, fxt_workspace_id):
    session = make_session(
        organization_id=fxt_organization_id,
        workspace_id=fxt_workspace_id,
    )
    with session_context(session=session):
        yield session

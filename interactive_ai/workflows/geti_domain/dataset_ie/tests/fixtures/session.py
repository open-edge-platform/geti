# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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

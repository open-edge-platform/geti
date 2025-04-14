# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

import pytest

from geti_types import ID, make_session, session_context

logger = logging.getLogger(__name__)


@pytest.fixture
def fxt_organization_id():
    yield ID("000000000000000000000001")


@pytest.fixture
def fxt_workspace_id():
    return ID("652651cd3ffd5b3dc7f1d391")


@pytest.fixture(autouse=True)
def fxt_session_ctx(fxt_organization_id, fxt_workspace_id):
    logger.info("Initializing session (fixture 'fxt_session_ctx')")
    session = make_session(
        organization_id=fxt_organization_id,
        workspace_id=fxt_workspace_id,
    )
    with session_context(session=session):
        yield session

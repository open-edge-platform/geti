# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from geti_types import make_session, session_context


@pytest.fixture(scope="session", autouse=True)
def fxt_session():
    """Initialize the session context variable with a default Session object"""
    session = make_session()
    with session_context(session=session):
        yield session

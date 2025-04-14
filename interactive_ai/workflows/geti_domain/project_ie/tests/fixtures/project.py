# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements project fixtures
"""

import pytest
from geti_types import ID, ProjectIdentifier


@pytest.fixture
def fxt_workspace_id():
    return ID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def fxt_project_identifier_1(fxt_workspace_id, fxt_ote_id):
    yield ProjectIdentifier(
        workspace_id=fxt_workspace_id,
        project_id=fxt_ote_id(1),
    )


@pytest.fixture
def fxt_project_identifier_2(fxt_workspace_id, fxt_ote_id):
    yield ProjectIdentifier(
        workspace_id=fxt_workspace_id,
        project_id=fxt_ote_id(2),
    )


@pytest.fixture
def fxt_project_identifier(fxt_project_identifier_1):
    yield fxt_project_identifier_1

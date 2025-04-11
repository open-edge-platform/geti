# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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

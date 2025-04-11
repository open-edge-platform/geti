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

from unittest.mock import MagicMock

import pytest
from sc_sdk.entities.task_node import TaskNode

from tests.test_helpers import ID


@pytest.fixture(scope="function")
def fxt_detection_node(fxt_mongo_id):
    return TaskNode(
        title="Object detection (MOCK)",
        project_id=ID(),
        task_properties=MagicMock(),
        id_=fxt_mongo_id(100),
    )

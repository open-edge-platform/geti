# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import MagicMock

import pytest
from iai_core.entities.task_node import TaskNode

from tests.test_helpers import ID


@pytest.fixture(scope="function")
def fxt_detection_node(fxt_mongo_id):
    return TaskNode(
        title="Object detection (MOCK)",
        project_id=ID(),
        task_properties=MagicMock(),
        id_=fxt_mongo_id(100),
    )

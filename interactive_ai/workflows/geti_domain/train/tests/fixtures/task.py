# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import MagicMock, patch

import pytest
from geti_types import ID
from sc_sdk.algorithms import ModelTemplateList
from sc_sdk.entities.label_schema import LabelSchemaView
from sc_sdk.entities.model_template import TaskFamily, TaskType
from sc_sdk.entities.task_node import TaskNode, TaskProperties

from tests.fixtures.values import IDOffsets

PROJECT_ID = "project_id"
TASK_ID = "task_id"


@pytest.fixture
def fxt_trainable_task(fxt_detection_task):
    yield fxt_detection_task


@pytest.fixture
def fxt_detection_task(fxt_ote_id, fxt_empty_project):
    yield TaskNode(
        title="dummy detection task",
        task_properties=TaskProperties.from_model_template(ModelTemplateList().get_by_id("detection")),
        project_id=fxt_ote_id(IDOffsets.TASK_CHAIN_PROJECT),
        id_=fxt_ote_id(IDOffsets.DETECTION_TASK),
    )


@pytest.fixture(scope="function")
def fxt_detection_node(fxt_mongo_id):
    return TaskNode(
        title="Object detection (MOCK)",
        project_id=ID(),
        task_properties=MagicMock(),
        id_=fxt_mongo_id(100),
    )


@pytest.fixture
def fxt_task_node():
    return TaskNode(
        title="Test node",
        project_id=ID(PROJECT_ID),
        id_=ID(TASK_ID),
        task_properties=TaskProperties(
            task_type=TaskType.ANOMALY_DETECTION,
            task_family=TaskFamily.VISION,
            is_trainable=True,
            is_global=False,
            is_anomaly=True,
        ),
    )


@pytest.fixture
def fxt_label_schema(fxt_label):
    yield LabelSchemaView.from_labels([fxt_label])


@pytest.fixture(autouse=True)
def fxt_requests_post():
    """Patch istio-proxy termination callback not to raise an error in local environment."""
    with patch("jobs_common.tasks.primary_container_task.requests.post") as mock_requests_post:
        mock_requests_post.return_value.status_code = 200
        yield mock_requests_post

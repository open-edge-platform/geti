# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import os
from copy import deepcopy
from unittest.mock import patch
from uuid import UUID

import pytest
from bson import UUID_SUBTYPE, Binary, ObjectId, UuidRepresentation
from pymongo import MongoClient

from migration.scripts.reduce_anomaly_tasks import ReduceAnomalyTasksMigration

ORGANIZATION_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
WORKSPACE_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
PROJECT_ID = ObjectId("66a0faf070cdf6d0b2ec5f93")


@pytest.fixture
def fxt_project() -> dict:
    yield {
        "organization_id": ORGANIZATION_ID,
        "workspace_id": WORKSPACE_ID,
        "_id": PROJECT_ID,
        "performance": {
            "score": 0.4,
            "task_performances": [
                {
                    "score": {"value": 0.4, "metric_type": "f-measure"},
                    "global_score": {"value": 0.4, "metric_type": "f-measure"},
                    "local_score": {"value": 0.1, "metric_type": "f-measure"},
                }
            ],
        },
        "project_type": "UNDEFINED",
        "task_graph": {"pipeline_representation": "UNDEFINED"},
    }


@pytest.fixture
def fxt_anomaly_classification_project(fxt_project) -> dict:
    anomaly_classification_project = deepcopy(fxt_project)
    anomaly_classification_project["project_type"] = "ANOMALY_CLASSIFICATION"
    anomaly_classification_project["task_graph"]["pipeline_representation"] = "Dataset → Anomaly classification"
    yield anomaly_classification_project


@pytest.fixture
def fxt_anomaly_detection_project(fxt_project) -> dict:
    anomaly_detection_project = deepcopy(fxt_project)
    anomaly_detection_project["project_type"] = "ANOMALY_DETECTION"
    anomaly_detection_project["task_graph"]["pipeline_representation"] = "Dataset → Anomaly detection"
    yield anomaly_detection_project


@pytest.fixture
def fxt_anomaly_segmentation_project(fxt_project) -> dict:
    anomaly_segmentation_project = deepcopy(fxt_project)
    anomaly_segmentation_project["project_type"] = "ANOMALY_SEGMENTATION"
    anomaly_segmentation_project["task_graph"]["pipeline_representation"] = "Dataset → Anomaly segmentation"
    yield anomaly_segmentation_project


@pytest.fixture
def fxt_label() -> dict:
    yield {
        "domain": "UNDEFINED",
        "is_anomalous": True,
        "organization_id": ORGANIZATION_ID,
        "workspace_id": WORKSPACE_ID,
        "project_id": PROJECT_ID,
    }


@pytest.fixture
def fxt_anomaly_classification_label(fxt_label) -> dict:
    anomaly_classification_label = deepcopy(fxt_label)
    anomaly_classification_label["domain"] = "ANOMALY_CLASSIFICATION"
    yield anomaly_classification_label


@pytest.fixture
def fxt_anomaly_detection_label(fxt_label) -> dict:
    anomaly_detection_label = deepcopy(fxt_label)
    anomaly_detection_label["domain"] = "ANOMALY_DETECTION"
    yield anomaly_detection_label


@pytest.fixture
def fxt_anomaly_segmentation_label(fxt_label) -> dict:
    anomaly_segmentation_label = deepcopy(fxt_label)
    anomaly_segmentation_label["domain"] = "ANOMALY_SEGMENTATION"
    yield anomaly_segmentation_label


@pytest.fixture
def fxt_task_node() -> dict:
    yield {
        "workspace_id": WORKSPACE_ID,
        "organization_id": ORGANIZATION_ID,
        "project_id": PROJECT_ID,
        "task_type": "UNDEFINED",
        "task_title": "UNDEFINED",
    }


@pytest.fixture
def fxt_anomaly_classification_task_node(fxt_task_node) -> dict:
    anomaly_classification_task_node = deepcopy(fxt_task_node)
    anomaly_classification_task_node["task_type"] = "ANOMALY_CLASSIFICATION"
    anomaly_classification_task_node["task_title"] = "Anomaly classification"
    yield anomaly_classification_task_node


@pytest.fixture
def fxt_anomaly_detection_task_node(fxt_task_node) -> dict:
    anomaly_detection_task_node = deepcopy(fxt_task_node)
    anomaly_detection_task_node["task_type"] = "ANOMALY_DETECTION"
    anomaly_detection_task_node["task_title"] = "Anomaly detection"
    yield anomaly_detection_task_node


@pytest.fixture
def fxt_anomaly_segmentation_task_node(fxt_task_node) -> dict:
    anomaly_segmentation_task_node = deepcopy(fxt_task_node)
    anomaly_segmentation_task_node["task_type"] = "ANOMALY_SEGMENTATION"
    anomaly_segmentation_task_node["task_title"] = "Anomaly segmentation"
    yield anomaly_segmentation_task_node


@pytest.fixture
def fxt_mongo_client() -> MongoClient:
    database_address = os.environ.get("DATABASE_ADDRESS", "mongodb://localhost:27017/")
    database_username = os.environ.get("DATABASE_USERNAME", None)
    database_password = os.environ.get("DATABASE_PASSWORD", None)

    return MongoClient(database_address, username=database_username, password=database_password)


def side_effect_mongo_mock_from_uuid(uuid: UUID, uuid_representation=UuidRepresentation.STANDARD):
    """Override (Mock) the bson.binary.Binary.from_uuid function to work for mongomock
    Code is copy pasted from the original function,
    but `uuid_representation` is ignored and only code parts as if
    uuid_representation == UuidRepresentation.STANDARD are used
    """
    if not isinstance(uuid, UUID):
        raise TypeError("uuid must be an instance of uuid.UUID")

    subtype = UUID_SUBTYPE
    payload = uuid.bytes

    return Binary(payload, subtype)


@pytest.fixture
def fxt_mongo_uuid(monkeypatch):
    with patch.object(Binary, "from_uuid", side_effect=side_effect_mongo_mock_from_uuid):
        yield


class TestAnomalyReductionProcessMigration:
    @pytest.mark.parametrize(
        "lazyfxt_project, lazyfxt_label, lazyfxt_task_node",
        [
            (
                "fxt_anomaly_classification_project",
                "fxt_anomaly_classification_label",
                "fxt_anomaly_classification_task_node",
            ),
            ("fxt_anomaly_detection_project", "fxt_anomaly_detection_label", "fxt_anomaly_detection_task_node"),
            (
                "fxt_anomaly_segmentation_project",
                "fxt_anomaly_segmentation_label",
                "fxt_anomaly_segmentation_task_node",
            ),
        ],
        ids=[
            "Anomaly classification",
            "Anomaly detection",
            "Anomaly segmentation",
        ],
    )
    def test_upgrade_project(
        self, fxt_mongo_client, fxt_mongo_uuid, lazyfxt_project, lazyfxt_label, lazyfxt_task_node, request
    ):
        # Arrange
        project = request.getfixturevalue(lazyfxt_project)
        label = request.getfixturevalue(lazyfxt_label)
        task_node = request.getfixturevalue(lazyfxt_task_node)

        mock_db = fxt_mongo_client.get_database("geti_test")
        request.addfinalizer(lambda: fxt_mongo_client.drop_database("geti_test"))
        project_collection = mock_db.project
        label_collection = mock_db.label
        task_node_collection = mock_db.task_node
        project_collection.insert_one(project)
        label_collection.insert_one(label)
        task_node_collection.insert_one(task_node)

        # act
        with patch.object(MongoClient, "get_database", return_value=mock_db):
            ReduceAnomalyTasksMigration.upgrade_project(
                organization_id=str(ORGANIZATION_ID),
                workspace_id=str(WORKSPACE_ID),
                project_id=str(PROJECT_ID),
            )

        # Check that the fields are correctly reduced
        project_after_upgrade = list(project_collection.find(filter={"_id": PROJECT_ID}))
        assert project_after_upgrade[0]["project_type"] == "ANOMALY"
        assert project_after_upgrade[0]["task_graph"]["pipeline_representation"] == "Dataset → Anomaly"
        assert project_after_upgrade[0]["performance"]["task_performances"][0]["score"]["metric_type"] == "accuracy"
        assert not project_after_upgrade[0]["performance"]["task_performances"][0].get("global_score")
        assert not project_after_upgrade[0]["performance"]["task_performances"][0].get("local_score")

        labels_after_upgrade = list(label_collection.find(filter={"project_id": PROJECT_ID}))
        assert labels_after_upgrade[0]["domain"] == "ANOMALY"

        task_node_after_upgrade = list(task_node_collection.find(filter={"project_id": PROJECT_ID}))
        assert task_node_after_upgrade[0]["task_type"] == "ANOMALY"
        assert task_node_after_upgrade[0]["task_title"] == "Anomaly"

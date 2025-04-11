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
from unittest.mock import patch
from uuid import UUID

import pytest
from bson import UUID_SUBTYPE, Binary, ObjectId, UuidRepresentation
from pymongo import MongoClient

from migration.scripts.add_project_type import AddProjectTypeMigration
from migration.utils import MongoDBConnection

ORGANIZATION_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
WORKSPACE_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
PROJECT_ID = ObjectId("662c1c6b3a3df3291394b158")
TRAINABLE_TASK_NODE_1 = ObjectId("662c1c6b3a3df3291394b159")
TRAINABLE_TASK_NODE_2 = ObjectId("662c1c6b3a3df3291394b160")
OTHER_TASK_NODE_1 = ObjectId("662c1c6b3a3df3291394b161")


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


@pytest.fixture
def fxt_mongo_client() -> MongoClient:
    return MongoDBConnection().client


@pytest.fixture
def fxt_project():
    yield {
        "workspace_id": WORKSPACE_ID,
        "organization_id": ORGANIZATION_ID,
        "_id": PROJECT_ID,
        "task_graph": {"nodes": [TRAINABLE_TASK_NODE_1, OTHER_TASK_NODE_1, TRAINABLE_TASK_NODE_2]},
    }


def get_task_node(id_: ObjectId, is_trainable: bool, task_type: str) -> dict:
    return {
        "_id": id_,
        "workspace_id": WORKSPACE_ID,
        "organization_id": ORGANIZATION_ID,
        "project_id": PROJECT_ID,
        "is_trainable": is_trainable,
        "task_type": task_type,
    }


class TestAddProjectTypeMigration:
    def test_upgrade_project(
        self,
        request,
        fxt_project,
        fxt_mongo_uuid,
        fxt_mongo_client,
    ) -> None:
        # Arrange
        mock_db = fxt_mongo_client.get_database("geti_test")
        request.addfinalizer(lambda: fxt_mongo_client.drop_database("geti_test"))
        project_collection = mock_db.project
        task_node_collection = mock_db.task_node
        project_collection.insert_one(fxt_project)
        task_node_collection.insert_one(
            get_task_node(id_=TRAINABLE_TASK_NODE_1, is_trainable=True, task_type="train_1")
        )
        task_node_collection.insert_one(get_task_node(id_=OTHER_TASK_NODE_1, is_trainable=False, task_type="no_type"))
        task_node_collection.insert_one(
            get_task_node(id_=TRAINABLE_TASK_NODE_2, is_trainable=True, task_type="train_2")
        )

        # Act
        with patch.object(MongoClient, "get_database", return_value=mock_db):
            AddProjectTypeMigration.upgrade_project(
                organization_id=str(ORGANIZATION_ID),
                workspace_id=str(WORKSPACE_ID),
                project_id=str(PROJECT_ID),
            )

        # Assert
        assert project_collection.find_one()["project_type"] == "train_1 → train_2"

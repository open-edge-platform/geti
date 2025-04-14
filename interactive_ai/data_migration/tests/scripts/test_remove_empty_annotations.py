# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch
from uuid import UUID, uuid4

import mongomock
import pytest
from bson import UUID_SUBTYPE, ObjectId, UuidRepresentation
from bson.binary import Binary
from pymongo import MongoClient

from migration.scripts.remove_empty_annotations import RemoveEmptyAnnotationMigration


@pytest.fixture
def fxt_organization_id():
    yield uuid4()


@pytest.fixture
def fxt_workspace_id():
    yield uuid4()


@pytest.fixture
def fxt_project_id():
    yield ObjectId()


@pytest.fixture(autouse=True)
def fxt_mongo_uuid(monkeypatch):
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

    with patch.object(Binary, "from_uuid", side_effect=side_effect_mongo_mock_from_uuid):
        yield


class TestRemoveEmptyAnnotationMigration:
    def test_upgrade_project_removes_empty_annotations(self, fxt_organization_id, fxt_workspace_id, fxt_project_id):
        mock_db = mongomock.MongoClient(uuidRepresentation="standard").db
        annotation_collection = mock_db.create_collection("annotation_scene")
        annotation_collection.insert_many(
            [
                {
                    "_id": ObjectId("012345678901234567891234"),
                    "annotations": [{"labels": []}, {"labels": ["label1"]}],
                    "organization_id": fxt_organization_id,
                    "workspace_id": fxt_workspace_id,
                    "project_id": fxt_project_id,
                },
                {
                    "_id": ObjectId("012345678901234567891235"),
                    "annotations": [{"labels": ["label2"]}],
                    "organization_id": fxt_organization_id,
                    "workspace_id": fxt_workspace_id,
                    "project_id": fxt_project_id,
                },
            ]
        )
        with patch.object(MongoClient, "get_database", return_value=mock_db):
            RemoveEmptyAnnotationMigration.upgrade_project(
                str(fxt_organization_id), str(fxt_workspace_id), str(fxt_project_id)
            )

        updated_scenes = list(annotation_collection.find())
        assert len(updated_scenes) == 2
        assert updated_scenes[0]["annotations"] == [{"labels": ["label1"]}]
        assert updated_scenes[1]["annotations"] == [{"labels": ["label2"]}]

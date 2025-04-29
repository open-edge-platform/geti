# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from copy import deepcopy
from unittest.mock import patch
from uuid import UUID, uuid4

import mongomock
import pytest
from bson import ObjectId
from bson.binary import UUID_SUBTYPE, Binary, UuidRepresentation
from pymongo import MongoClient

from migration.scripts.set_training_framework_in_models import SetTrainingFrameworkInModelsMigration


@pytest.fixture
def fxt_organization_id():
    yield uuid4()


@pytest.fixture
def fxt_workspace_id():
    yield uuid4()


@pytest.fixture
def fxt_project_ids():
    yield ObjectId(), ObjectId()  # 2 projects


@pytest.fixture
def fxt_models_before_upgrade(fxt_organization_id, fxt_workspace_id, fxt_project_ids):
    """List of documents present in the database BEFORE upgrading project #0"""
    yield [
        # document in project #0 without 'training_framework' -> expected that it is updated
        {
            "_id": ObjectId(),
            "organization_id": fxt_organization_id,
            "workspace_id": fxt_workspace_id,
            "project_id": fxt_project_ids[0],
            "model_status": "SUCCESS",
        },
        # document in project #0 with 'training_framework' -> expected that it is NOT updated
        {
            "_id": ObjectId(),
            "organization_id": fxt_organization_id,
            "workspace_id": fxt_workspace_id,
            "project_id": fxt_project_ids[0],
            "model_status": "SUCCESS",
            "training_framework": {"type": "THIRD_PARTY", "version": "5.6.7"},
        },
        # document from another project -> expected that it is NOT updated
        {
            "_id": ObjectId(),
            "organization_id": fxt_organization_id,
            "workspace_id": fxt_workspace_id,
            "project_id": fxt_project_ids[1],
            "model_status": "SUCCESS",
        },
    ]


@pytest.fixture
def fxt_models_after_upgrade(fxt_models_before_upgrade):
    """List of documents present in the database AFTER upgrading project #0"""
    docs_after_upgrade = deepcopy(fxt_models_before_upgrade)
    docs_after_upgrade[0].update({"training_framework": {"type": "OTX", "version": "1.6.2"}})
    yield docs_after_upgrade


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


class TestTrainingFrameworkMigration:
    def test_set_training_frameworks_in_models(
        self,
        fxt_organization_id,
        fxt_workspace_id,
        fxt_project_ids,
        fxt_models_before_upgrade,
        fxt_models_after_upgrade,
    ) -> None:
        mock_db = mongomock.MongoClient(uuidRepresentation="standard").db
        model_collection = mock_db.create_collection("model")
        model_collection.insert_many(fxt_models_before_upgrade)
        project_to_upgrade_id = fxt_project_ids[0]

        with patch.object(MongoClient, "get_database", return_value=mock_db):
            SetTrainingFrameworkInModelsMigration.upgrade_project(
                organization_id=str(fxt_organization_id),
                workspace_id=str(fxt_workspace_id),
                project_id=str(project_to_upgrade_id),
            )

        actual_models_after_upgrade = list(model_collection.find())
        actual_models_after_upgrade.sort(key=lambda doc: doc["_id"])
        fxt_models_after_upgrade.sort(key=lambda doc: doc["_id"])
        assert actual_models_after_upgrade == fxt_models_after_upgrade

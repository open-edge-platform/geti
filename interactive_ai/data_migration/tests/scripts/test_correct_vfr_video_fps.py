# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os
from unittest.mock import patch
from uuid import UUID, uuid4

import mongomock
import pytest
from bson import ObjectId
from bson.binary import UUID_SUBTYPE, Binary, UuidRepresentation
from pymongo import MongoClient

from migration.scripts.correct_vfr_video_fps import CorrectVFRVideoFPS
from migration.utils.connection import MinioStorageClient


@pytest.fixture
def fxt_organization_id():
    yield uuid4()


@pytest.fixture
def fxt_workspace_id():
    yield uuid4()


@pytest.fixture
def fxt_project_id():
    yield ObjectId()


@pytest.fixture
def fxt_dataset_storage_id():
    yield ObjectId()


@pytest.fixture
def fxt_video_id():
    yield ObjectId()


@pytest.fixture
def fxt_videos_before_upgrade(
    fxt_video_id, fxt_dataset_storage_id, fxt_organization_id, fxt_workspace_id, fxt_project_id
):
    """
    List of documents present in the database before upgrade
    """
    yield [
        {
            "_id": fxt_video_id,
            "organization_id": fxt_organization_id,
            "workspace_id": fxt_workspace_id,
            "project_id": fxt_project_id,
            "dataset_storage_id": fxt_dataset_storage_id,
            "extension": "mp4",
            "fps": 20,
        }
    ]


@pytest.fixture
def fxt_videos_after_upgrade(
    fxt_video_id, fxt_dataset_storage_id, fxt_organization_id, fxt_workspace_id, fxt_project_id
):
    """
    List of documents present in the database after upgrade
    """
    yield [
        {
            "_id": fxt_video_id,
            "organization_id": fxt_organization_id,
            "workspace_id": fxt_workspace_id,
            "project_id": fxt_project_id,
            "dataset_storage_id": fxt_dataset_storage_id,
            "extension": "mp4",
            "fps": 30,
        }
    ]


@pytest.fixture
def fxt_ds_storage_collection(fxt_dataset_storage_id, fxt_project_id):
    """
    List of documents present in the database after upgrade
    """
    yield [
        {
            "_id": fxt_dataset_storage_id,
            "project_id": fxt_project_id,
        }
    ]


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


class TestCorrectVideoFPS:
    def test_adjust_hyper_params_upgrade(
        self,
        fxt_organization_id,
        fxt_workspace_id,
        fxt_project_id,
        fxt_videos_before_upgrade,
        fxt_videos_after_upgrade,
        fxt_ds_storage_collection,
    ) -> None:
        mock_db = mongomock.MongoClient(uuidRepresentation="standard").db
        os.environ["S3_CREDENTIALS_PROVIDER"] = "aws"

        video_collection = mock_db.create_collection("video")
        video_collection.insert_many(fxt_videos_before_upgrade)

        ds_storage_collection = mock_db.create_collection("dataset_storage")
        ds_storage_collection.insert_many(fxt_ds_storage_collection)

        with (
            patch.object(MongoClient, "get_database", return_value=mock_db),
            patch.object(CorrectVFRVideoFPS, "get_video_fps", return_value=30),
            patch.object(MinioStorageClient, "authenticate_saas_client"),
        ):
            CorrectVFRVideoFPS.upgrade_project(
                organization_id=str(fxt_organization_id),
                workspace_id=str(fxt_workspace_id),
                project_id=str(fxt_project_id),
            )

        video_after_upgrade = list(video_collection.find())

        assert video_after_upgrade == fxt_videos_after_upgrade

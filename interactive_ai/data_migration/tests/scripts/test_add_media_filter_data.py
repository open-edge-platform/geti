# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch
from uuid import UUID

import pytest
from bson import UUID_SUBTYPE, Binary, ObjectId, UuidRepresentation
from pymongo import MongoClient

from migration.scripts.add_media_filter_data import AddDataForFilteringMigration
from migration.utils import MongoDBConnection

ORGANIZATION_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
WORKSPACE_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
PROJECT_ID = ObjectId("662c1c6b3a3df3291394b158")
IMAGE_ID = ObjectId("662c1c6b3a3df3291394b159")
VIDEO_ID = ObjectId("662c1c6b3a3df3291394b160")
FILTER_DATA_ID_1 = ObjectId("662c1c6b3a3df3291394b161")
FILTER_DATA_ID_2 = ObjectId("662c1c6b3a3df3291394b162")
FILTER_DATA_ID_3 = ObjectId("662c1c6b3a3df3291394b163")


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
def fxt_image() -> dict:
    return {
        "workspace_id": WORKSPACE_ID,
        "organization_id": ORGANIZATION_ID,
        "project_id": PROJECT_ID,
        "_id": IMAGE_ID,
        "size": 5,
        "uploader_id": "image_uploader",
    }


@pytest.fixture
def fxt_video() -> dict:
    return {
        "workspace_id": WORKSPACE_ID,
        "organization_id": ORGANIZATION_ID,
        "project_id": PROJECT_ID,
        "_id": VIDEO_ID,
        "size": 7,
        "uploader_id": "video_uploader",
        "total_frames": 100,
        "fps": 10,
        "stride": 5,
    }


@pytest.fixture
def fxt_list_of_filter_data() -> list[dict]:
    return [
        {
            "_id": FILTER_DATA_ID_1,
            "workspace_id": WORKSPACE_ID,
            "organization_id": ORGANIZATION_ID,
            "project_id": PROJECT_ID,
            "media_identifier": {
                "media_id": IMAGE_ID,
                "type": "image",
            },
        },
        {
            "_id": FILTER_DATA_ID_2,
            "workspace_id": WORKSPACE_ID,
            "organization_id": ORGANIZATION_ID,
            "project_id": PROJECT_ID,
            "media_identifier": {
                "media_id": VIDEO_ID,
                "type": "video",
            },
        },
        {
            "_id": FILTER_DATA_ID_3,
            "workspace_id": WORKSPACE_ID,
            "organization_id": ORGANIZATION_ID,
            "project_id": PROJECT_ID,
            "media_identifier": {
                "media_id": VIDEO_ID,
                "type": "video_frame",
                "frame_index": 4,
            },
        },
    ]


@pytest.fixture
def fxt_list_of_filter_data_expected() -> list[dict]:
    return [
        {
            "_id": FILTER_DATA_ID_1,
            "project_id": PROJECT_ID,
            "media_identifier": {
                "media_id": IMAGE_ID,
                "type": "image",
            },
            "size": 5,
            "uploader_id": "image_uploader",
        },
        {
            "_id": FILTER_DATA_ID_2,
            "project_id": PROJECT_ID,
            "media_identifier": {
                "media_id": VIDEO_ID,
                "type": "video",
            },
            "size": 7,
            "uploader_id": "video_uploader",
            "frame_count": 100,
            "frame_rate": 10,
            "frame_stride": 5,
            "duration": 10,
        },
        {
            "_id": FILTER_DATA_ID_3,
            "project_id": PROJECT_ID,
            "media_identifier": {
                "media_id": VIDEO_ID,
                "type": "video_frame",
                "frame_index": 4,
            },
            "size": 7,
            "uploader_id": "video_uploader",
            "frame_count": 100,
            "frame_rate": 10,
            "frame_stride": 5,
            "duration": 10,
        },
    ]


class TestAddProjectTypeMigration:
    def test_upgrade_project(
        self,
        request,
        fxt_image,
        fxt_video,
        fxt_list_of_filter_data,
        fxt_list_of_filter_data_expected,
        fxt_mongo_client,
        fxt_mongo_uuid,
    ) -> None:
        # Arrange
        mock_db = fxt_mongo_client.get_database("geti_test")
        request.addfinalizer(lambda: fxt_mongo_client.drop_database("geti_test"))
        filter_collection = mock_db.dataset_storage_filter_data
        image_collection = mock_db.image
        video_collection = mock_db.video
        for doc in fxt_list_of_filter_data:
            filter_collection.insert_one(doc)
        image_collection.insert_one(fxt_image)
        video_collection.insert_one(fxt_video)

        # Act
        with patch.object(MongoClient, "get_database", return_value=mock_db):
            AddDataForFilteringMigration.upgrade_project(
                organization_id=str(ORGANIZATION_ID),
                workspace_id=str(WORKSPACE_ID),
                project_id=str(PROJECT_ID),
            )

        # Assert
        new_docs = list(filter_collection.find())
        assert len(new_docs) == 3
        for doc in new_docs:
            # UUID handling does not work properly during tests
            del doc["organization_id"]
            del doc["workspace_id"]
            assert doc in fxt_list_of_filter_data_expected

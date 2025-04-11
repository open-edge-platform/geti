#  INTEL CONFIDENTIAL
#
#  Copyright (C) 2024 Intel Corporation
#
#  This software and the related documents are Intel copyrighted materials, and your use of them is
#  governed by the express license under which they were provided to you ("License"). Unless the
#  License provides otherwise, you may not use, modify, copy, publish, distribute, disclose or transmit
#  this software or the related documents without Intel's prior written permission.
#
#  This software and the related documents are provided as is, with no express or implied warranties,
#  other than those that are expressly stated in the License.
import datetime
from unittest.mock import patch
from uuid import UUID

import mongomock
import pytest
from bson import ObjectId
from bson.binary import UUID_SUBTYPE, Binary, UuidRepresentation
from pymongo import MongoClient

from migration.scripts.remove_empty_annotation_scene import RemoveEmptyAnnotationSceneMigrationScript


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


@pytest.fixture()
def fxt_mongo_uuid(monkeypatch):
    with patch.object(Binary, "from_uuid", side_effect=side_effect_mongo_mock_from_uuid):
        yield


@pytest.fixture
def fxt_mongo_id():
    """
    Create a realistic MongoDB ID string for testing purposes.

    If you need multiple ones, call this fixture repeatedly with different arguments.
    """
    base_id: int = 0x60D31793D5F1FB7E6E3C1A4F

    def _build_id(offset: int = 0) -> str:
        return str(hex(base_id + offset))[2:]

    yield _build_id


def get_annotation_scene(id_: str, media_identifier: dict, annotations: list | None = None) -> dict:
    if annotations is None:
        annotations = []
    return {
        "_id": ObjectId(id_),
        "dataset_storage_id": ObjectId("665ebe4de7ad59929fa37f92"),
        "annotations": annotations,
        "creation_date": datetime.datetime.now(),
        "editor_name": "sc",
        "invalid_task_ids": [],
        "kind": "ANNOTATION",
        "label_ids": [],
        "media_height": 2,
        "media_identifier": media_identifier,
        "media_width": 2,
        "model_ids": [],
        "organization_id": UUID("11fdb5ad-8e0d-4301-b22b-06589beef658"),
        "project_id": ObjectId("60d31793d5f1fb7e6e3c1a50"),
        "workspace_id": UUID("11fdb5ad-8e0d-4301-b22b-06589beef658"),
        "task_id": ObjectId("60d31793d5f1fb7e6e3c1a4f"),
    }


def get_annotation_scene_state(
    id_: str, annotation_scene_id: str, media_identifier: dict, annotation_state: str = "NONE"
) -> dict:
    return {
        "_id": ObjectId(id_),
        "annotation_scene_id": ObjectId(annotation_scene_id),
        "dataset_storage_id": ObjectId("665ebe4de7ad59929fa37f92"),
        "labels_to_revisit_full_scene": [],
        "labels_to_revisit_per_annotation": [],
        "media_annotation_state": annotation_state,
        "media_identifier": media_identifier,
        "organization_id": UUID("11fdb5ad-8e0d-4301-b22b-06589beef658"),
        "project_id": ObjectId("60d31793d5f1fb7e6e3c1a50"),
        "state_per_task": [{"task_id": ObjectId("60d31793d5f1fb7e6e3c1a4f"), "annotation_state": annotation_state}],
        "unannotated_rois": [],
        "workspace_id": UUID("11fdb5ad-8e0d-4301-b22b-06589beef658"),
    }


class TestRemoveEmptyAnnotationScene:
    def test_remove_empty_annotation_scene_from_db(self, fxt_mongo_id, fxt_mongo_uuid) -> None:
        # Arrange
        mock_db = mongomock.MongoClient().db
        annotation_scene_collection = mock_db.get_collection("annotation_scene")
        annotation_scene_state_collection = mock_db.get_collection("annotation_scene_state")

        image_id_1 = fxt_mongo_id(1)
        media_identifier_1 = {"media_id": image_id_1, "type": "image"}
        image_id_2 = fxt_mongo_id(2)
        media_identifier_2 = {"media_id": image_id_2, "type": "image"}

        annotation_scene_1a = get_annotation_scene(id_=fxt_mongo_id(10), media_identifier=media_identifier_1)
        annotation_scene_collection.insert_one(annotation_scene_1a)
        annotation_scene_1b = get_annotation_scene(
            id_=fxt_mongo_id(11), media_identifier=media_identifier_1, annotations=["something"]
        )
        annotation_scene_collection.insert_one(annotation_scene_1b)
        annotation_scene_2 = get_annotation_scene(id_=fxt_mongo_id(12), media_identifier=media_identifier_2)
        annotation_scene_collection.insert_one(annotation_scene_2)

        annotation_scene_state_1a = get_annotation_scene_state(
            id_=fxt_mongo_id(20), annotation_scene_id=annotation_scene_1a["_id"], media_identifier=media_identifier_1
        )
        annotation_scene_state_collection.insert_one(annotation_scene_state_1a)
        annotation_scene_state_1b = get_annotation_scene_state(
            id_=fxt_mongo_id(21),
            annotation_scene_id=annotation_scene_1b["_id"],
            media_identifier=media_identifier_1,
            annotation_state="ANNOTATED",
        )
        annotation_scene_state_collection.insert_one(annotation_scene_state_1b)
        annotation_scene_state_2 = get_annotation_scene_state(
            id_=fxt_mongo_id(22), annotation_scene_id=annotation_scene_2["_id"], media_identifier=media_identifier_2
        )
        annotation_scene_state_collection.insert_one(annotation_scene_state_2)

        with patch.object(MongoClient, "get_database", return_value=mock_db):
            RemoveEmptyAnnotationSceneMigrationScript.upgrade_project(
                organization_id="11fdb5ad-8e0d-4301-b22b-06589beef658",
                workspace_id="11fdb5ad-8e0d-4301-b22b-06589beef658",
                project_id="60d31793d5f1fb7e6e3c1a50",
            )

        annotation_scene_docs = list(annotation_scene_collection.find())
        annotation_scene_state_docs = list(annotation_scene_state_collection.find())

        assert len(annotation_scene_docs) == 1
        assert len(annotation_scene_state_docs) == 1
        assert annotation_scene_docs[0]["annotations"] == ["something"]
        assert annotation_scene_state_docs[0]["annotation_scene_id"] == annotation_scene_docs[0]["_id"]

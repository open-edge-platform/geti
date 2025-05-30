# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from copy import deepcopy
from uuid import UUID

import pytest
from bson import ObjectId

from migration.scripts.add_dataset_storage_filter_data_preprocessing import (
    AddDatasetStorageFilterPreprocessingMigration,
)
from migration.utils import MongoDBConnection

ORGANIZATION_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
WORKSPACE_ID = UUID("11fdb5ad-8e0d-4301-b22b-06589beef658")
PROJECT_ID = ObjectId("66a0faf070cdf6d0b2ec5f93")


def create_dummy_documents(num_docs: int):
    docs = []
    for i in range(num_docs):
        doc_id = ObjectId(str(i).zfill(24))
        docs.append(
            {
                "_id": doc_id,
                "organization_id": ORGANIZATION_ID,
                "workspace_id": WORKSPACE_ID,
                "project_id": PROJECT_ID,
            }
        )

    return docs


@pytest.fixture()
def fxt_dataset_storage_filter_data():
    yield create_dummy_documents(100)


@pytest.fixture()
def fxt_dataset_storage_filter_data_with_preprocessing(fxt_dataset_storage_filter_data):
    dataset_storage_filter_data_with_preprocessing = deepcopy(fxt_dataset_storage_filter_data)
    for dataset_storage_filter_data in dataset_storage_filter_data_with_preprocessing:
        # pop
        dataset_storage_filter_data["preprocessing"] = "FINISHED"
    yield dataset_storage_filter_data_with_preprocessing


class TestAddDatasetStorageFilterPreprocessingMigration:
    def test_upgrade_project(
        self,
        fxt_dataset_storage_filter_data,
        request,
    ):
        def cleanup():
            # Remove the documents added during the test
            dataset_storage_filter_data_collection.delete_many(
                {"_id": {"$in": [doc["_id"] for doc in fxt_dataset_storage_filter_data]}}
            )

        request.addfinalizer(cleanup)

        database = MongoDBConnection().client["geti"]
        dataset_storage_filter_data_collection = database.get_collection("dataset_storage_filter_data")

        dataset_storage_filter_data_collection.insert_many(fxt_dataset_storage_filter_data)

        AddDatasetStorageFilterPreprocessingMigration.upgrade_project(
            organization_id=str(ORGANIZATION_ID),
            workspace_id=str(WORKSPACE_ID),
            project_id=str(PROJECT_ID),
        )

        collection = database.get_collection("dataset_storage_filter_data")
        for fxt_doc in fxt_dataset_storage_filter_data:
            doc = collection.find_one({"_id": fxt_doc["_id"]})
            assert "preprocessing" in doc
            assert doc["preprocessing"] == "FINISHED"

    def test_downgrade_project(
        self,
        fxt_dataset_storage_filter_data_with_preprocessing,
        request,
    ):
        def cleanup():
            # Remove the documents added during the test
            dataset_storage_filter_data_collection.delete_many(
                {"_id": {"$in": [doc["_id"] for doc in fxt_dataset_storage_filter_data_with_preprocessing]}}
            )

        request.addfinalizer(cleanup)

        database = MongoDBConnection().client["geti"]
        dataset_storage_filter_data_collection = database.get_collection("dataset_storage_filter_data")

        dataset_storage_filter_data_collection.insert_many(fxt_dataset_storage_filter_data_with_preprocessing)

        AddDatasetStorageFilterPreprocessingMigration.downgrade_project(
            organization_id=str(ORGANIZATION_ID),
            workspace_id=str(WORKSPACE_ID),
            project_id=str(PROJECT_ID),
        )

        collection = database.get_collection("dataset_storage_filter_data")
        for fxt_doc in fxt_dataset_storage_filter_data_with_preprocessing:
            doc = collection.find_one({"_id": fxt_doc["_id"]})
            assert "preprocessing" not in doc

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import pytest
from sc_sdk.repos.base.mongo_connector import MongoConnector
from sc_sdk.repos.mappers import IDToMongo

from job.repos.document_repo import DocumentRepo


@pytest.mark.ProjectIEMsComponent
class TestDocumentRepo:
    def test_get_project_document_from_db(
        self, request, fxt_organization_id, fxt_project_identifier_1, fxt_project_identifier_2
    ) -> None:
        # Insert some project documents in the db
        org_id = IDToMongo.forward(fxt_organization_id)
        project_docs = [
            {
                "_id": IDToMongo.forward(proj_ident.project_id),
                "organization_id": org_id,
                "workspace_id": IDToMongo.forward(proj_ident.workspace_id),
                "name": f"Project {str(proj_ident.project_id)}",
            }
            for proj_ident in [fxt_project_identifier_1, fxt_project_identifier_2]
        ]
        project_collection = MongoConnector.get_collection(collection_name=DocumentRepo.PROJECTS_COLLECTION)
        request.addfinalizer(lambda: project_collection.delete_many({"organization_id": org_id}))
        project_collection.insert_many(project_docs)

        document_repo_1 = DocumentRepo(fxt_project_identifier_1)
        document_repo_2 = DocumentRepo(fxt_project_identifier_2)
        found_project_doc_1 = document_repo_1._get_project_document_from_db()
        found_project_doc_2 = document_repo_2._get_project_document_from_db()

        assert found_project_doc_1["_id"] == IDToMongo.forward(fxt_project_identifier_1.project_id)
        assert found_project_doc_2["_id"] == IDToMongo.forward(fxt_project_identifier_2.project_id)

    @pytest.mark.parametrize("collection_name", ["project", "task_node"])
    def test_get_all_documents_from_db_collection(
        self, request, collection_name, fxt_ote_id, fxt_organization_id, fxt_workspace_id, fxt_project_identifier
    ) -> None:
        document_repo = DocumentRepo(fxt_project_identifier)
        # Insert some project documents in the db
        org_id = IDToMongo.forward(fxt_organization_id)
        ws_id = IDToMongo.forward(fxt_workspace_id)
        project_collection = MongoConnector.get_collection(collection_name="project")
        task_node_collection = MongoConnector.get_collection(collection_name="task_node")
        proj_doc = {
            "_id": IDToMongo.forward(fxt_project_identifier.project_id),
            "organization_id": org_id,
            "workspace_id": ws_id,
            "name": "TestProject",
        }
        task_node_docs = [
            {
                "_id": IDToMongo.forward(fxt_ote_id(i)),
                "organization_id": org_id,
                "workspace_id": ws_id,
                "project_id": IDToMongo.forward(fxt_project_identifier.project_id),
                "name": f"Task {i}",
            }
            for i in range(100, 102)
        ]
        request.addfinalizer(lambda: project_collection.delete_many({"organization_id": org_id}))
        request.addfinalizer(lambda: task_node_collection.delete_many({"organization_id": org_id}))
        project_collection.insert_one(proj_doc)
        task_node_collection.insert_many(task_node_docs)

        found_docs = list(document_repo._get_all_documents_from_db_collection(collection_name))

        if collection_name == DocumentRepo.PROJECTS_COLLECTION:
            assert len(found_docs) == 1  # 1 project document
            assert found_docs[0]["_id"] == IDToMongo.forward(fxt_project_identifier.project_id)
        else:
            assert len(found_docs) == 2  # 2 task node documents

    def test_get_all_documents_from_db(self, fxt_project_identifier) -> None:
        document_repo = DocumentRepo(fxt_project_identifier)
        with (
            patch.object(DocumentRepo, "_get_project_document_from_db", return_value=iter([])) as mock_get_project_doc,
            patch.object(
                DocumentRepo, "_get_all_documents_from_db_collection", return_value=iter([])
            ) as mock_get_docs_from_collection,
        ):
            collection_names = ("project", "task_node")
            for coll_name in collection_names:
                document_repo.get_all_documents_from_db_for_collection(collection_name=coll_name)

        mock_get_project_doc.assert_called_once_with()
        mock_get_docs_from_collection.assert_called_once_with(collection_name="task_node")

    @pytest.mark.parametrize("collection_name", ["project", "other"])
    def test_insert_documents_to_db_collection(
        self, request, collection_name, fxt_ote_id, fxt_organization_id, fxt_workspace_id, fxt_project_identifier
    ) -> None:
        document_repo = DocumentRepo(fxt_project_identifier)
        org_id = IDToMongo.forward(fxt_organization_id)
        ws_id = IDToMongo.forward(fxt_workspace_id)
        docs = [
            {
                "_id": IDToMongo.forward(fxt_ote_id(i)),
                "organization_id": org_id,
                "workspace_id": ws_id,
                "foo": "bar",
            }
            for i in range(3)
        ]
        collection = MongoConnector.get_collection(collection_name=collection_name)
        request.addfinalizer(lambda: collection.delete_many({"organization_id": org_id}))

        document_repo.insert_documents_to_db_collection(
            collection_name=collection_name, documents=docs, insertion_batch_size=2
        )

        assert collection.count_documents({}) == len(docs)

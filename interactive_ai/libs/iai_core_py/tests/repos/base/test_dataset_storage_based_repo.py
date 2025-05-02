# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import patch

from bson import ObjectId

from iai_core.repos.base import SessionBasedRepo
from iai_core.repos.base.session_repo import QueryAccessMode

from geti_types import DatasetStorageIdentifier, make_session


class TestDatasetStorageBasedSessionRepo:
    def test_preliminary_query_match_filter(self, fxt_ote_id, fxt_dataset_storage_based_session_repo) -> None:
        session = make_session()
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=session.workspace_id,
            project_id=fxt_ote_id(2),
            dataset_storage_id=fxt_ote_id(3),
        )
        repo = fxt_dataset_storage_based_session_repo(
            session=session, dataset_storage_identifier=dataset_storage_identifier
        )

        with patch.object(
            SessionBasedRepo, "preliminary_query_match_filter", return_value={}
        ) as mock_super_match_filter:
            out_filter = repo.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)

        mock_super_match_filter.assert_called_once_with(access_mode=QueryAccessMode.READ)
        assert out_filter == {
            "workspace_id": ObjectId(str(dataset_storage_identifier.workspace_id)),
            "project_id": ObjectId(str(dataset_storage_identifier.project_id)),
            "dataset_storage_id": ObjectId(str(dataset_storage_identifier.dataset_storage_id)),
        }

    def test_indexes(self, fxt_ote_id, fxt_dataset_storage_based_session_repo) -> None:
        session = make_session()
        dataset_storage_identifier = DatasetStorageIdentifier(
            workspace_id=fxt_ote_id(1),
            project_id=fxt_ote_id(2),
            dataset_storage_id=fxt_ote_id(3),
        )
        repo = fxt_dataset_storage_based_session_repo(
            session=session, dataset_storage_identifier=dataset_storage_identifier
        )

        indexes_names = set(repo._collection.index_information().keys())

        assert indexes_names == {
            "_id_",
            "organization_id_-1_workspace_id_-1_project_id_-1_dataset_storage_id_-1__id_1",
        }

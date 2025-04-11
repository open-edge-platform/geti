# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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

import pytest
from bson import ObjectId

from sc_sdk.entities.model_storage import ModelStorageIdentifier
from sc_sdk.repos.base import SessionBasedRepo
from sc_sdk.repos.base.session_repo import QueryAccessMode

from geti_types import make_session


@pytest.mark.ScSdkComponent
class TestModelStorageBasedSessionRepo:
    def test_preliminary_query_match_filter(self, fxt_ote_id, fxt_model_storage_based_session_repo) -> None:
        session = make_session()
        model_storage_identifier = ModelStorageIdentifier(
            workspace_id=session.workspace_id,
            project_id=fxt_ote_id(2),
            model_storage_id=fxt_ote_id(3),
        )
        repo = fxt_model_storage_based_session_repo(session=session, model_storage_identifier=model_storage_identifier)

        with patch.object(
            SessionBasedRepo, "preliminary_query_match_filter", return_value={}
        ) as mock_super_match_filter:
            out_filter = repo.preliminary_query_match_filter(access_mode=QueryAccessMode.READ)

        mock_super_match_filter.assert_called_once_with(access_mode=QueryAccessMode.READ)
        assert out_filter == {
            "workspace_id": ObjectId(str(model_storage_identifier.workspace_id)),
            "project_id": ObjectId(str(model_storage_identifier.project_id)),
            "model_storage_id": ObjectId(str(model_storage_identifier.model_storage_id)),
        }

    def test_indexes(self, fxt_ote_id, fxt_model_storage_based_session_repo) -> None:
        session = make_session()
        model_storage_identifier = ModelStorageIdentifier(
            workspace_id=fxt_ote_id(1),
            project_id=fxt_ote_id(2),
            model_storage_id=fxt_ote_id(3),
        )
        repo = fxt_model_storage_based_session_repo(session=session, model_storage_identifier=model_storage_identifier)

        indexes_names = set(repo._collection.index_information().keys())

        assert indexes_names == {
            "_id_",
            "organization_id_-1_workspace_id_-1_project_id_-1_model_storage_id_-1__id_1",
        }

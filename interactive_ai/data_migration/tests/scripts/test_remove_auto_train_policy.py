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

from collections.abc import Callable
from functools import partial
from unittest.mock import patch

import mongomock
import pytest
from pymongo import MongoClient

from migration.scripts.remove_auto_train_policy import RemoveAutoTrainPolicyMigration


class TestRemoveAutoTrainPolicyMigration:
    @pytest.mark.parametrize("collection_exists", [True, False], ids=["existing", "non-existing"])
    def test_upgrade_non_project_data(self, collection_exists) -> None:
        def drop_collection_with_return(collection_name: str, original_fn: Callable):
            # wrapper around mongomock.Database.drop_collection that returns info, like the pymongo method does
            original_fn(collection_name)
            return {"ok": 1.0}

        mock_db = mongomock.MongoClient(uuidRepresentation="standard").db
        if collection_exists:
            mock_db.create_collection("auto_train_policy")
            assert "auto_train_policy" in mock_db.list_collection_names()
        else:
            assert "auto_train_policy" not in mock_db.list_collection_names()

        with (
            patch.object(MongoClient, "get_database", return_value=mock_db),
            patch.object(
                mock_db,
                "drop_collection",
                new=partial(drop_collection_with_return, original_fn=mock_db.drop_collection),
            ),
        ):
            RemoveAutoTrainPolicyMigration.upgrade_non_project_data()

        assert "auto_train_policy" not in mock_db.list_collection_names()

    @pytest.mark.parametrize("collection_exists", [True, False], ids=["existing", "non-existing"])
    def test_downgrade_non_project_data(self, collection_exists) -> None:
        mock_db = mongomock.MongoClient(uuidRepresentation="standard").db
        if collection_exists:
            mock_db.create_collection("auto_train_policy")
            assert "auto_train_policy" in mock_db.list_collection_names()
        else:
            assert "auto_train_policy" not in mock_db.list_collection_names()

        with patch.object(MongoClient, "get_database", return_value=mock_db):
            RemoveAutoTrainPolicyMigration.downgrade_non_project_data()

        assert "auto_train_policy" in mock_db.list_collection_names()

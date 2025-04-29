# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

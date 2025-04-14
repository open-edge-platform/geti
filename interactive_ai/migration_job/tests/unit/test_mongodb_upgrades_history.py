# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from datetime import datetime

import mongomock
import pytest
from bson import ObjectId

from migration_job.mongodb_upgrades_history import MigrationHistory


@pytest.mark.component
class TestMigrationHistory:
    @pytest.mark.parametrize("previous_upgrade_exists", [False, True], ids=["first upgrade", "previously upgraded"])
    def test_get_current_data_version(self, previous_upgrade_exists) -> None:
        mongo_client = mongomock.MongoClient()  # type: ignore
        db_name = "test_db"
        migration_history = MigrationHistory(client=mongo_client, db_name=db_name)
        collection = mongo_client[db_name][MigrationHistory.COLLECTION_NAME]
        if previous_upgrade_exists:
            upgrade_docs = [
                {
                    "_id": ObjectId("5f9b1b3b7b3b4b0001e1b3b4"),
                    "filepath": "foo.py",
                    "description": "Foo script",
                    "downgradability": True,
                    "current_version": "1.0",
                    "target_version": "2.0",
                    "start_date": datetime(2020, 1, 1),
                    "stop_date": datetime(2020, 1, 2),
                },
                {
                    "_id": ObjectId("5f9b1b3b7b3b4b0001e1b3b5"),
                    "filepath": "bar.py",
                    "description": "Bar script",
                    "downgradability": False,
                    "current_version": "2.0",
                    "target_version": "3.0",
                    "start_date": datetime(2020, 1, 2),
                    "stop_date": datetime(2020, 1, 3),
                },
            ]
            collection.insert_many(upgrade_docs)

        curr_data_version = migration_history.get_current_data_version()

        assert curr_data_version == "3.0" if previous_upgrade_exists else "1.0"

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

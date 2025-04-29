# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import re
from collections import UserDict
from datetime import datetime
from typing import TYPE_CHECKING

from geti_logger_tools.logger_config import initialize_logger
from pymongo import DESCENDING, MongoClient

if TYPE_CHECKING:
    from pymongo.collection import Collection

DEFAULT_DATABASE_NAME = "geti"

logger = initialize_logger(__name__, use_async=False)


class MigrationStepDocument(UserDict):
    def __init__(  # noqa: PLR0913
        self,
        changeset_id: str | None = None,
        filepath: str | None = None,
        author: str | None = None,
        description: str | None = None,
        backward_compatibility: bool | None = None,
        downgradability: bool | None = None,
        current_version: str | None = None,
        target_version: str | None = None,
        start_date: datetime | None = None,
        stop_date: datetime | None = None,
    ) -> None:
        super().__init__()
        self.data["id"] = changeset_id
        self.data["filepath"] = filepath
        self.data["author"] = author
        self.data["description"] = description
        self.data["backward_compatibility"] = backward_compatibility
        self.data["downgradability"] = downgradability
        self.data["current_version"] = current_version
        self.data["target_version"] = target_version
        self.data["start_date"] = start_date
        self.data["stop_date"] = stop_date


class MigrationHistory:
    COLLECTION_NAME = "upgrades_history"

    def __init__(self, client: MongoClient, db_name: str = DEFAULT_DATABASE_NAME) -> None:
        self.client = client
        self.db = self.client[db_name]
        self.collection: Collection = self.db[self.COLLECTION_NAME]

    def create_collection_if_not_exists(self) -> None:
        if self.COLLECTION_NAME not in self.db.list_collection_names():
            self.db.create_collection(self.COLLECTION_NAME)

    def insert_document(self, document: MigrationStepDocument) -> bool:
        result = self.collection.insert_one(document.data)
        return result.acknowledged

    def get_current_data_version(self) -> str:
        """
        Determine the current data version based on the history of previous upgrades.
        If no history is found, the data version is assumed to be '1.0'.

        :return: data version as string
        """
        last_upgrade_info = self.collection.find_one(sort=[("_id", DESCENDING)])
        if last_upgrade_info is None or not bool(
            re.match(r"^\d+\.\d+$", last_upgrade_info.get("target_version", "missing"))
        ):
            logger.warning(
                f"Could not determine the current data version through the database (found '{last_upgrade_info}');"
                f" defaulting to '1.0'."
            )
            return "1.0"
        return last_upgrade_info["target_version"]

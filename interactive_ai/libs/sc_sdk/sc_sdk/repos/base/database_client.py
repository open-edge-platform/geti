"""
This module contains the base implementation for database client.
"""

# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

import logging
import os
from typing import TypeVar

import pymongo

from geti_types import Singleton

AnyType = TypeVar("AnyType")


class DatabaseClient(metaclass=Singleton):
    """
    Singleton containing a database client shared across the entire application.
    """

    def __init__(self) -> None:
        database_address = os.environ.get("DATABASE_ADDRESS", "mongodb://localhost:27017/")
        database_username = os.environ.get("DATABASE_USERNAME", None)
        database_password = os.environ.get("DATABASE_PASSWORD", None)

        self.client: pymongo.MongoClient = pymongo.MongoClient(
            database_address, username=database_username, password=database_password
        )

    def is_running(self) -> bool:
        """
        Check whether the MongoDB server is running.
        """
        try:
            self.client.server_info()
        except Exception:
            logging.exception("The MongoDB server is not reachable.")
            return False

        return True

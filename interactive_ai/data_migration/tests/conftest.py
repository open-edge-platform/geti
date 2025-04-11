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

import logging
import os
from unittest.mock import patch

import pytest
from testcontainers.mongodb import MongoDbContainer

from migration.utils.connection import MongoDBConnection

os.environ["MONGODB_DATABASE_NAME"] = "geti"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def mongodb_testcontainer():
    docker_registry = os.getenv("REGISTRY", "")
    image_name = os.path.join(docker_registry, "mongo:7.0.7")
    logger.info(f"Pulling MongoDB testcontainer image from: {image_name}")
    with MongoDbContainer(image_name) as mongo:
        db_url = mongo.get_connection_url()
        with patch.object(MongoDBConnection, "_get_connection_string", return_value=db_url):
            logger.info(f"MongoDB container started at {MongoDBConnection._get_connection_string()}")
            yield mongo

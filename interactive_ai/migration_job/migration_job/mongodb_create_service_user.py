"""A script for creating MongoDB users for platform services."""

# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

import logging
import os
import sys
from collections.abc import Sequence

import pymongo

from migration_job.utils import create_mongo_client

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

MONGODB_CMD_CREATE_USER = "createUser"
MONGODB_CMD_USERS_INFO = "usersInfo"


def create_user(client: pymongo.MongoClient, username: str, password: str, roles: Sequence[str]) -> None:
    """
    Creates MongoDB users with readWriteAnyDatabase role.

    :param client: The MongoClient to use for executing the Mongo commands.
    :param username: The username for the new user.
    :param password: The password for the new user.
    :param roles: All-database roles for the new user.
    """
    logger.info(f"Creating user: {username}")
    client.admin.command(MONGODB_CMD_CREATE_USER, username, pwd=password, roles=roles)


def does_user_exist(client: pymongo.MongoClient, username: str) -> bool:
    """Checks whether a user with the provided username exists in the `admin` database.

    :param client: The MongoClient to use for executing the Mongo commands.
    :param username: The username of the looked for user.

    :return bool: True if the user with the provided username exists in the
        admin DB. Otherwise, False.
    """
    users = client.admin.command(MONGODB_CMD_USERS_INFO)["users"]  # type: ignore
    return any(user["user"] == username for user in users)


def _parse_roles(roles_str: str) -> Sequence[str]:
    """Parses the serialized roles string.

    :param roles_str: String containing comma-separated all-database roles,
        e.g. "readWriteAnyDatabase,dbAdminAnyDatabase".

    :return Sequence[str]: Sequence of str representing all-database roles.
    """
    return [role.strip() for role in roles_str.split(",") if role.strip()]


def main():  # noqa: ANN201
    """The script's entry point.

    :raise EnvironmentError: If any of the required environment variables is not set.
    """
    try:
        # Credentials for the MongoDB user to be created.
        db_username_service = os.environ["DATABASE_USERNAME_SERVICE"]
        db_password_service = os.environ["DATABASE_PASSWORD_SERVICE"]

        # A string containing comma-separated, all-database MongoDB roles for the user to be created.
        # E.g. "readWriteAnyDatabase,dbAdminAnyDatabase".
        service_user_all_db_roles = os.environ["SERVICE_USER_ALL_DB_ROLES"]
    except KeyError as err:
        raise OSError("The required environment variables are not set correctly.") from err

    client = create_mongo_client()

    if does_user_exist(client=client, username=db_username_service):
        logger.warning(f"User {repr(db_username_service)} already exists, skipping creation.")
        return

    roles = _parse_roles(service_user_all_db_roles)
    create_user(
        client=client,
        username=db_username_service,
        password=db_password_service,
        roles=roles,
    )

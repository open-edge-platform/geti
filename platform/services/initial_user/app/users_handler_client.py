# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import base64
import os
from collections.abc import Mapping
from typing import Any

from geti_logger_tools.logger_config import initialize_logger
from geti_spicedb_tools import RoleMutationOperations, SpiceDB, SpiceDBUserRoles

from users_handler.exceptions import UserDoesNotExist
from users_handler.users_handler import AuthorizationRelationships, UsersHandler, UserType

INITIAL_USER_PASSWORD = os.getenv("INITIAL_USER_PASSWORD", "")
FIND_USER: Mapping[Any, Any] = {
    "first_name": "admin",
    "second_name": "admin",
    "email": os.getenv("INITIAL_USER_EMAIL", ""),
    "country": "POL",
    "status": "ACT",
}


logger = initialize_logger(__name__)


class UsersHandlerConnection:
    """
    Provides connection to OpenLDAP via Users Handler.
    """

    def __init__(self) -> None:
        self.host = os.environ.get("LDAP_HOST", "impt-openldap")
        self.port = int(os.environ.get("LDAP_PORT", "389"))
        self.service_user = f"cn={os.environ.get('LDAP_ADMIN_USER', '')},dc=example,dc=org"
        self.service_password = os.environ.get("LDAP_ADMIN_PASSWORD", "")
        auth_config = {
            "user": self.service_user,
            "password": self.service_password,
            "host": self.host,
            "port": self.port,
        }

        logger.info(f"Initializing UsersHandler: {self.host}:{self.port}")
        self.users_handler = UsersHandler(**auth_config)

    def get_accounts_for_migration(self) -> list[UserType]:
        return self.users_handler.list_users()

    @staticmethod
    def update_roles_in_spicedb(user_id: str, role: dict) -> None:
        SpiceDB().change_user_relation(
            user_id=user_id,
            relations=[SpiceDBUserRoles[role["resource_type"].upper()].value[role["role"].lower()]],
            resource_id=role["resource_id"],
            resource_type=role["resource_type"],
            operation=RoleMutationOperations.TOUCH,
        )

    def create_initial_user(self, uid: str, workspace_id: str, organization_id: str) -> bool:
        roles = [
            {"role": "ADMIN", "resource_id": workspace_id, "resource_type": "workspace"},
            {"role": "ADMIN", "resource_id": organization_id, "resource_type": "organization"},
        ]
        password = base64.b64encode(INITIAL_USER_PASSWORD.encode("ascii")).decode("ascii")
        user_auth_relationships = [
            AuthorizationRelationships(
                resource_type=role["resource_type"],
                resource_id=role["resource_id"],
                relations=[SpiceDBUserRoles[role["resource_type"].upper()].value[role["role"].lower()]],
                operation=RoleMutationOperations.TOUCH,
            )
            for role in roles
        ]
        try:
            find_user = self.users_handler.get_user(uid=uid)
            logger.debug(f"Received response from OpenLDAP when searching for user with uid {uid}: {find_user}")
            if find_user:
                logger.info("User already exist in openldap.")
                return False
        except UserDoesNotExist:
            logger.debug("User not found. Proceed with creation.")

        logger.info(f"User {FIND_USER['email']} added to openldap as a admin.")
        return self.users_handler.add_user(
            uid=uid,
            name=FIND_USER["first_name"],
            mail=FIND_USER["email"],
            password=password,
            admin=True,
            registered=True,
            authorization_relationships=user_auth_relationships,
        )

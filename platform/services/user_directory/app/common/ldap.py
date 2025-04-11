# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import base64
import logging
import os

from pydantic.main import BaseModel

from users_handler.exceptions import EmailAlreadyExists, UserDoesNotExist, WeakPassword
from users_handler.users_handler import UsersHandler

logger = logging.getLogger(__name__)


class UsersHandlerUser(BaseModel):
    email: str
    first_name: str | None = None
    password: str
    roles: list | None = None


class OpenLDAPConnection:
    def __init__(self) -> None:
        self.host = os.environ.get("LDAP_HOST", "impt-openldap")
        self.port = int(os.environ.get("LDAP_PORT", 389))  # noqa: PLW1508
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

    def create_initial_user(self, uid: str, data: UsersHandlerUser) -> bool:
        password = base64.b64encode((base64.b64decode(data.password).decode("utf-8")).encode("ascii")).decode("ascii")
        try:
            find_user = self.users_handler.get_user(uid=uid)
            logger.debug(f"Received response from OpenLDAP when searching for user with uid {uid}: {find_user}")
            if find_user:
                logger.info("User already exists in openldap.")
                return False
        except UserDoesNotExist:
            logger.debug("User not found. Proceed with creation.")
        try:
            return self.users_handler.add_user(
                uid=uid,
                name=data.first_name if data.first_name is not None else "noname",
                mail=data.email,
                password=password,
                admin=True,
                registered=True,
            )
        except EmailAlreadyExists:
            logger.debug("User already exists in openldap.")
            return False
        except WeakPassword:
            logger.debug("Password is too weak.")
            return False

    def delete_user(self, uid: str) -> bool:
        return self.users_handler.delete_user(uid)

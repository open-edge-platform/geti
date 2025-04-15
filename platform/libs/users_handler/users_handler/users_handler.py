"""Module to manage users"""

# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

import base64
import logging
import os
import re
import secrets
from binascii import a2b_base64, b2a_base64
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import NamedTuple

import jwt
import ldap
from cryptography.exceptions import InvalidKey
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from geti_spicedb_tools import (
    AccessResourceTypes,
    Permissions,
    Relations,
    RoleMutationOperations,
    SpiceDB,
    SpiceDBResourceTypes,
    SpiceDBUserRoles,
    UserRoles,
)
from PIL import Image

from users_handler import string as utils_string
from users_handler.audit_logger import AuditLogger
from users_handler.enums import LdapAttr
from users_handler.exceptions import (
    EmailAlreadyExists,
    InvalidEmail,
    SameNewPassword,
    UserAlreadyExists,
    UserDoesNotExist,
    UserHandlerError,
    WeakPassword,
    WrongOldPassword,
    WrongUserToken,
)
from users_handler.user_role import UserRole  # noqa: F401
from users_handler.user_type import UserType
from users_handler.validation import validate_user_input

logger = logging.getLogger(__name__)
audit_logger = logging.getLogger(__name__ + "-audits")
file_handler = AuditLogger.get_spicedb_file_handler()
audit_logger.addHandler(file_handler)

# default to localhost for easier integration testing with port-forward
_SPICEDB_ADDRESS = os.environ.get("SPICEDB_ADDRESS", "localhost:50051")
_SPICEDB_TOKEN = os.environ.get("SPICEDB_TOKEN")

Image.MAX_IMAGE_PIXELS = 200000000

IMAGE_WEIGHT_LIMIT_KB = 500
IMAGE_MIN_SIZE_PIXELS = 32
IMAGE_MAX_SIZE_PIXELS = 20000

LENGTH_UID = 32
LENGTH_PASSWORD = 32


class AuthorizationRelationships(NamedTuple):
    resource_type: str | None = None
    resource_id: str | None = None
    relations: list[Relations] = []
    operation: RoleMutationOperations = RoleMutationOperations.CREATE


class UsersHandler:
    """Main class to handle users"""

    BASE = "dc=example,dc=org"
    USERS_ATTRIBUTES = (
        LdapAttr.cn,
        LdapAttr.uid,
        LdapAttr.mail,
        LdapAttr.name,
        LdapAttr.group,
        LdapAttr.registered,
        LdapAttr.email_token,
    )
    ADMIN_GID = 500
    USER_GID = 501

    JWT_ALGORITHM = "HS256"

    def __init__(self, password, host="localhost", port=389, user="cn=admin,dc=example,dc=org") -> None:  # noqa: ANN001
        self._host = host
        self._port = port
        self._user = user
        self._password = password

        self._connect()

        self._authzed_client = SpiceDB()

    def _connect(self) -> None:
        logger.debug(f"Connecting to LDAP host {self._host}:{self._port} as {self._user}")
        self._connection = ldap.initialize(f"ldap://{self._host}:{self._port}", bytes_mode=False)
        self._connection.set_option(ldap.OPT_REFERRALS, 0)
        self._connection.simple_bind_s(self._user, self._password)

    @staticmethod
    def is_email_valid(mail: str) -> bool:
        """Validates email address format"""
        if len(mail) < 5 or len(mail) > 64:
            raise InvalidEmail(f"Invalid email length: {mail}")
        regex = re.compile(
            r"^[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*@"
            r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$"
        )
        if re.fullmatch(regex, mail):
            return True
        raise InvalidEmail(f"Invalid email: {mail}")

    @staticmethod
    def _get_attribute(attributes: dict, attribute_key: str) -> list | None:
        attribute = attributes.get(attribute_key)
        if attribute and len(attribute) > 0:
            return [el.decode() for el in attribute]
        return None

    @staticmethod
    def _get_first_attribute(attributes: dict, attribute_key: str) -> str | None:
        attribute = UsersHandler._get_attribute(attributes, attribute_key)
        if attribute:
            return attribute[0]
        return None

    @classmethod
    def _get_user_gid(cls, is_admin: bool):
        return (cls.USER_GID, cls.ADMIN_GID)[is_admin]

    @staticmethod
    def _base64_encode(data: str) -> str:
        """Encode data as base64 with padding removed"""
        return base64.encodebytes(data.encode("utf-8")).decode("utf-8").replace("=", "").replace("\n", "")

    @staticmethod
    def _ab64_encode(data) -> str:  # noqa: ANN001
        return b2a_base64(data).decode("ascii").rstrip("=\n").replace("+", ".")

    @staticmethod
    def _ab64_decode(data: str):  # noqa: ANN205
        data = data.replace(".", "+")
        return a2b_base64(data + "=" * (-len(data) % 4))

    def _hash_password(self, clear_pass) -> str:  # noqa: ANN001
        salt = secrets.token_bytes(16)
        iterations = 25000
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=64,
            salt=salt,
            iterations=iterations,
        )
        key = kdf.derive(clear_pass)
        return "{}{}${}${}".format("{PBKDF2-SHA512}", iterations, self._ab64_encode(salt), self._ab64_encode(key))

    def _get_latest_uid_number(self) -> int:
        try:
            data = self._connection.search_s(
                base=self.BASE, scope=ldap.SCOPE_SUBTREE, filterstr="(objectClass=*)", attrlist=["uidNumber"]
            )
        except ldap.LDAPError as ldap_error:
            raise UserHandlerError("Can't get uid number") from ldap_error

        latest_uid = 0
        if len(data) == 0:
            logger.info("Empty uid list")
            return 1001
        for entry in list(data):
            uid = entry[1].get("uidNumber", None)
            if uid and int(uid[0]) > latest_uid:
                latest_uid = int(uid[0])
        return latest_uid

    @staticmethod
    def check_password_strength(password: str) -> None:
        """
        Check strength of a new password
        :param password: base64 URL safe encoded password
        """
        decoded_pass = base64.urlsafe_b64decode(password).decode("ascii")
        check = re.match(
            r"^(?=.*[A-Z])(?=.*[a-z])((?=.*[0-9])|(?=.*[\ !\"#$%&'()*+,-.\/:;<=>?@\[\\\]^_`{|}~]))[A-Za-z0-9\ !\"#$%&'"
            r"()*+,-.\/:;<=>?@\[\\\]^_`{|}~]{8,200}$",
            decoded_pass,
        )
        if check is None:
            error = "Password must have 8-200 characters, at least one capital letter, lower letter, digit or symbol"
            logger.error(error)
            raise WeakPassword(error)

    def verify_current_password(self, current_password: str, old_password: str) -> None:
        """
        Check if password is correct
        :param current_password: current password from ldap
        :param old_password: password to check against
        """
        salt_b64 = re.search("\\$(.*)\\$", current_password).group(1)  # type: ignore
        key_b64 = re.search(".*\\$(.*)", current_password).group(1)  # type: ignore
        key = self._ab64_decode(key_b64)
        salt = self._ab64_decode(salt_b64)
        iterations = 25000
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=64,
            salt=salt,
            iterations=iterations,
        )
        pass_old_decoded = base64.urlsafe_b64decode(old_password)
        try:
            kdf.verify(pass_old_decoded, key)
        except InvalidKey as invalid_key:
            logger.error("Given old password for user is wrong")
            raise WrongOldPassword("Given old password for user is wrong") from invalid_key

    def validate_password(self, uid: str, new_password: str, old_password: str) -> bool:
        """
        Validate a new password
        :param uid: User uid
        :param new_password: base64 URL safe encoded new user password
        :param old_password: base64 URL safe encoded old user password
        :return: boolean, True if success
        """
        logger.info(f"Validating a new password for user {uid}")

        password_ldap = self.get_password(uid=uid)
        self.verify_current_password(password_ldap, old_password)

        if new_password == old_password:
            logger.error(f"New and old passwords for user {uid} cannot be the same")
            raise SameNewPassword(f"New and old passwords for user {uid} cannot be the same")

        return True

    def get_password(self, uid: str) -> str:
        """
        Get password from LDAP for given user.
        """
        try:
            data = self._connection.search_s(
                base=self.BASE,
                scope=ldap.SCOPE_SUBTREE,
                filterstr="(&(objectClass=inetOrgPerson)(objectClass=posixAccount)(objectClass=top))",
                attrlist=(LdapAttr.uid, LdapAttr.user_password),
            )
        except ldap.LDAPError as ldap_error:
            logger.error("Can't list users")
            raise AttributeError("Can't list users") from ldap_error

        for entry in list(data):
            attr = entry[1]
            uid_ldap = self._get_first_attribute(attr, LdapAttr.uid)
            password_ldap = self._get_first_attribute(attr, LdapAttr.user_password)
            if uid_ldap == uid and password_ldap is not None:
                return password_ldap

        raise UserDoesNotExist(f"User with uid: {uid} not found")

    def list_users(self) -> list[UserType]:
        """
        :return: List of all users (legacy service accounts excluded)
        """
        try:
            data = self._connection.search_s(
                base=self.BASE,
                scope=ldap.SCOPE_SUBTREE,
                filterstr="(&(objectClass=inetOrgPerson)(objectClass=posixAccount)(objectClass=top))",
                attrlist=self.USERS_ATTRIBUTES,
            )
        except ldap.LDAPError as ldap_error:
            logger.error("Can't list users")
            raise AttributeError("Can't list users") from ldap_error

        out = []
        for entry in list(data):
            attr = entry[1]
            name = self._get_first_attribute(attr, LdapAttr.name)
            uid = self._get_first_attribute(attr, LdapAttr.uid)
            mail = self._get_first_attribute(attr, LdapAttr.mail)
            registered = self._get_first_attribute(attr, LdapAttr.registered)
            email_token = self._get_first_attribute(attr, LdapAttr.email_token)
            user_registered = False
            if registered is not None:
                user_registered = registered.lower() == "true"
            gid = int(attr.get(LdapAttr.group)[0])

            # Return only Admins and Users
            if gid not in [self.ADMIN_GID, self.USER_GID]:
                continue

            roles: list = ([], [UserRoles.ADMIN.name])[gid == self.ADMIN_GID]  # required for 1.1->1.2 migration
            if name is None or uid is None or mail is None:
                logger.debug(f"Empty field in User entry {entry}")
            else:
                user = UserType(
                    name=name,
                    uid=uid,  # type: ignore
                    mail=mail,
                    roles=roles,
                    group=gid,
                    registered=user_registered,
                    email_token=email_token,
                )
                out.append(user)
        return out

    def validate_unique_entry(self, uid=None, mail=None) -> None:  # noqa: ANN001
        """Ensures no user with given parameters is in db"""
        users = self.list_users()
        for user in users:
            if uid is not None and user[LdapAttr.uid] == uid:  # type: ignore
                raise UserAlreadyExists
            if mail is not None and user[LdapAttr.mail] == mail:  # type: ignore
                raise EmailAlreadyExists

    def get_user(self, uid: str) -> UserType:
        """
        Returns user with given id
        :param uid:
        :return: UserType Dict
        :raises UserDoesNotExist: On failure to find a user with the provided UID.
        """
        users = self.list_users()
        for user in users:
            if user["uid"] == uid:
                return user
        raise UserDoesNotExist(f"User with uid: {uid} not found")

    def add_user(
        self,
        uid: str,
        password: str,
        name: str,
        authorization_relationships: Sequence[AuthorizationRelationships] = (),
        mail: str = "",
        admin: bool = False,
        registered: bool = True,
    ) -> bool:
        """
        Creates new user
        :param uid: new user uid, needs to be unique
        :param password: base64 URL safe encoded user password
        :param name: new user name
        :param mail: new user mail
        :param admin: boolean, if True user will be created as admin, default False
        :param registered: boolean, if True user will be flagged as registered, default True
        :param authorization_relationships: list of relations set for user in spicedb
        :return: boolean, True if success
        """
        gid = self._get_user_gid(admin)
        self.is_email_valid(mail=mail)
        self.validate_unique_entry(uid=uid, mail=mail)

        latest_uid = self._get_latest_uid_number()
        self.check_password_strength(password)
        password_decoded = base64.urlsafe_b64decode(password)
        password_hash = self._hash_password(password_decoded)

        modslist = {
            "objectClass": ["inetOrgPerson", "posixAccount", "top"],
            LdapAttr.name: [name],
            LdapAttr.uid: [uid],
            LdapAttr.cn: [uid],
            "uidNumber": [str(latest_uid + 1)],
            "homeDirectory": [f"/home/users/{uid}"],
            LdapAttr.group: [str(gid)],
            LdapAttr.mail: [mail],
            LdapAttr.user_password: [password_hash],
            LdapAttr.registered: [str(registered)],
        }
        modlist = {key: [v.encode() for v in values] for key, values in modslist.items()}

        uid_b64: str = self._base64_encode(uid)

        # Create necessary SpiceDB relationships for the new user.
        for relation in authorization_relationships:
            self._authzed_client.change_user_relation(
                resource_type=relation.resource_type,  # type: ignore
                user_id=uid_b64,
                resource_id=relation.resource_id,  # type: ignore
                relations=relation.relations,
                operation=relation.operation,
            )

        try:
            self._connection.add_s(dn=f"cn={ldap.dn.escape_dn_chars(uid)},{self.BASE}", modlist=list(modlist.items()))
        except ldap.LDAPError as ldap_error:
            self._authzed_client.delete_relations(user_id=uid_b64, object_type=SpiceDBResourceTypes.USER.value)
            raise UserHandlerError(f"Can't create user: {uid}") from ldap_error

        return True

    def delete_user(self, uid: str) -> bool:
        """
        Removes user with given uid
        :param uid: User uid
        :return: boolean, True if success
        """

        self._authzed_client.delete_relations(
            user_id=self._base64_encode(uid),
            object_type=SpiceDBResourceTypes.USER.value,
        )

        try:
            self._connection.delete_s(dn=f"cn={ldap.dn.escape_dn_chars(uid)},{self.BASE}")
        except ldap.LDAPError:
            logger.error(f"Can't delete user {uid}")
            return False

        return True

    def change_user_password(self, uid: str, new_password: str) -> bool:
        """
        Change user password with given uid
        :param uid: User uid
        :param new_password:  base64 URL safe encoded user password
        :return: boolean, True if success
        """
        password_decoded = base64.urlsafe_b64decode(new_password)
        password_hash = self._hash_password(password_decoded)
        encoded_password = password_hash.encode()

        try:
            self._connection.modify_s(
                dn=f"cn={ldap.dn.escape_dn_chars(uid)},{self.BASE}",
                modlist=[(ldap.MOD_REPLACE, LdapAttr.user_password, [encoded_password])],
            )
        except ldap.LDAPError as ldap_error:
            logger.error(f"Can't update user {uid} password")
            raise UserHandlerError(f"Can't update user {uid} password") from ldap_error
        return True

    def generate_jwt_token(self, uid: str, exp_period_in_min: int, secret: str, mail: str | None = None) -> str:
        """
        Generate JWT token based on user email, save it to ldap and return as string
        """
        exp_time = datetime.now(tz=timezone.utc) + timedelta(minutes=exp_period_in_min)
        header = {"alg": UsersHandler.JWT_ALGORITHM, "typ": "JWT"}
        if not mail:
            mail = uid
        payload = {"uid": uid, "mail": mail, "exp": exp_time}
        token = jwt.encode(payload=payload, key=secret, algorithm=UsersHandler.JWT_ALGORITHM, headers=header)
        self.edit_user(uid=uid, email_token=token)
        return token

    def _generate_unique_uid(self) -> str:
        """
        Generates unique UID.

        :return str: The generated unique UID.
        """
        while True:
            uid = utils_string.random_str(LENGTH_UID)
            try:
                self.validate_unique_entry(uid=uid)
                return uid
            except UserAlreadyExists:
                pass

    def generate_replacing_jwt_token(self, uid: str, prev_token: str, secret: str) -> str:
        """
        Generate JWT token using expiration time from previous token, save it to ldap and return as string
        """
        data = jwt.decode(
            jwt=prev_token,
            algorithms=[UsersHandler.JWT_ALGORITHM],
            options={"verify_signature": False, "verify_exp": True},
        )
        exp_time = datetime.fromtimestamp(
            data.get("exp", ""),
            tz=timezone.utc,
        )
        time_now = datetime.now(tz=timezone.utc)
        if exp_time < time_now:
            raise jwt.exceptions.ExpiredSignatureError
        time_left = exp_time - time_now
        return self.generate_jwt_token(
            uid=uid, mail=data.get("mail"), exp_period_in_min=time_left.seconds // 60, secret=secret
        )

    def verify_jwt_token(self, token: str, secret) -> UserType:  # noqa: ANN001
        """
        Verify user's JWT one-time email token, remove it from LDAP if proper and return related user
        """
        unsafe_uid = jwt.decode(
            jwt=token,
            algorithms=[UsersHandler.JWT_ALGORITHM],
            options={"verify_signature": False, "verify_exp": True},
        ).get("uid", "")
        validate_user_input({"user_id": unsafe_uid})
        if not unsafe_uid:
            raise WrongUserToken
        payload = jwt.decode(
            jwt=token,
            key=secret,
            algorithms=[UsersHandler.JWT_ALGORITHM],
            options={"verify_signature": True, "verify_exp": True},
        )
        uid = payload["uid"]
        user = self.get_user(uid)
        if user.get("email_token") != token:
            raise WrongUserToken
        self.edit_user(uid, email_token="")
        return user

    # noinspection PyUnresolvedReferences
    def generate_changes_list(
        self,
        admin: bool = False,
        change_admin: bool = False,
        registered: bool | None = None,
        mail: str | None = None,
        name: str | None = None,
        email_token: str | None = None,
        new_uid: str | None = None,
    ) -> list:
        """
        Generate a list of changes
        :param admin: if change_admin arg is present changes if user is admin
        :param change_admin: if True allows change admin value
        :param registered: if arg preset changes registered to value
        :param mail: if arg present changes mail to value
        :param name: if arg present changes name to value
        :param email_token: if arg present and not empty changes email_token to value
        :param new_uid: new uid of the user (used when uid changes during the migration to account service)
        """
        changes = []
        if name:
            changes.append((ldap.MOD_REPLACE, LdapAttr.name, [name.encode()]))
        if mail:
            changes.append((ldap.MOD_REPLACE, LdapAttr.mail, [mail.encode()]))
        if change_admin:
            gid = self._get_user_gid(is_admin=admin)
            changes.append((ldap.MOD_REPLACE, LdapAttr.group, [str(gid).encode()]))
        if registered is not None:
            changes.append((ldap.MOD_REPLACE, LdapAttr.registered, [str(registered).encode()]))
        if email_token is not None:
            if email_token == "":
                changes.append((ldap.MOD_DELETE, LdapAttr.email_token, []))
            else:
                changes.append((ldap.MOD_REPLACE, LdapAttr.email_token, [email_token.encode()]))
        if new_uid:
            changes.append((ldap.MOD_REPLACE, LdapAttr.uid, [new_uid.encode()]))
        return changes

    def edit_user(  # noqa: ANN201, PLR0913
        self,
        uid: str,
        name: str | None = None,
        mail: str | None = None,
        admin: bool = False,
        change_admin: bool = False,
        registered: bool | None = None,
        email_token: str | None = None,
        new_uid: str | None = None,
    ):
        """
        Edit user with given id.
        :param uid: user selector
        :param name: if arg present changes name to value
        :param mail: if arg present changes mail to value
        :param admin: if change_admin arg is present changes if user is admin
        :param change_admin: if True allows change admin value
        :param registered: if arg preset changes registered to value
        :param email_token:
        :param new_uid: if user id changes (e.g. during migration to account service)
        :return: True if succeed
        """
        if mail:
            self.validate_unique_entry(mail=mail)
            self.is_email_valid(mail=mail)
        changes = self.generate_changes_list(admin, change_admin, registered, mail, name, email_token, new_uid)
        try:
            self._connection.modify_s(dn=f"cn={ldap.dn.escape_dn_chars(uid)},{self.BASE}", modlist=changes)
        except ldap.LDAPError as ldap_error:
            logger.error(f"Can't update user {uid}")
            raise UserHandlerError(f"Can't update user {uid}") from ldap_error
        return True

    def get_user_from_jwt_header(self, header: str) -> UserType:
        """
        Returns user based on the provided JWT in HTTP header.

        :param header: x-auth-request-access-token, JWT data

        :return UserType: The resolved user.

        :raise UserDoesNotExist: If the requested User does not exist
        :raise TypeError: If preferred_username claim is missing or JWT is invalid
        """
        logger.debug("Attempting to get user from JWT header")
        try:
            decoded_data = jwt.decode(
                jwt=header,
                options={
                    "verify_signature": False,
                    "verify_exp": True,
                },
            )
        except jwt.PyJWTError as err:
            raise TypeError("Problem during JWT decoding") from err

        uid = decoded_data.get("preferred_username")

        if not isinstance(uid, str):
            raise TypeError(f"Expected the uid to be an instance of {str}, got {type(uid)}.")

        return self.get_user(uid)

    def get_user_roles(
        self, uid: str, resource_type: AccessResourceTypes, resource_id: str | None = None
    ) -> list[tuple[str, str]]:
        """
        Fetch a list of roles assigned to a user.
        Returns a list of tuples, where first element is resource_id and
         second element is role assigned to the resource.
        """
        return self._authzed_client.get_user_roles(
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=self._base64_encode(uid),
        )

    def modify_user_roles(  # noqa: ANN201
        self, uid: str, authorization_relationships: list[AuthorizationRelationships]
    ):
        """
        Modify roles of target user
        :param uid: uid of target user example@mail.com
        :param authorization_relationships: list of relationships to create or delete for user
        """
        for relation in authorization_relationships:
            self._authzed_client.change_user_relation(
                resource_type=relation.resource_type,  # type: ignore
                user_id=self._base64_encode(uid),
                resource_id=relation.resource_id,  # type: ignore
                relations=relation.relations,
                operation=relation.operation,
            )

    def would_modify_user_roles_remove_all_workspace_roles(
        self, uid: str, authorization_relationships: list[AuthorizationRelationships]
    ) -> bool:
        """
        Check if modify roles of target user would result in removal of all the Workspace related Roles
        :param uid: uid of target user example@mail.com
        :param authorization_relationships: list of relationships to create or delete for user
        """
        effective_workspace_roles = {
            f"{resource_id}__{role}"
            for (resource_id, role) in self.get_user_roles(uid=uid, resource_type=AccessResourceTypes.WORKSPACE)
        }

        logger.debug(f"Initial User Workspace Roles: {effective_workspace_roles=}")

        for authorization_relationship in authorization_relationships:
            for relation in authorization_relationship.relations:
                if AccessResourceTypes.WORKSPACE.value != authorization_relationship.resource_type:
                    continue

                try:
                    items = [
                        authorization_relationship.resource_id,
                        SpiceDBUserRoles.role_from_relation(authorization_relationship.resource_type, relation),
                    ]
                    role = "__".join(items)  # type: ignore

                    if authorization_relationship.operation in [RoleMutationOperations.DELETE]:
                        effective_workspace_roles.discard(role)
                        logger.debug(f"Would remove Workspace role {role}")
                    elif authorization_relationship.operation in [
                        RoleMutationOperations.CREATE,
                        RoleMutationOperations.TOUCH,
                    ]:
                        effective_workspace_roles.add(role)
                        logger.debug(f"Would add Workspace role {role}")
                except ValueError:
                    logger.debug(
                        f"Skipping relation {relation},"
                        f" as it doesn't make sense for {authorization_relationship.resource_type}"
                    )

        logger.debug(f"Would result in Workspace roles: {effective_workspace_roles=}")
        return len(effective_workspace_roles) == 0

    def check_user_can_manage_permission(
        self, uid: str, authorization_relationships: list[AuthorizationRelationships]
    ) -> bool:
        """
        Check if user has can_manage permission on all resources provided in authorization_relationship list.
        Returns True if user has can_manage permission on all resources, returns False otherwise.
        """
        return all(
            self._authzed_client.check_permission(
                resource_type=relation.resource_type,  # type: ignore
                resource_id=relation.resource_id,  # type: ignore
                subject_type=SpiceDBResourceTypes.USER.value,
                subject_id=self._base64_encode(uid),
                permission=(Permissions.CAN_MANAGE),
            )
            for relation in authorization_relationships
        )

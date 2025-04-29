"""
Common functions for user related operations.
"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from enum import Enum

from geti_spicedb_tools import AccessResourceTypes
from grpc_interfaces.account_service.pb.user_common_pb2 import UserRole, UserRoleOperation
from pydantic import BaseModel, validator

from users_handler.exceptions import SameNewPassword, UserDoesNotExist, UserHandlerError, WeakPassword, WrongOldPassword
from users_handler.users_handler import UsersHandler, UserType

from common.errors import GeneralError
from common.interfaces.payload_error import ResponseException
from common.utils import timed_lru_cache
from config import AUTH_CONFIG


class UserRoles(str, Enum):
    """
    Enum with roles that can be assigned to a user.
    """

    ADMIN = "ADMIN"
    CONTRIBUTOR = "CONTRIBUTOR"


class RoleModel(BaseModel):
    """
    Represents user role model.
    """

    resource_id: str
    resource_type: AccessResourceTypes
    role: UserRoles

    @validator("role")
    @classmethod
    def admin_for_organization(cls, role, values):  # noqa: ANN001
        """Validate admin role for user directory"""
        if values.get("resource_type") == "organization" and role == "CONTRIBUTOR":
            raise ValueError("Contributor can't have access to user directory")
        return role


def update_password(uid: str, new_password: str, old_password: str | None = None) -> bool:
    """Updates user password"""
    users_handler = UsersHandler(**AUTH_CONFIG)

    if old_password:
        try:
            users_handler.validate_password(uid, new_password, old_password)
        except WrongOldPassword as uh_exception:
            raise ResponseException(
                code=GeneralError.WRONG_OLD_PASSWORD.name,
                item=uid,
                msg=str(uh_exception),
            ) from uh_exception
        except SameNewPassword as uh_exception:
            raise ResponseException(
                code=GeneralError.SAME_NEW_PASSWORD.name,
                item=uid,
                msg=str(uh_exception),
            ) from uh_exception
        except UserHandlerError as uh_exception:
            raise ResponseException(
                code=GeneralError.ELEMENT_NOT_FOUND.name,
                item=uid,
                msg=str(uh_exception),
            ) from uh_exception

    try:
        users_handler.check_password_strength(new_password)
    except WeakPassword as uh_exception:
        raise ResponseException(code=GeneralError.WEAK_PASSWORD.name, item=uid, msg=str(uh_exception)) from uh_exception

    try:
        users_handler.change_user_password(uid=uid, new_password=new_password)
        return True
    except UserHandlerError as uh_exception:
        raise ResponseException(code=GeneralError.INVALID_INPUT.name, item=uid, msg=str(uh_exception)) from uh_exception


async def get_user_by_email(mail: str) -> UserType | None:
    """Return user by email"""
    users_handler = UsersHandler(**AUTH_CONFIG)
    users = users_handler.list_users()
    for user in users:
        if user["mail"] == mail:
            return user
    return None


@timed_lru_cache(seconds=5)
def get_user_from_header(header: str) -> UserType:
    """
    Returns user from HTTP request's header.
    Wrapped in timed_lru_cache decorator to reduce LDAP's load.
    """
    users_handler = UsersHandler(**AUTH_CONFIG)
    try:
        return users_handler.get_user_from_jwt_header(header)
    except ValueError as err:
        raise UserDoesNotExist from err


def update_missing_workspace_roles(
    role_ops: list[UserRoleOperation], default_workspace: str
) -> list[UserRoleOperation]:
    """
    Update the list of roles with missing workspace related roles.
    """
    org_admin = False
    workspace_admin = False
    org_contributor = False
    workspace_contributor = False
    operation: str = ""

    for role in role_ops:
        if "organization_admin" in role.role.role:
            org_admin = True
            operation = role.operation
        elif "organization_contributor" in role.role.role:
            org_contributor = True
            operation = role.operation
        elif "workspace_admin" in role.role.role:
            workspace_admin = True
        elif "workspace_contributor" in role.role.role:
            workspace_contributor = True

    if (org_admin and not workspace_admin) or (org_contributor and not workspace_contributor):
        workspace_role = "workspace_admin"
        workspace_operation = operation
        if org_contributor:
            workspace_role = "workspace_contributor"

        role_op = UserRoleOperation(
            role=UserRole(role=workspace_role, resource_type="workspace", resource_id=default_workspace),
            operation=workspace_operation,
        )

        role_ops.append(role_op)

    return role_ops

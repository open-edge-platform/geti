# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import base64
import functools
import logging
from collections.abc import Callable, Mapping
from http import HTTPStatus

import grpc
from fastapi.responses import PlainTextResponse
from grpc_interfaces.account_service.client import AccountServiceClient
from grpc_interfaces.account_service.pb.organization_pb2 import FindOrganizationRequest, ListOrganizationsResponse
from grpc_interfaces.account_service.pb.user_common_pb2 import (
    UserData,
    UserInvitationRequest,
    UserRole,
    UserRoleOperation,
)
from grpc_interfaces.account_service.pb.user_pb2 import (
    FindUserRequest,
    ListUsersResponse,
    UserIdRequest,
    UserInvitationResponse,
    UserRolesRequest,
)
from grpc_interfaces.account_service.pb.user_status_pb2 import UserStatusRequest, UserStatusResponse

from users_handler.subject_pb2 import IDTokenSubject

logger = logging.getLogger(__name__)


def get_sub_from_jwt_token(uid: str) -> str:
    """
    Generate the JWT subject string (sub) based on a given user ID (uid).

    :param uid: The user ID used to construct the IDTokenSubject object.

    :return: A base64 encoded serialized JWT subject string.
    """
    id_token_subject = IDTokenSubject()
    id_token_subject.user_id = f"cn={uid},dc=example,dc=org"
    id_token_subject.conn_id = "regular_users"

    sub: str = base64.b64encode(id_token_subject.SerializeToString()).decode(encoding="utf8").rstrip("=")
    return sub


class AccountServiceError(Exception):
    def __init__(self, message: str, grpc_status_code: grpc.StatusCode):
        super().__init__(message)
        self.grpc_status_code = grpc_status_code


def _rpc_error_as_account_service_error(func: Callable):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except grpc.RpcError as rpc_error:
            logger.exception("Account Service returned error")
            raise AccountServiceError(rpc_error.details(), rpc_error.code())

    return wrapper


class AccountServiceConnection:
    def __init__(self) -> None:
        self.client = AccountServiceClient(metadata_getter=lambda: ())

    @_rpc_error_as_account_service_error
    def create_user(self, organization_id: str, create_user: dict) -> UserData:
        user_data = UserData(**create_user, organization_id=organization_id)
        created_user: UserData = self.client.user_stub.create(user_data)
        logger.info(f"User created with id: {created_user.id}")
        logger.debug(f"Received response from Account Service for user creation: {created_user}")
        return created_user

    def update_user_external_id(self, uid: str, organization_id: str, external_id: str, find_user: Mapping) -> str:
        user_data = UserData(**find_user, id=uid, organization_id=organization_id, external_id=external_id)
        modify_response = self.client.user_stub.modify(user_data)
        logger.info(f"Updated external_id {external_id} for user with id: {modify_response.id}")
        logger.debug(f"Received response from Account Service when user is updated with external_id: {modify_response}")
        return modify_response.external_id

    def set_user_roles(self, uid: str, organization_id: str, roles: list):  # noqa: ANN201
        role_ops: list[UserRoleOperation] = []
        for role in roles:
            user_role = UserRole(role=role["role"], resource_type=role["resourceType"], resource_id=role["resourceId"])
            role_op = UserRoleOperation(role=user_role, operation="CREATE")
            role_ops.append(role_op)
        user_roles = UserRolesRequest(roles=role_ops, user_id=uid, organization_id=organization_id)
        try:
            self.set_roles(user_roles)
        except AccountServiceError as error:
            if error.grpc_status_code == grpc.StatusCode.ALREADY_EXISTS:
                return PlainTextResponse(
                    "User already exists",
                    status_code=HTTPStatus.CONFLICT,
                )
            raise

    @_rpc_error_as_account_service_error
    def set_roles(self, user_roles: UserRolesRequest) -> None:
        self.client.user_stub.set_roles(user_roles)

    @_rpc_error_as_account_service_error
    def invite_user(self, invitation_request: UserInvitationRequest) -> UserInvitationResponse:
        return self.client.user_stub.send_invitation(invitation_request)

    @_rpc_error_as_account_service_error
    def delete_user(self, request: UserIdRequest) -> None:
        self.client.user_stub.delete(request)

    @_rpc_error_as_account_service_error
    def get_organization(self, find_request: FindOrganizationRequest) -> ListOrganizationsResponse:
        return self.client.organization_stub.find(find_request)

    @_rpc_error_as_account_service_error
    def get_users(self, find_request: FindUserRequest) -> ListUsersResponse:
        return self.client.user_stub.find(find_request)

    @_rpc_error_as_account_service_error
    def change_user_status(self, status_request: UserStatusRequest) -> UserStatusResponse:
        return self.client.user_status_stub.change(status_request)

    @_rpc_error_as_account_service_error
    def get_default_workspace_id(self, organization_id: str) -> str:
        return self.client.get_default_workspace_id(organization_id)

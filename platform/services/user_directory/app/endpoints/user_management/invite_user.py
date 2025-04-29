# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import base64
import json
import logging
import os
from http import HTTPStatus
from typing import Annotated

from fastapi import Header
from fastapi.responses import PlainTextResponse
from grpc import StatusCode
from grpc_interfaces.account_service.pb.user_common_pb2 import UserRole, UserRoleOperation
from grpc_interfaces.account_service.pb.user_pb2 import UserIdRequest, UserRolesRequest
from opentelemetry import trace  # type: ignore[attr-defined]
from pydantic.main import BaseModel
from service_connection.k8s_client.config_maps import get_config_map
from service_connection.k8s_client.secrets import get_secrets
from service_connection.kafka import send_message
from service_connection.smtp_client import EmailTemplates, SMTPClient

from endpoints.user_management.router import organization_router
from users_handler.exceptions import UserAlreadyExists
from users_handler.subject_pb2 import IDTokenSubject

from common.account_service import AccountServiceConnection, AccountServiceError
from common.endpoint_logger import EndpointLogger
from common.ldap import OpenLDAPConnection, UsersHandlerUser
from common.users import update_missing_workspace_roles
from config import JWT_SECRET

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# TODO: change when onboarding-service will be deployed on on-prem platform
INVITATION_PHRASE = "QFNDQWRtaW4="


class InviteUserData(BaseModel):
    email: str
    organizationId: str  # noqa: N815
    firstName: str | None = None  # noqa: N815
    secondName: str | None = None  # noqa: N815


class UserRoleREST(BaseModel):
    role: str
    resourceType: str  # noqa: N815
    resourceId: str  # noqa: N815


class UserRoleOperationREST(BaseModel):
    role: UserRoleREST
    operation: str


class UserInvitationRequestREST(BaseModel):
    user: InviteUserData
    roles: list[UserRoleOperationREST]


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


@organization_router.post(
    "/{organization_id}/invitations",
    status_code=HTTPStatus.CREATED,
)
@organization_router.post(
    "/{organization_id}/users/invitations",
    status_code=HTTPStatus.CREATED,
)
@EndpointLogger.extended_logging
def invite_user_endpoint(  # noqa: ANN201
    body: UserInvitationRequestREST, organization_id: str, host: Annotated[str | None, Header()] = None
):
    """
    Create new user in openldap and account service

    :param body: User data passed with POST request
    :param organization_id: id of user organization
    :param host: 'Host' header value in request
    """
    server_address = host if host else "intel.com"
    find_user = {
        "first_name": body.user.firstName,
        "second_name": body.user.secondName,
        "email": body.user.email,
        "status": "RGS",
    }
    create_user = dict(**find_user, external_id="default")
    account_service = AccountServiceConnection()
    try:
        created_user = account_service.create_user(organization_id=organization_id, create_user=create_user)
    except AccountServiceError as error:
        if error.grpc_status_code == StatusCode.ALREADY_EXISTS:
            return PlainTextResponse(
                "User already exists",
                status_code=HTTPStatus.CONFLICT,
            )
        if error.grpc_status_code == StatusCode.INVALID_ARGUMENT:
            return PlainTextResponse(
                str(error),
                status_code=HTTPStatus.BAD_REQUEST,
            )
        raise

    try:
        open_ldap = OpenLDAPConnection()
        initial_user = UsersHandlerUser(
            email=body.user.email, first_name=body.user.firstName, password=INVITATION_PHRASE
        )
        user_created_successfully = open_ldap.create_initial_user(uid=created_user.id, data=initial_user)
        if not user_created_successfully:
            raise UserAlreadyExists
    except Exception:
        account_service.delete_user(UserIdRequest(user_id=created_user.id, organization_id=organization_id))
        raise

    try:
        sub = get_sub_from_jwt_token(uid=created_user.id)

        role_ops: list[UserRoleOperation] = []
        for role_op in body.roles:
            user_role = UserRole(
                role=role_op.role.role, resource_type=role_op.role.resourceType, resource_id=role_op.role.resourceId
            )
            role_operation = UserRoleOperation(role=user_role, operation=role_op.operation)
            role_ops.append(role_operation)

        # extend a list of roles with workspace related roles only if manage_users feature flag is enabled
        if os.environ.get("FEATURE_FLAG_MANAGE_USERS", "false") == "true":
            default_workspace = account_service.get_default_workspace_id(organization_id)
            role_ops = update_missing_workspace_roles(role_ops=role_ops, default_workspace=default_workspace)

        roles_request = UserRolesRequest(user_id=created_user.id, organization_id=organization_id, roles=role_ops)

        account_service.set_roles(roles_request)
        account_service.update_user_external_id(
            uid=created_user.id, organization_id=organization_id, external_id=sub, find_user=find_user
        )

        exp = int(
            get_config_map(name="impt-configuration", field_list=["invite-user-expiration"])["invite-user-expiration"]
        )
        secret = get_secrets(
            name=JWT_SECRET,
            secrets_list=["key"],
        )["key"]
        invitation_link = (
            f"https://{server_address}/registration/sign-up?token="
            f"{open_ldap.users_handler.generate_jwt_token(uid=created_user.id, exp_period_in_min=exp, secret=secret)}"
        )

        topic, message = SMTPClient._render_template(
            EmailTemplates.INVITATION_MAIL.value, {"invitationLink": invitation_link}
        )

        email_send_request_message = {
            "subject": topic,
            "to": body.user.email,
            "from_address": os.environ.get("INVITATION_FROM_ADDRESS", "no-reply@geti.intel.com"),
            "from_name": os.environ.get("INVITATION_FROM_NAME", "Intel Geti"),
            "content": "",
            "html_content": message,
        }
        send_message(json.dumps(email_send_request_message))

    except Exception:
        account_service.delete_user(UserIdRequest(user_id=created_user.id, organization_id=organization_id))
        open_ldap.delete_user(created_user.id)
        raise
    return None

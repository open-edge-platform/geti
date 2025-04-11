# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from http import HTTPStatus

from fastapi.responses import PlainTextResponse
from grpc import StatusCode
from grpc_interfaces.account_service.pb.user_common_pb2 import UserData, UserRole
from grpc_interfaces.account_service.pb.user_pb2 import UserIdRequest
from opentelemetry import trace  # type: ignore[attr-defined]
from pydantic.main import BaseModel

from endpoints.user_management.router import organization_router

from common.account_service import AccountServiceConnection, AccountServiceError, get_sub_from_jwt_token
from common.endpoint_logger import EndpointLogger
from common.ldap import OpenLDAPConnection, UsersHandlerUser

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class CreateUserBody(BaseModel):
    email: str
    firstName: str  # noqa: N815
    secondName: str  # noqa: N815
    password: str
    roles: list


class UserRoleResponse(BaseModel):
    role: str
    resourceType: str  # noqa: N815
    resourceId: str  # noqa: N815

    @classmethod
    def from_protobuf(cls, proto: UserRole):
        return cls(role=proto.role, resourceType=proto.resource_type, resourceId=proto.resource_id)


class CreatedUserResponse(BaseModel):
    id: str
    firstName: str  # noqa: N815
    secondName: str  # noqa: N815
    email: str
    externalId: str  # noqa: N815
    country: str
    status: str
    organizationId: str  # noqa: N815
    organizationStatus: str  # noqa: N815
    roles: list
    lastSuccessfulLogin: str | None  # noqa: N815
    createdAt: str | None  # noqa: N815
    createdBy: str  # noqa: N815
    modifiedAt: str | None  # noqa: N815
    modifiedBy: str  # noqa: N815
    telemetryConsent: str  # noqa: N815
    telemetryConsentAt: str | None  # noqa: N815
    userConsent: str  # noqa: N815
    userConsentAt: str | None  # noqa: N815
    presignedUrl: str  # noqa: N815

    @classmethod
    def from_protobuf(cls, proto: UserData):
        response = cls(
            id=proto.id,
            firstName=proto.first_name,
            secondName=proto.second_name,
            email=proto.email,
            externalId=proto.external_id,
            country=proto.country,
            status=proto.status,
            organizationId=proto.organization_id,
            organizationStatus=proto.organization_status,
            lastSuccessfulLogin=(
                proto.last_successful_login.ToJsonString() if str(proto.last_successful_login) != "" else None
            ),
            createdAt=proto.created_at.ToJsonString() if str(proto.created_at) != "" else None,
            createdBy=proto.created_by,
            modifiedAt=proto.modified_at.ToJsonString() if str(proto.modified_at) != "" else None,
            modifiedBy=proto.modified_by,
            telemetryConsent=proto.telemetry_consent,
            telemetryConsentAt=(
                proto.telemetry_consent_at.ToJsonString() if str(proto.telemetry_consent_at) != "" else None
            ),
            userConsent=proto.user_consent,
            userConsentAt=proto.user_consent_at.ToJsonString() if str(proto.user_consent_at) != "" else None,
            presignedUrl=proto.presigned_url,
            roles=[],
        )
        for role in proto.roles:
            response.roles.append(UserRoleResponse.from_protobuf(role))
        return response


@organization_router.post(
    "/{organization_id}/users/create",
    status_code=HTTPStatus.CREATED,
)
@EndpointLogger.extended_logging
def create_organization_user(body: CreateUserBody, organization_id: str):  # noqa: ANN201
    """
    Create new user in openldap and account service

    :param body: User data passed with POST request
    :param organization_id: id of user organization
    """
    find_user = {"first_name": body.firstName, "second_name": body.secondName, "email": body.email, "status": "ACT"}
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
        if error.grpc_status_code in (StatusCode.INVALID_ARGUMENT, StatusCode.FAILED_PRECONDITION):
            return PlainTextResponse(
                str(error),
                status_code=HTTPStatus.BAD_REQUEST,
            )
        raise

    try:
        open_ldap = OpenLDAPConnection()
        initial_user = UsersHandlerUser(
            email=body.email, first_name=body.firstName, password=body.password, roles=body.roles
        )
        if not open_ldap.create_initial_user(uid=created_user.id, data=initial_user):
            account_service.delete_user(UserIdRequest(user_id=created_user.id, organization_id=organization_id))
            return PlainTextResponse(
                status_code=HTTPStatus.BAD_REQUEST,
            )
    except Exception:
        account_service.delete_user(UserIdRequest(user_id=created_user.id, organization_id=organization_id))
        raise

    try:
        sub = get_sub_from_jwt_token(uid=created_user.id)
        account_service.set_user_roles(uid=created_user.id, organization_id=organization_id, roles=body.roles)
        account_service.update_user_external_id(
            uid=created_user.id, organization_id=organization_id, external_id=sub, find_user=find_user
        )
    except Exception:
        account_service.delete_user(UserIdRequest(user_id=created_user.id, organization_id=organization_id))
        open_ldap.delete_user(created_user.id)
        raise

    created_user.external_id = sub
    response = CreatedUserResponse.from_protobuf(created_user)
    response.roles = body.roles
    return response

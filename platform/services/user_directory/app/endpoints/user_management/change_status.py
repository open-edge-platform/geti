# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from http import HTTPStatus

from fastapi.responses import PlainTextResponse
from grpc import StatusCode
from grpc_interfaces.account_service.pb.user_status_pb2 import UserStatusRequest
from opentelemetry import trace  # type: ignore[attr-defined]
from pydantic.main import BaseModel

from endpoints.user_management.router import organization_router
from users_handler.exceptions import UserDoesNotExist

from common.account_service import AccountServiceConnection, AccountServiceError
from common.endpoint_logger import EndpointLogger
from common.ldap import OpenLDAPConnection

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class StatusREST(BaseModel):
    organizationId: str  # noqa: N815
    status: str


@organization_router.put(
    "/{organization_id}/users/{user_id}/statuses",
    responses={
        HTTPStatus.OK.value: {"description": HTTPStatus.OK.description},
        HTTPStatus.BAD_REQUEST.value: {"description": HTTPStatus.BAD_REQUEST.description},
    },
)
@EndpointLogger.extended_logging
def change_status_endpoint(body: StatusREST, organization_id: str, user_id: str):  # noqa: ANN201
    """
    Changes a status of a user.

    :param body: Status data passed in a request
    :param organization_id: id of user organization
    :param user_id: id of a user
    """
    account_service = AccountServiceConnection()

    try:
        user_status: UserStatusRequest = UserStatusRequest(
            status=body.status, user_id=user_id, organization_id=organization_id
        )

        _ = account_service.change_user_status(user_status)
    except AccountServiceError as error:
        if error.grpc_status_code == StatusCode.INVALID_ARGUMENT:
            return PlainTextResponse(
                str(error),
                status_code=HTTPStatus.BAD_REQUEST,
            )
        if error.grpc_status_code == StatusCode.FAILED_PRECONDITION:
            return PlainTextResponse(
                str(error),
                status_code=HTTPStatus.CONFLICT,
            )
        raise

    # delete user from LDAP if user gets the DEL status
    if body.status == "DEL":
        try:
            open_ldap = OpenLDAPConnection()
            _ = open_ldap.delete_user(user_id)
        except UserDoesNotExist:
            logger.debug("User doesn't exist in LDAP")
        except Exception:
            raise

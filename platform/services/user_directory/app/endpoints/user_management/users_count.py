# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
from http import HTTPStatus

from grpc_interfaces.account_service.pb.organization_pb2 import FindOrganizationRequest, ListOrganizationsResponse
from grpc_interfaces.account_service.pb.user_pb2 import FindUserRequest, ListUsersResponse

from endpoints.user_management.router import users_router

from common.account_service import AccountServiceConnection

logger = logging.getLogger(__name__)


def _get_default_organization_id(account_service: AccountServiceConnection) -> str:
    find_request: FindOrganizationRequest = FindOrganizationRequest()
    find_response: ListOrganizationsResponse = account_service.get_organization(find_request=find_request)
    if find_response.organizations and len(find_response.organizations) > 0:
        return find_response.organizations[0].id

    raise RuntimeError("Cannot find default organization.")


def _get_users_count(account_service: AccountServiceConnection, organization_id: str) -> str:
    find_user = FindUserRequest(organization_id=organization_id)
    find_response: ListUsersResponse = account_service.get_users(find_user)

    return str(find_response.total_matched_count)


@users_router.get(
    "/count",
    responses={
        HTTPStatus.OK.value: {"description": HTTPStatus.OK.description},
        HTTPStatus.BAD_REQUEST.value: {"description": HTTPStatus.BAD_REQUEST.description},
    },
    response_model=str,
)
def users_count():  # noqa: ANN201
    """
    Returns a number of active/registered users defined in the platform
    """
    account_service = AccountServiceConnection()

    def_org_id = _get_default_organization_id(account_service=account_service)
    return _get_users_count(account_service=account_service, organization_id=def_org_id)

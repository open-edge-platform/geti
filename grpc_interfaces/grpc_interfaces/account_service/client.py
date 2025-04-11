# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

import json
import logging
import os
from collections.abc import Callable, Mapping
from typing import Any

import grpc
from google.protobuf.json_format import MessageToDict

from .enums import UserStatus
from .pb.organization_pb2 import FindOrganizationRequest, ListOrganizationsResponse, OrganizationData
from .pb.organization_pb2_grpc import OrganizationStub
from .pb.organization_status_pb2 import OrganizationStatusRequest, OrganizationStatusResponse
from .pb.organization_status_pb2_grpc import OrganizationStatusStub
from .pb.user_common_pb2 import UserData
from .pb.user_pb2 import FindUserRequest, ListUsersResponse, UserIdRequest
from .pb.user_pb2_grpc import UserStub
from .pb.user_status_pb2 import UserStatusRequest, UserStatusResponse
from .pb.user_status_pb2_grpc import UserStatusStub
from .pb.workspace_pb2 import FindWorkspaceRequest, ListWorkspacesResponse, WorkspaceData
from .pb.workspace_pb2_grpc import WorkspaceStub
from .responses.user_by_id_response import UserByIDResponse

logger = logging.getLogger(__name__)


GRPC_MAX_MESSAGE_SIZE = int(os.environ.get("GRPC_MAX_MESSAGE_SIZE", 128 * 1024**2))  # noqa: PLW1508
FIND_USER: Mapping[Any, Any] = {
    "first_name": "admin",
    "second_name": "admin",
    "email": os.getenv("INITIAL_USER_EMAIL", ""),
    "country": "POL",
    "status": "ACT",
}

DEFAULT_ORGANIZATION: Mapping[Any, Any] = {
    "name": "default",
    "country": "POL",
    "type": "B2C",
    "cell_id": "default",
    "status": "ACT",
}
DEFAULT_WORKSPACE_NAME = "Default workspace"
CREATE_USER = dict(**FIND_USER, external_id="default")


class AccountServiceClient:
    """
    Provides gRPC connection to Account Service.

    :param metadata_getter: Lazy-evaluated function that returns the metadata to include
        in the gRPC request. It is typically used to propagate the session context.
        If the function returns None, then no metadata is propagated.
    """

    RETRY_MAX_ATTEMPTS = 5
    RETRY_INITIAL_BACKOFF = 1
    RETRY_MAX_BACKOFF = 4
    RETRY_BACKOFF_MULTIPLIER = 2

    def __init__(self, metadata_getter: Callable[[], tuple[tuple[str, str], ...] | None]) -> None:
        self.metadata_getter = metadata_getter
        self.host = os.environ.get("ACCOUNT_SERVICE_HOST", "impt-account-service")
        self.port = int(os.environ.get("ACCOUNT_SERVICE_PORT", 5001))  # noqa: PLW1508
        self.channel = grpc.insecure_channel(
            f"{self.host}:{self.port}",
            options=[
                (
                    "grpc.service_config",
                    json.dumps(
                        {
                            "methodConfig": [
                                {
                                    "name": [{}],  # to match all RPCs from the account service
                                    "retryPolicy": {
                                        "maxAttempts": self.RETRY_MAX_ATTEMPTS,
                                        "initialBackoff": f"{self.RETRY_INITIAL_BACKOFF}s",
                                        "maxBackoff": f"{self.RETRY_MAX_BACKOFF}s",
                                        "backoffMultiplier": self.RETRY_BACKOFF_MULTIPLIER,
                                        "retryableStatusCodes": ["UNAVAILABLE"],
                                    },
                                }
                            ]
                        }
                    ),
                ),
                ("grpc.max_send_message_length", GRPC_MAX_MESSAGE_SIZE),
                ("grpc.max_receive_message_length", GRPC_MAX_MESSAGE_SIZE),
            ],
        )
        self.organization_stub = OrganizationStub(self.channel)
        self.organization_status_stub = OrganizationStatusStub(self.channel)
        self.workspace_stub = WorkspaceStub(self.channel)
        self.user_stub = UserStub(self.channel)
        self.user_status_stub = UserStatusStub(self.channel)

    @staticmethod
    def _convert_response_status_to_user_status(received_response: UserStatusResponse) -> UserStatus:
        return UserStatus(received_response.status)

    def create_default_organization(self) -> str:
        org_data = OrganizationData(**DEFAULT_ORGANIZATION)
        find_org = FindOrganizationRequest(**DEFAULT_ORGANIZATION)
        find_response: ListOrganizationsResponse = self.organization_stub.find(find_org)
        logger.debug(f"Received response from Account Service when searching for organization: {find_response}")
        if find_response.total_matched_count >= 1:
            logger.info("Organization already exist.")
            return find_response.organizations[0].id
        create_response = self.organization_stub.create(org_data)
        logger.debug(f"Received response from Account Service for organization creation: {create_response}")
        logger.info(f"Organization created with id: {create_response.id}")
        return create_response.id

    def create_default_workspace(self, organization_id: str) -> str:
        workspace_data = WorkspaceData(name=DEFAULT_WORKSPACE_NAME, organization_id=organization_id)
        find_work = FindWorkspaceRequest(name=DEFAULT_WORKSPACE_NAME, organization_id=organization_id)
        find_response: ListWorkspacesResponse = self.workspace_stub.find(find_work)
        logger.debug(f"Received response from Account Service when searching for workspace: {find_response}")
        if find_response.total_matched_count >= 1:
            logger.info("Workspace already exist.")
            return find_response.workspaces[0].id
        create_response = self.workspace_stub.create(workspace_data)
        logger.debug(f"Received response from Account Service for workspace creation: {create_response}")
        logger.info(f"Workspace created with id: {create_response.id}")
        return create_response.id

    def create_initial_user(self, organization_id: str) -> str:
        user_data = UserData(**CREATE_USER, organization_id=organization_id)
        find_user = FindUserRequest(**FIND_USER, organization_id=organization_id)
        find_response: ListUsersResponse = self.user_stub.find(find_user)
        logger.debug(f"Received response from Account Service when searching for user: {find_response}")
        if find_response.total_matched_count >= 1:
            logger.info("User already exist.")
            return find_response.users[0].id
        create_response = self.user_stub.create(user_data)
        logger.info(f"User created with id: {create_response.id}")
        logger.debug(f"Received response from Account Service for user creation: {create_response}")
        return create_response.id

    def update_user_external_id(self, uid: str, organization_id: str, external_id: str) -> str:
        user_data = UserData(**FIND_USER, id=uid, organization_id=organization_id, external_id=external_id)
        modify_response = self.user_stub.modify(user_data)
        logger.info(f"Updated external_id {external_id} for user with id: {modify_response.id}")
        logger.debug(f"Received response from Account Service when user is updated with external_id: {modify_response}")
        return modify_response.external_id

    def get_all_organizations(self) -> list[dict]:
        find_org = FindOrganizationRequest()
        find_response: ListOrganizationsResponse = self.organization_stub.find(find_org)
        message = MessageToDict(find_response)
        return message.get("organizations", [])

    def get_active_intel_organizations_ids(self) -> list[str]:
        find_request = FindOrganizationRequest(status="ACT")
        find_response: ListOrganizationsResponse = self.organization_stub.find(find_request)
        return [
            org.id
            for org in find_response.organizations
            if any(admin.email.endswith("@intel.com") for admin in org.admins)
        ]

    def get_organizations_users(self, find_user_request: FindUserRequest) -> list[dict]:
        find_response: ListUsersResponse = self.user_stub.find(find_user_request)
        message = MessageToDict(find_response)
        return message.get("users", [])

    def get_default_workspace_id(self, organization_id: str) -> str:
        request = FindWorkspaceRequest(organization_id=organization_id)
        workspaces_response: ListWorkspacesResponse = self.workspace_stub.find(request)
        logger.debug(
            f"Received response from Account Service when searching for organization {organization_id} "
            f"default workspace: {workspaces_response}"
        )
        # TODO currently there's ony one workspace, in the future there might be adjustments required
        return workspaces_response.workspaces[0].id

    def change_user_status(self, user_status_request: UserStatusRequest) -> UserStatus:
        change_user_status = UserStatusRequest(
            status=user_status_request.status,
            user_id=user_status_request.user_id,
            organization_id=user_status_request.organization_id,
            created_by=user_status_request.created_by,
        )
        change_response: UserStatusResponse = self.user_status_stub.change(change_user_status)
        return self._convert_response_status_to_user_status(received_response=change_response)

    def change_organization_status(
        self, organization_status_request: OrganizationStatusRequest
    ) -> OrganizationStatusResponse:
        return self.organization_status_stub.change(organization_status_request)

    def get_user_by_id(self, user_id_request: UserIdRequest) -> UserByIDResponse:
        get_user_by_id = UserIdRequest(user_id=user_id_request.user_id, organization_id=user_id_request.organization_id)
        get_by_id_response = self.user_stub.get_by_id(get_user_by_id)
        return UserByIDResponse.from_protobuf(get_by_id_response)

    def close(self) -> None:
        """Close the GRPC channel."""
        logger.info(f"Closing account service GRPC channel at address {self.host}:{self.port}.")
        self.channel.close()

    def __enter__(self) -> "AccountServiceClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        self.close()

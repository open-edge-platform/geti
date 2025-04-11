# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from google.protobuf.empty_pb2 import Empty
from grpc import RpcError, StatusCode
from grpc_interfaces.account_service.client import AccountServiceClient
from grpc_interfaces.account_service.pb.organization_pb2 import OrganizationData, OrganizationIdRequest
from grpc_interfaces.account_service.pb.user_common_pb2 import UserData
from grpc_interfaces.account_service.pb.user_pb2 import FindUserRequest, UserProfileData, UserRolesRequest
from grpc_interfaces.account_service.pb.workspace_pb2 import FindWorkspaceRequest, ListWorkspacesResponse, WorkspaceData

from geti_logger_tools.logger_config import initialize_logger
from models.organization import Organization, OrganizationRepoInterface
from models.user import User, UserRepoInterface
from models.workspace import WorkspaceRepoInterface

logger = initialize_logger(__name__)


class WorkspaceRepo(WorkspaceRepoInterface):
    def __init__(self, client: AccountServiceClient) -> None:
        self.acc_svc_client = client

    async def create(self, organization: OrganizationData) -> WorkspaceData:
        workspace = WorkspaceData(organization_id=organization.id, name=organization.name)
        return self.acc_svc_client.workspace_stub.create(workspace)

    async def get_by_organization_id(self, organization_id: str) -> WorkspaceData:
        request = FindWorkspaceRequest(organization_id=organization_id)
        workspaces_response: ListWorkspacesResponse = self.acc_svc_client.workspace_stub.find(request)
        # TODO currently there's ony one workspace, in the future there might be adjustments required
        return workspaces_response.workspaces[0]


class OrganizationRepo(OrganizationRepoInterface):
    """
    Repo class for getting/modifying Organizations in Account Service.
    """

    def __init__(self, client: AccountServiceClient) -> None:
        self.acc_svc_client = client

    async def get(self, id_: str) -> Organization | None:
        try:
            org_data = self.acc_svc_client.organization_stub.get_by_id(OrganizationIdRequest(id=id_))
        except RpcError as e:
            if e.code() == StatusCode.NOT_FOUND:
                logger.info(f"Organization {id_} not found")
                return None
            logger.exception(f"Failed to get organization {id_}")
            raise

        return Organization(id_=org_data.id, status=org_data.status, cell_id=org_data.cell_id, name=org_data.name)

    async def update(self, organization: Organization, modified_by: str) -> None:
        org_data = self.acc_svc_client.organization_stub.get_by_id(OrganizationIdRequest(id=organization.id_))
        org_data = OrganizationData(
            id=org_data.id,
            name=org_data.name,
            country=org_data.country,
            location=org_data.location,
            cell_id=org_data.cell_id,
            status=organization.status,
            created_at=org_data.created_at,
            created_by=org_data.created_by,
            modified_at=org_data.modified_at,
            modified_by=modified_by,
            request_access_reason=org_data.request_access_reason,
        )
        self.acc_svc_client.organization_stub.modify(org_data)

    async def create(
        self, organization_name: str, status: str = "ACT", request_access_reason: str = ""
    ) -> OrganizationData:
        organization_data = OrganizationData(
            name=organization_name, status=status, request_access_reason=request_access_reason
        )
        try:
            organization = self.acc_svc_client.organization_stub.create(organization_data)
        except RpcError:
            logger.info(f"Failed to create organization {organization_data}")
            raise
        return organization


class UserRepo(UserRepoInterface):
    """
    Repo class for getting/modifying Users in Account Service.
    """

    def __init__(self, client: AccountServiceClient) -> None:
        self.acc_svc_client = client

    async def get_user_by_email(self, email: str, organization_id: str) -> User | None:
        try:
            user_data_list = self.acc_svc_client.user_stub.find(
                FindUserRequest(email=email, organization_id=organization_id)
            )
            user_data = next(user for user in user_data_list.users if user.email.lower() == email.lower())
            logger.debug(f"Find user {email} response: {user_data}")
        except StopIteration:
            logger.info(f"User {email} not found in organization {organization_id}")
            return None
        except RpcError:
            logger.exception(f"Failed to get user {email} in organization {organization_id}")
            raise
        return User(
            id_=user_data.id,
            first_name=user_data.first_name,
            second_name=user_data.second_name,
            status=user_data.status,
            email=user_data.email,
            organization_id=user_data.organization_id,
            external_id=user_data.external_id,
        )

    async def get_user_profile(self, token: str) -> UserProfileData | None:
        try:
            user_data = self.acc_svc_client.user_stub.get_user_profile(
                metadata=(("x-auth-request-access-token", token),), request=Empty()
            )
            logger.debug(f"Find user response: {user_data}")
        except RpcError as e:
            if e.code() == StatusCode.NOT_FOUND:
                logger.info("User not found")
                return None
            logger.exception(f"Failed to get user profile from {token}")
            raise
        return user_data

    async def update(self, user: User, modified_by: str) -> None:
        """
        Update user in Account Service.
        """
        try:
            user_data_list = self.acc_svc_client.user_stub.find(
                FindUserRequest(email=user.email, organization_id=user.organization_id)
            )
            user_data = next(u for u in user_data_list.users if u.email == user.email)
        except StopIteration:
            raise ValueError(f"User {user.email} not found in organization {user.organization_id}")
        user_data.first_name = user.first_name
        user_data.second_name = user.second_name
        user_data.status = user.status
        user_data.organization_id = user.organization_id
        user_data.modified_by = modified_by
        user_data.telemetry_consent = user.telemetry_consent
        user_data.user_consent = user.user_consent
        user_data.external_id = user.external_id
        self.acc_svc_client.user_stub.modify(user_data)

    async def create(self, user_data: UserData) -> UserData:
        """
        Create user in Account Service.
        """
        try:
            user = self.acc_svc_client.user_stub.create(user_data)
        except RpcError:
            logger.exception(f"Failed to create user {user_data}")
            raise
        return user

    async def set_roles(self, user_id: str, organization_id: str, roles: list) -> None:
        """
        Set roles for created user
        """
        try:
            req = UserRolesRequest(user_id=user_id, organization_id=organization_id, roles=roles)
            self.acc_svc_client.user_stub.set_roles(req)
        except RpcError:
            logger.exception(f"Failed to set roles for user {user_id}")
            raise

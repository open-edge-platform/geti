# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from geti_logger_tools.logger_config import initialize_logger
from geti_spicedb_tools import SpiceDB
from grpc_interfaces.account_service.pb.organization_pb2 import FindOrganizationRequest, ListOrganizationsResponse
from grpc_interfaces.account_service.pb.workspace_pb2 import FindWorkspaceRequest, ListWorkspacesResponse

from account_service_client import AccountServiceConnection

logger = initialize_logger(__name__)


def main() -> None:
    """
    Main function that will:
        - get all organizations
        - get all workspaces connected to those organizations
        - add missing spicedb parent_organization for workspaces connected to organizations
    """
    acc_svc = AccountServiceConnection()
    find_organization = FindOrganizationRequest()
    find_organization_response: ListOrganizationsResponse = acc_svc.client.organization_stub.find(find_organization)
    spicedb_client = SpiceDB()
    for organization in find_organization_response.organizations:
        find_workspace = FindWorkspaceRequest(organization_id=organization.id)
        find_workspace_response: ListWorkspacesResponse = acc_svc.client.workspace_stub.find(find_workspace)
        for workspace in find_workspace_response.workspaces:
            spicedb_client.link_organization_to_workspace_in_spicedb(
                workspace_id=workspace.id, organization_id=organization.id
            )
            logger.info(f"Workspace {workspace.id} linked with org {organization.id}")


if __name__ == "__main__":
    main()

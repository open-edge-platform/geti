"""Tests the account_service_initial_user.create_initial_user module."""

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

from unittest.mock import Mock

import pytest
from google.protobuf.json_format import ParseDict

from grpc_interfaces.account_service.client import AccountServiceClient, UserByIDResponse
from grpc_interfaces.account_service.pb.organization_pb2 import ListOrganizationsResponse, OrganizationDataWithAdmins
from grpc_interfaces.account_service.pb.user_common_pb2 import UserData
from grpc_interfaces.account_service.pb.user_pb2 import FindUserRequest, ListUsersResponse, UserIdRequest
from grpc_interfaces.account_service.pb.user_status_pb2 import UserStatusRequest, UserStatusResponse


@pytest.fixture
def mock_account_service_client():
    client = AccountServiceClient(metadata_getter=lambda: (("key", "value"),))
    client.organization_stub = Mock()
    client.workspace_stub = Mock()
    client.user_stub = Mock()
    client.user_status_stub = Mock()
    yield client


def test_create_default_organization_that_exist(mock_account_service_client):
    mock_account_service_client.organization_stub.find.total_matched_count = 1
    mock_account_service_client.organization_stub.find.return_value = Mock(
        total_matched_count=1, organizations=[Mock(id="o123456")]
    )
    mock_account_service_client.organization_stub.create.return_value = Mock(id="o098765")

    org_id = mock_account_service_client.create_default_organization()

    assert org_id == "o123456"
    assert mock_account_service_client.organization_stub.find.call_count == 1
    assert mock_account_service_client.organization_stub.create.call_count == 0


def test_create_default_organization_that_does_not_exist(mock_account_service_client):
    mock_account_service_client.organization_stub.find.total_matched_count = 0
    mock_account_service_client.organization_stub.find.return_value = Mock(total_matched_count=0)
    mock_account_service_client.organization_stub.create.return_value = Mock(id="o098765")

    org_id = mock_account_service_client.create_default_organization()

    assert org_id == "o098765"
    assert mock_account_service_client.organization_stub.find.call_count == 1
    assert mock_account_service_client.organization_stub.create.call_count == 1


def test_create_default_workspace_that_exist(mock_account_service_client):
    mock_account_service_client.workspace_stub.find.return_value = Mock(
        total_matched_count=1, workspaces=[Mock(id="w123456")]
    )

    workspace_id = mock_account_service_client.create_default_workspace(organization_id="o123456")

    assert workspace_id == "w123456"
    assert mock_account_service_client.workspace_stub.find.call_count == 1
    assert mock_account_service_client.workspace_stub.create.call_count == 0


def test_create_default_workspace_that_does_not_exist(mock_account_service_client):
    mock_account_service_client.workspace_stub.find.return_value = Mock(total_matched_count=0, workspaces=[])
    mock_account_service_client.workspace_stub.create.return_value = Mock(id="w123456")

    workspace_id = mock_account_service_client.create_default_workspace(organization_id="o123456")

    assert workspace_id == "w123456"
    assert mock_account_service_client.workspace_stub.find.call_count == 1
    assert mock_account_service_client.workspace_stub.create.call_count == 1


def test_create_initial_user_that_exist(mock_account_service_client):
    mock_account_service_client.user_stub.find.return_value = Mock(total_matched_count=1, users=[Mock(id="u123456")])

    user_id = mock_account_service_client.create_initial_user(organization_id="o123456")

    assert user_id == "u123456"
    assert mock_account_service_client.user_stub.find.call_count == 1
    assert mock_account_service_client.user_stub.create.call_count == 0


def test_create_initial_user_that_does_not_exist(mock_account_service_client):
    mock_account_service_client.user_stub.find.return_value = Mock(total_matched_count=0, users=[])
    mock_account_service_client.user_stub.create.return_value = Mock(id="u123456")

    user_id = mock_account_service_client.create_initial_user(organization_id="o123456")

    assert user_id == "u123456"
    assert mock_account_service_client.user_stub.find.call_count == 1
    assert mock_account_service_client.user_stub.create.call_count == 1


def test_modify_initial_user_external_id(mock_account_service_client):
    mock_account_service_client.user_stub.modify.return_value = Mock(external_id="e_id")

    external_id = mock_account_service_client.update_user_external_id(
        uid="u123456", organization_id="o123456", external_id="e_id"
    )

    assert external_id == "e_id"


def test_get_all_organizations(mock_account_service_client):
    expected_result = [{"id": "some-fake-id"}]
    list_organization_response = ListOrganizationsResponse()
    organization_data = OrganizationDataWithAdmins()
    organization_data.id = expected_result[0]["id"]
    list_organization_response.organizations.append(organization_data)

    mock_account_service_client.organization_stub.find.return_value = list_organization_response

    actual_result = mock_account_service_client.get_all_organizations()

    assert actual_result == expected_result


def test_get_all_organizations_users(mock_account_service_client):
    expected_result = [{"id": "some-fake-id", "organizationId": "some-fake-id"}]
    find_user_request = FindUserRequest(organization_id=expected_result[0]["id"])
    list_users_response = ListUsersResponse()
    user_data = UserData()
    user_data.id = expected_result[0]["id"]
    user_data.organization_id = expected_result[0]["organizationId"]
    list_users_response.users.append(user_data)
    mock_account_service_client.user_stub.find.return_value = list_users_response

    actual_result = mock_account_service_client.get_organizations_users(find_user_request=find_user_request)

    assert actual_result == expected_result


def test_change_user_status(mock_account_service_client):
    payload = {"organization_id": "some-fake-id", "user_id": "some-fake-id", "status": "DEL"}
    user_status_request = UserStatusRequest(**payload)
    user_status_response = UserStatusResponse()
    user_status_response.status = payload["status"]
    mock_account_service_client.user_status_stub.change.return_value = user_status_response

    actual_result = mock_account_service_client.change_user_status(user_status_request=user_status_request)

    assert actual_result == payload["status"]


def test_get_user_by_id(mock_account_service_client):
    payload = {"organization_id": "some-fake-org-id", "user_id": "some-fake-id"}
    user_id = {
        "id": "some-fake-id",
        "email": "some-fake-email",
        "status": "some-fake-status",
        "organizationId": "some-fake-org-id",
        "createdAt": "2023-11-30T12:30:45Z",
        "createdBy": "someone",
        "modifiedAt": "2023-11-30T12:30:45Z",
    }
    user_id_request = UserIdRequest(**payload)
    user_by_id_data = UserData()
    ParseDict(user_id, user_by_id_data)
    expected_response = UserByIDResponse.from_protobuf(user_by_id_data)
    mock_account_service_client.user_stub.get_by_id.return_value = user_by_id_data

    actual_result = mock_account_service_client.get_user_by_id(user_id_request)
    assert actual_result == expected_response


def test_get_active_intel_organizations(mock_account_service_client):
    org1 = OrganizationDataWithAdmins(
        id="org1",
        admins=[
            OrganizationDataWithAdmins.AdminSimpleData(email="admin1@intel.com"),
            OrganizationDataWithAdmins.AdminSimpleData(email="admin2@example.com"),
        ],
    )
    org2 = OrganizationDataWithAdmins(
        id="org2", admins=[OrganizationDataWithAdmins.AdminSimpleData(email="admin3@not_intel.com")]
    )
    org3 = OrganizationDataWithAdmins(
        id="org3", admins=[OrganizationDataWithAdmins.AdminSimpleData(email="admin4@intel.com")]
    )
    mock_response = ListOrganizationsResponse(
        organizations=[org1, org2, org3], total_count=5, total_matched_count=3, next_page=None
    )
    mock_account_service_client.organization_stub.find.return_value = mock_response

    result = mock_account_service_client.get_active_intel_organizations_ids()

    assert result == ["org1", "org3"]
    mock_account_service_client.organization_stub.find.assert_called_once()
    args, kwargs = mock_account_service_client.organization_stub.find.call_args
    assert args[0].status == "ACT"

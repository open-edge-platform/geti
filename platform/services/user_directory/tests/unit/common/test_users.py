# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


from grpc_interfaces.account_service.pb.user_common_pb2 import UserRole, UserRoleOperation

from common.users import update_missing_workspace_roles


def mock_workspace(mocker, name: str, workspace_id: str):
    mocked_workspaces = {"workspaces": [{"name": name, "id": workspace_id}]}
    mocker.patch("requests.get")
    mocker.patch("json.loads", return_value=mocked_workspaces)


def test_update_missing_workspace_roles_append_admin(mocker):
    role_ops = [
        UserRoleOperation(
            role=UserRole(role="organization_admin", resource_type="organization", resource_id="organization_123"),
            operation="CREATE",
        )
    ]

    default_workspace = "workspace_123"

    result = update_missing_workspace_roles(role_ops, default_workspace)

    assert len(result) == 2
    assert result[1].operation == "CREATE"
    assert result[1].role.role == "workspace_admin"
    assert result[1].role.resource_type == "workspace"
    assert result[1].role.resource_id == default_workspace


def test_update_missing_workspace_roles_append_contributor(mocker):
    role_ops = [
        UserRoleOperation(
            role=UserRole(
                role="organization_contributor", resource_type="organization", resource_id="organization_123"
            ),
            operation="CREATE",
        )
    ]

    default_workspace = "workspace_123"

    result = update_missing_workspace_roles(role_ops, default_workspace)

    assert len(result) == 2
    assert result[1].operation == "CREATE"
    assert result[1].role.role == "workspace_contributor"
    assert result[1].role.resource_type == "workspace"
    assert result[1].role.resource_id == default_workspace


def test_update_missing_workspace_roles_not_append(mocker):
    role_ops = [
        UserRoleOperation(
            role=UserRole(role="workspace_contributor", resource_type="workspace", resource_id="workspace_123"),
            operation="CREATE",
        )
    ]

    default_workspace = "workspace_124"

    result = update_missing_workspace_roles(role_ops, default_workspace)

    assert len(result) == 1
    assert result[0].operation == "CREATE"
    assert result[0].role.role == "workspace_contributor"
    assert result[0].role.resource_type == "workspace"
    assert result[0].role.resource_id == "workspace_123"


def test_update_missing_workspace_roles_not_append_multiple_roles(mocker):
    role_ops = [
        UserRoleOperation(
            role=UserRole(role="workspace_contributor", resource_type="workspace", resource_id="workspace_123"),
            operation="CREATE",
        ),
        UserRoleOperation(
            role=UserRole(
                role="organization_contributor", resource_type="organization", resource_id="organization_123"
            ),
            operation="CREATE",
        ),
    ]

    default_workspace = "workspace_124"

    result = update_missing_workspace_roles(role_ops, default_workspace)

    assert len(result) == 2
    assert result[0].operation == "CREATE"
    assert result[0].role.role == "workspace_contributor"
    assert result[0].role.resource_type == "workspace"
    assert result[0].role.resource_id == "workspace_123"

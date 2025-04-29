# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import http

import pytest
from models.error import AccountServiceError
from models.organization import Organization
from models.user import RoleOperation, RolePayload, User, UserRole, UserRoleOperation
from models.workspace import Workspace

from config.env import FF_MANAGE_USERS_ROLES


def test_set_get_roles(user: User, workspace: Workspace):
    role = UserRole("workspace_admin", "workspace", workspace.id)
    role_ops = [UserRoleOperation(role, RoleOperation.CREATE)]
    user.set_roles(role_ops)

    returned_roles = user.get_roles("workspace")
    assert len(returned_roles) == 1
    assert role == returned_roles[0]


def test_assign_get_user_roles(user: User, workspace: Workspace):
    if FF_MANAGE_USERS_ROLES:
        role_op = RolePayload("workspace_admin", workspace.id)
        user.assign_user_role(role_op)

        response = user.get_user_roles()
        assert len(response["roles"]) == 1
        returned_role = response["roles"][0]
        assert role_op.role == returned_role["role"]
        assert role_op.resource_id == returned_role["resourceId"]


def test_assign_role_with_overlapping_resource_type(user: User, workspace: Workspace):
    if FF_MANAGE_USERS_ROLES:
        # Assign an initial role to the user
        initial_role = RolePayload("workspace_admin", workspace.id)
        user.assign_user_role(initial_role)

        # Verify the initial role is assigned
        response = user.get_user_roles()
        assert len(response["roles"]) == 1
        assert response["roles"][0]["role"] == initial_role.role
        assert response["roles"][0]["resourceId"] == initial_role.resource_id

        # Assign a new role of the same resource type
        new_role = RolePayload("workspace_contributor", workspace.id)
        user.assign_user_role(new_role)

        # Verify the new role is assigned and the old role is removed
        response = user.get_user_roles()
        assert len(response["roles"]) == 1
        assert response["roles"][0]["role"] == new_role.role
        assert response["roles"][0]["resourceId"] == new_role.resource_id


def test_remove_role_rejected_not_for_project(user: User, workspace: Workspace):
    if FF_MANAGE_USERS_ROLES:
        role = RolePayload("workspace_admin", workspace.id)
        user.assign_user_role(role)

        # Verify role is assigned
        response = user.get_user_roles()
        assert len(response["roles"]) == 1
        assert response["roles"][0]["role"] == role.role

        # Remove the role
        try:
            user.delete_role(role)
        except AccountServiceError:
            pass

        response = user.get_user_roles()
        assert len(response["roles"]) == 1, "Role was deleted when it should not be possible"


def test_assign_roles_with_different_resource_types(user: User, workspace: Workspace, organization: Organization):
    if FF_MANAGE_USERS_ROLES:
        workspace_role = RolePayload("workspace_admin", workspace.id)
        org_role = RolePayload("organization_admin", organization.id)

        # Assign roles
        user.assign_user_role(workspace_role)
        user.assign_user_role(org_role)

        # Verify both roles are present
        response = user.get_user_roles()
        assert len(response["roles"]) == 2

        roles = {r["role"]: r["resourceId"] for r in response["roles"]}
        assert roles["workspace_admin"] == workspace.id
        assert roles["organization_admin"] == organization.id


def test_role_replacement_for_resource_type(user: User, workspace: Workspace):
    if FF_MANAGE_USERS_ROLES:
        role1 = RolePayload("workspace_admin", workspace.id)
        role2 = RolePayload("workspace_contributor", workspace.id)

        # Assign the first role
        user.assign_user_role(role1)

        # Replace with the second role
        user.assign_user_role(role2)

        # Verify only the second role exists
        response = user.get_user_roles()
        assert len(response["roles"]) == 1
        assert response["roles"][0]["role"] == role2.role
        assert response["roles"][0]["resourceId"] == role2.resource_id


def test_role_replacement_workspace_updated_for_organization_role_changes(
    user: User, workspace: Workspace, organization: Organization
):
    if FF_MANAGE_USERS_ROLES:
        main_role = RolePayload("organization_admin", organization.id)
        updated_role = RolePayload("organization_contributor", organization.id)
        expected_extra_role = RolePayload("workspace_contributor", workspace.id)

        # Assign the main role
        user.assign_user_role(main_role)
        user.assign_user_role(updated_role)

        response = user.get_user_roles()
        assert len(response["roles"]) == 2

        for role in response["roles"]:
            if role["role"] == expected_extra_role.role and role["resourceId"] == expected_extra_role.resource_id:
                break
        else:
            assert False, f"Did not find {expected_extra_role} on returned roles"


def test_set_get_roles_invalid_resource_type(user: User):
    invalid_name = "wooooorkspace"
    with pytest.raises(AccountServiceError) as err:
        user.get_roles(invalid_name)

    assert err.value.message == f"Invalid resource type: {invalid_name}"
    assert err.value.status_code == http.HTTPStatus.BAD_REQUEST


def test_set_roles_rollback_on_error(user: User, workspace: Workspace, organization: Organization):
    initial_role = UserRole("workspace_admin", "workspace", workspace.id)
    role_ops = [UserRoleOperation(initial_role, RoleOperation.CREATE)]
    user.set_roles(role_ops)

    correct_role = UserRole("organization_admin", "organization", organization.id)
    incorrect_role = UserRole("bad_role", "bad_res_type", "1234")
    role_ops = [
        UserRoleOperation(correct_role, RoleOperation.CREATE),
        UserRoleOperation(incorrect_role, RoleOperation.CREATE),
    ]
    try:
        user.set_roles(role_ops)
        assert False, "should raise error with incorrect role"
    except AccountServiceError as ex:
        assert ex.status_code == http.HTTPStatus.BAD_REQUEST

    returned_workspace_roles = user.get_roles("workspace")
    assert len(returned_workspace_roles) == 1
    assert initial_role == returned_workspace_roles[0]

    returned_organization_roles = user.get_roles("organization")
    assert len(returned_organization_roles) == 0


def test_set_roles_already_exists_error(user: User, workspace: Workspace, organization: Organization):
    initial_role = UserRole("workspace_admin", "workspace", workspace.id)
    role_ops = [UserRoleOperation(initial_role, RoleOperation.CREATE)]
    user.set_roles(role_ops)

    try:
        user.set_roles(role_ops)
        assert False, "should raise error with duplicated role"
    except AccountServiceError as ex:
        assert ex.status_code == http.HTTPStatus.CONFLICT

    # duplicated role should not be rollbacked!
    returned_workspace_roles = user.get_roles("workspace")
    assert len(returned_workspace_roles) == 1
    assert initial_role == returned_workspace_roles[0]

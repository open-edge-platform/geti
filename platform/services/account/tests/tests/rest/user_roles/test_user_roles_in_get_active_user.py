# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from models.user import RoleOperation, User, UserRole, UserRoleOperation

from tests.rest.user_roles.common import ComplexRolesModelPlayground


def test_get_active_user(user, workspace, signed_token):
    """
    Test covers the scenario where a user is assigned to more than one workspace,
    but only one workspace exists withing the organizations with ID: user.organization_id
    """
    with ComplexRolesModelPlayground() as playground:
        role_ops = [
            UserRoleOperation(
                UserRole("workspace_admin", "workspace", playground.workspace_to_stay.id),
                operation=RoleOperation.CREATE,
            ),
            UserRoleOperation(
                UserRole("workspace_contributor", "workspace", workspace.id),
                operation=RoleOperation.CREATE,
            ),
        ]
        user.set_roles(role_ops)

        returned_user = User.get_active_user(user.organization_id, signed_token)
        assert returned_user is not None
        assert returned_user.id == user.id
        assert len(returned_user.roles) == 1


def test_get_active_user_all_relationships(user, workspace, signed_token):
    with ComplexRolesModelPlayground():
        role_ops = [
            UserRoleOperation(
                UserRole("workspace_admin", "workspace", workspace.id),
                operation=RoleOperation.CREATE,
            ),
            UserRoleOperation(
                UserRole("organization_admin", "organization", user.organization_id),
                operation=RoleOperation.CREATE,
            ),
        ]
        user.set_roles(role_ops)

        returned_user = User.get_active_user(user.organization_id, signed_token)
        assert returned_user is not None
        assert returned_user.id == user.id
        assert len(returned_user.roles) == len(role_ops)

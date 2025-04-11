# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from models.user import RoleOperation, UserRole, UserRoleOperation

from tests.rest.user_roles.common import ComplexRolesModelPlayground


def test_delete_cascade_organization_roles():
    with ComplexRolesModelPlayground() as playground:
        playground.user0.set_roles(
            [
                UserRoleOperation(
                    UserRole("workspace_admin", "workspace", playground.workspace_0_to_be_deleted.id),
                    operation=RoleOperation.CREATE,
                ),
                UserRoleOperation(
                    UserRole("workspace_contributor", "workspace", playground.workspace_1_to_be_deleted.id),
                    operation=RoleOperation.CREATE,
                ),
                UserRoleOperation(
                    UserRole("workspace_admin", "workspace", playground.workspace_to_stay.id),
                    operation=RoleOperation.CREATE,
                ),
            ]
        )

        playground.org_to_be_deleted.delete()

        user_roles_after_org_deletion = playground.user0.get_roles("workspace")

        assert len(user_roles_after_org_deletion) == 1
        assert user_roles_after_org_deletion == [
            UserRole("workspace_admin", "workspace", playground.workspace_to_stay.id)
        ]


def test_delete_cascade_workspace_roles():
    with ComplexRolesModelPlayground() as playground:
        playground.user0.set_roles(
            [
                UserRoleOperation(
                    UserRole("workspace_admin", "workspace", playground.workspace_0_to_be_deleted.id),
                    operation=RoleOperation.CREATE,
                ),
                UserRoleOperation(
                    UserRole("workspace_contributor", "workspace", playground.workspace_1_to_be_deleted.id),
                    operation=RoleOperation.CREATE,
                ),
                UserRoleOperation(
                    UserRole("workspace_admin", "workspace", playground.workspace_to_stay.id),
                    operation=RoleOperation.CREATE,
                ),
            ]
        )

        playground.workspace_0_to_be_deleted.delete()
        playground.workspace_1_to_be_deleted.delete()

        user_roles_after_workspace_deletion = playground.user0.get_roles("workspace")

        assert len(user_roles_after_workspace_deletion) == 1
        assert user_roles_after_workspace_deletion == [
            UserRole("workspace_admin", "workspace", playground.workspace_to_stay.id)
        ]


def test_delete_cascade_user_roles():
    with ComplexRolesModelPlayground() as playground:
        playground.user0.set_roles(
            [
                UserRoleOperation(
                    UserRole("workspace_admin", "workspace", playground.workspace_0_to_be_deleted.id),
                    operation=RoleOperation.CREATE,
                ),
                UserRoleOperation(
                    UserRole("workspace_contributor", "workspace", playground.workspace_1_to_be_deleted.id),
                    operation=RoleOperation.CREATE,
                ),
                UserRoleOperation(
                    UserRole("workspace_admin", "workspace", playground.workspace_to_stay.id),
                    operation=RoleOperation.CREATE,
                ),
            ]
        )

        playground.user0.delete()

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from models.user import FindUserRequest, RoleOperation, User, UserRole, UserRoleOperation

from tests.rest.user_roles.common import ComplexRolesModelPlayground


def test_find_user_with_role():
    """Find user that has single role and all parameters are provided in the find request"""
    with ComplexRolesModelPlayground() as playground:
        playground.user0.set_roles(
            [
                UserRoleOperation(
                    UserRole("workspace_admin", "workspace", playground.workspace_to_stay.id),
                    operation=RoleOperation.CREATE,
                ),
            ]
        )

        find_request = FindUserRequest(
            second_name=playground.user0.second_name,
            role="workspace_admin",
            resource_type=["workspace"],
            resource_id=playground.workspace_to_stay.id,
        )
        returned_users = playground.user0.find(playground.user0.organization_id, request=find_request)

        assert returned_users.total_matched_count == 1
        assert returned_users.users[0].second_name == find_request.second_name
        assert len(returned_users.users[0].roles) > 0
        assert returned_users.users[0].roles[0]["role"] == "workspace_admin"


def test_find_user_get_single_role():
    """Return single user with his workspace roles when specific role is requested and user has many roles"""
    with ComplexRolesModelPlayground() as playground:
        playground.user0.set_roles(
            [
                UserRoleOperation(
                    UserRole("workspace_admin", "workspace", playground.workspace_to_stay.id),
                    operation=RoleOperation.CREATE,
                ),
                UserRoleOperation(
                    UserRole("workspace_contributor", "workspace", playground.workspace_1_to_be_deleted.id),
                    operation=RoleOperation.CREATE,
                ),
            ]
        )

        find_request = FindUserRequest(
            second_name=playground.user0.second_name,
            role="workspace_admin",
            resource_type=["workspace"],
            resource_id=playground.workspace_to_stay.id,
        )
        returned_users = playground.user0.find(playground.user0.organization_id, request=find_request)

        assert returned_users.total_matched_count == 1
        assert returned_users.users[0].second_name == find_request.second_name
        assert len(returned_users.users[0].roles) == 1


def test_find_user_only_by_organization_resource_type():
    """Filter users based on whether they have a role with specific resource type"""
    with ComplexRolesModelPlayground() as playground:
        find_request = FindUserRequest(
            resource_type=["organization"],
        )
        returned_users = User.find(playground.user0.organization_id, request=find_request)
        assert returned_users.total_matched_count == 0

        playground.user0.set_roles(
            [
                UserRoleOperation(
                    UserRole("organization_admin", "organization", playground.user0.organization_id),
                    operation=RoleOperation.CREATE,
                ),
                UserRoleOperation(
                    UserRole("workspace_contributor", "workspace", playground.workspace_to_stay.id),
                    operation=RoleOperation.CREATE,
                ),
            ]
        )
        playground.user1.set_roles(
            [
                UserRoleOperation(
                    UserRole("workspace_admin", "workspace", playground.workspace_to_stay.id),
                    operation=RoleOperation.CREATE,
                )
            ]
        )

        returned_users = User.find(playground.user0.organization_id, request=find_request)

        assert returned_users.total_matched_count == 1
        assert returned_users.users[0].second_name == playground.user0.second_name
        assert len(returned_users.users[0].roles) == 1
        assert returned_users.users[0].roles[0]["role"] == "organization_admin"


def test_find_user_only_by_role(user):
    """Return only single organization role when no specific role requested and user has many roles."""
    with ComplexRolesModelPlayground() as playground:
        playground.user0.set_roles(
            [
                UserRoleOperation(
                    UserRole("organization_admin", "organization", playground.user0.organization_id),
                    operation=RoleOperation.CREATE,
                ),
                UserRoleOperation(
                    UserRole("workspace_contributor", "workspace", playground.workspace_to_stay.id),
                    operation=RoleOperation.CREATE,
                ),
            ]
        )
        user.set_roles(
            [
                UserRoleOperation(
                    UserRole("workspace_admin", "workspace", playground.workspace_0_to_be_deleted.id),
                    operation=RoleOperation.CREATE,
                )
            ]
        )

        find_request = FindUserRequest(
            resource_type=["workspace"],
        )
        returned_users = User.find(playground.user0.organization_id, request=find_request)

        assert returned_users.total_matched_count == 1
        assert returned_users.users[0].second_name == playground.user0.second_name
        assert len(returned_users.users[0].roles) == 1
        assert returned_users.users[0].roles[0]["role"] == "workspace_contributor"


def test_find_user_filter_roles():
    """Only roles with fitting resource type are returned when resource type is specified"""
    with ComplexRolesModelPlayground() as playground:
        playground.user0.set_roles(
            [
                UserRoleOperation(
                    UserRole("organization_admin", "organization", playground.user0.organization_id),
                    operation=RoleOperation.CREATE,
                ),
                UserRoleOperation(
                    UserRole("workspace_admin", "workspace", playground.workspace_to_stay.id),
                    operation=RoleOperation.CREATE,
                ),
                UserRoleOperation(
                    UserRole("workspace_contributor", "workspace", playground.workspace_to_stay.id),
                    operation=RoleOperation.CREATE,
                ),
            ]
        )
        playground.user1.set_roles(
            [
                UserRoleOperation(
                    UserRole("workspace_admin", "workspace", playground.workspace_to_stay.id),
                    operation=RoleOperation.CREATE,
                )
            ]
        )

        find_request = FindUserRequest(
            resource_type=["workspace"],
        )
        returned_users = User.find(playground.user0.organization_id, request=find_request)

        assert returned_users.total_matched_count == 2
        assert returned_users.users[0].second_name == playground.user0.second_name
        assert len(returned_users.users[0].roles) == 2


def test_find_user_get_many_roles():
    """Return all user roles with given type when specific no specific role name requested"""
    with ComplexRolesModelPlayground() as playground:
        playground.user0.set_roles(
            [
                UserRoleOperation(
                    UserRole("workspace_admin", "workspace", playground.workspace_to_stay.id),
                    operation=RoleOperation.CREATE,
                ),
                UserRoleOperation(
                    UserRole("workspace_contributor", "workspace", playground.workspace_to_stay.id),
                    operation=RoleOperation.CREATE,
                ),
            ]
        )

        find_request = FindUserRequest(
            second_name=playground.user0.second_name,
            resource_type=["workspace"],
            resource_id=playground.workspace_to_stay.id,
        )
        returned_users = playground.user0.find(playground.user0.organization_id, request=find_request)

        assert returned_users.total_matched_count == 1
        assert returned_users.users[0].second_name == find_request.second_name
        assert len(returned_users.users[0].roles) == 2
        for role in returned_users.users[0].roles:
            assert role["resourceType"] == "workspace"


def test_user_not_found_wrong_role():
    with ComplexRolesModelPlayground() as playground:
        playground.user0.set_roles(
            [
                UserRoleOperation(
                    UserRole("workspace_admin", "workspace", playground.workspace_to_stay.id),
                    operation=RoleOperation.CREATE,
                ),
            ]
        )

        find_request = FindUserRequest(
            second_name=playground.user0.second_name,
            role="wrongr2ole",
            resource_type=["workspace"],
            resource_id=playground.workspace_to_stay.id,
        )
        returned_users = playground.user0.find(playground.user0.organization_id, request=find_request)

        assert returned_users.total_matched_count == 0
        assert len(returned_users.users) == 0


def test_find_user_with_role_empty_role_name():
    with ComplexRolesModelPlayground() as playground:
        playground.user0.set_roles(
            [
                UserRoleOperation(
                    UserRole("workspace_admin", "workspace", playground.workspace_to_stay.id),
                    operation=RoleOperation.CREATE,
                ),
            ]
        )

        find_request = FindUserRequest(second_name=playground.user0.second_name, resource_type=["workspace"])
        returned_users = playground.user0.find(playground.user0.organization_id, request=find_request)

        assert returned_users.total_matched_count == 1
        assert returned_users.users[0].second_name == find_request.second_name
        assert len(returned_users.users[0].roles) == 1
        assert returned_users.users[0].roles[0]["resourceType"] == "workspace"


def test_find_user_only_roles_for_requested_org(user):
    with ComplexRolesModelPlayground() as playground:
        user.set_roles(
            [
                UserRoleOperation(
                    UserRole("organization_admin", "organization", playground.org_to_stay.id),
                    operation=RoleOperation.CREATE,
                ),
                UserRoleOperation(
                    UserRole("organization_contributor", "organization", user.organization_id),
                    operation=RoleOperation.CREATE,
                ),
            ]
        )

        find_request = FindUserRequest(second_name=user.second_name)
        returned_users = user.find(organization_id=user.organization_id, request=find_request)

        assert returned_users.total_matched_count == 1
        assert returned_users.users[0].second_name == user.second_name

        assert len(returned_users.users[0].roles) == 1
        assert returned_users.users[0].roles[0]["resourceType"] == "organization"
        assert returned_users.users[0].roles[0]["role"] == "organization_contributor"

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import http
from copy import deepcopy

from models.error import AccountServiceError
from models.user import FindUserRequest, RoleOperation, User, UserRole, UserRoleOperation
from utils.concurrent import ConcurrentUsers

from config.env import FF_MANAGE_USERS


def test_send_invitation(workspace):
    user = User.randomize(workspace.organization_id)
    invitation_response = user.send_invitation([])

    find_response = User.find(organization_id=workspace.organization_id, request=FindUserRequest())
    assert len(find_response.users) == 1
    just_invited_user = find_response.users[0]
    assert user.email.lower() == just_invited_user.email
    assert just_invited_user.status == "RGS"
    assert just_invited_user.id == invitation_response.user_id


def test_send_invitation_conflict(workspace):
    user_to_be_invited = User.randomize(workspace.organization_id)
    user_to_be_invited.send_invitation([])

    try:
        user_to_be_invited.send_invitation([])
    except AccountServiceError as err:
        assert err.status_code == http.HTTPStatus.CONFLICT
        assert (
            err.message
            == f'user with email "{user_to_be_invited.email.lower()}" in organization "{workspace.organization_id}" already exists'
        )


def test_send_invitation_conflict_possible_after_status_del(workspace):
    user_to_be_invited = User.randomize(workspace.organization_id)
    user_to_be_invited.send_invitation([])

    user_with_at_least_same_email_to_be_invited = deepcopy(user_to_be_invited)

    try:
        user_with_at_least_same_email_to_be_invited.send_invitation([])
    except AccountServiceError as err:
        assert err.status_code == http.HTTPStatus.CONFLICT
        assert err.message == (
            f'user with email "{user_with_at_least_same_email_to_be_invited.email.lower()}" '
            f'in organization "{workspace.organization_id}" already exists'
        )

    user_to_be_invited.status = "DEL"
    user_to_be_invited.modify()
    user_with_at_least_same_email_to_be_invited.send_invitation([])
    # fake assert (no exception raised)


def test_send_invitation_parallel(workspace):
    def user_creation():
        for _ in range(200):
            user = User.randomize(workspace.organization_id)
            try:
                user.send_invitation([])
            except AccountServiceError:
                raise

    many_users = ConcurrentUsers(10, user_creation)
    many_users.start_and_wait()

    real_users = User.find(workspace.organization_id, FindUserRequest())
    real_users_count = len(real_users.users)
    assert real_users_count == 300


def test_send_invitation_with_roles(workspace):
    if FF_MANAGE_USERS:
        user = User.randomize(workspace.organization_id)

        role_ops = [
            UserRoleOperation(
                UserRole("organization_admin", "organization", workspace.organization_id),
                operation=RoleOperation.CREATE,
            )
        ]
        invitation_response = user.send_invitation(role_ops)

        find_response = User.find(
            organization_id=workspace.organization_id, request=FindUserRequest(resource_type="workspace")
        )
        assert len(find_response.users) == 1
        just_invited_user = find_response.users[0]
        assert user.email.lower() == just_invited_user.email
        assert len(just_invited_user.roles) == 1
        print(just_invited_user.roles[0])
        assert just_invited_user.roles[0]["role"] == "workspace_admin"
        assert just_invited_user.roles[0]["resourceType"] == "workspace"
        assert just_invited_user.roles[0]["resourceId"] == workspace.id
        assert just_invited_user.status == "RGS"
        assert just_invited_user.id == invitation_response.user_id

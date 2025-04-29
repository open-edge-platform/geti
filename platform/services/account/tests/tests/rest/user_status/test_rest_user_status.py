# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import datetime
import http

from models.error import AccountServiceError
from models.personal_access_token import PersonalAccessToken, PersonalAccessTokenCreateRequest
from models.user import User
from models.user_status import (
    ListMembershipResponse,
    MembershipDeleteRequest,
    MembershipRequest,
    UserStatus,
    UserStatusRequest,
)
from utils.data_gen import gen_random_str

from config.env import FF_MANAGE_USERS


def test_change_user_status(user):
    req = UserStatusRequest(status="SSP", user_id=user.id, organization_id=user.organization_id)
    if FF_MANAGE_USERS:
        returned_status = UserStatus.modify(req)
    else:
        returned_status = UserStatus.change(req)

    assert returned_status.status == req.status
    assert returned_status.user_id == req.user_id
    assert returned_status.organization_id == req.organization_id
    assert returned_status.created_at is not None and returned_status.created_at != ""
    assert returned_status.id is not None and returned_status.id != ""


def test_change_user_status_to_delete(user):
    pat_req = PersonalAccessTokenCreateRequest(
        organization_id=user.organization_id,
        user_id=user.id,
        created_by=user.created_by,
        name=gen_random_str(),
        description=gen_random_str(100),
        expires_at=datetime.datetime.utcfromtimestamp(
            int(datetime.datetime.timestamp(datetime.datetime.now() + (datetime.timedelta(hours=24))))
        ).isoformat()
        + "Z",
    )
    PersonalAccessToken.create(pat_req)
    req = UserStatusRequest(status="DEL", user_id=user.id, organization_id=user.organization_id)
    if FF_MANAGE_USERS:
        returned_status = UserStatus.modify(req)
    else:
        returned_status = UserStatus.change(req)
    returned_pat = PersonalAccessToken.find(user.organization_id, user.id)

    assert returned_status.status == req.status
    assert returned_status.user_id == req.user_id
    assert returned_status.organization_id == req.organization_id
    assert returned_status.created_at is not None and returned_status.created_at != ""
    assert returned_status.id is not None and returned_status.id != ""
    assert len(returned_pat.personal_access_tokens) == 0


def test_user_logout(user, signed_token):
    req = UserStatusRequest(status="ACT", user_id=user.id, organization_id=user.organization_id)
    if FF_MANAGE_USERS:
        UserStatus.modify(req)
    else:
        UserStatus.change(req)

    result = UserStatus.logout(signed_token)
    assert result is None

    returned_user = User.get_by_id(user.id, user.organization_id)
    assert returned_user.last_logout_date is not None

    # Convert last_logout_date to a datetime object
    last_logout_date = datetime.datetime.strptime(returned_user.last_logout_date, "%Y-%m-%dT%H:%M:%S.%fZ")

    # Get the current UTC time
    current_time = datetime.datetime.utcnow()

    # Check that the time difference is within an acceptable range
    time_difference = current_time - last_logout_date
    assert datetime.timedelta(0) < time_difference < datetime.timedelta(seconds=2)


def test_cannot_change_user_status_to_del_on_single_org_admin(organization_admin):
    req = UserStatusRequest(
        status="DEL", user_id=organization_admin.id, organization_id=organization_admin.organization_id
    )
    try:
        if FF_MANAGE_USERS:
            UserStatus.modify(req)
        else:
            UserStatus.change(req)
    except AccountServiceError as ex:
        assert ex.status_code == http.HTTPStatus.BAD_REQUEST
        assert ex.message == "You cannot remove the last admin in the organization."
    else:
        assert False, "no exception raised when expected"


def test_get_memberships(user):
    if FF_MANAGE_USERS:
        req = MembershipRequest(
            organization_id=user.organization_id,
            first_name=user.first_name,
            second_name=user.second_name,
            email=user.email,
            status="ACT",
            name=user.first_name,
            sort_by="createdAt",
            sort_direction="asc",
            skip=0,
            limit=10,
        )
        response = UserStatus.get_memberships(req)

        assert response is not None
        assert isinstance(response, ListMembershipResponse)
        assert len(response.memberships) > 0
        for membership in response.memberships:
            assert membership.user_id == user.id
            assert membership.first_name == user.first_name


def test_get_memberships_only_by_name(user):
    if FF_MANAGE_USERS:
        req = MembershipRequest(organization_id=user.organization_id, name=user.second_name, skip=0, limit=10)
        response = UserStatus.get_memberships(req)

        assert response is not None
        assert isinstance(response, ListMembershipResponse)
        assert len(response.memberships) > 0
        for membership in response.memberships:
            assert membership.user_id == user.id
            assert membership.second_name == user.second_name


def test_get_memberships_with_pagination(user):
    if FF_MANAGE_USERS:
        req = MembershipRequest(organization_id=user.organization_id, skip=0, limit=5)
        response = UserStatus.get_memberships(req)

        assert response is not None
        assert isinstance(response, ListMembershipResponse)
        assert len(response.memberships) <= 5


def test_get_memberships_with_sorting(user):
    if FF_MANAGE_USERS:
        req = MembershipRequest(organization_id=user.organization_id, sort_by="createdAt", sort_direction="desc")
        response = UserStatus.get_memberships(req)

        assert response is not None
        assert isinstance(response, ListMembershipResponse)
        assert len(response.memberships) > 0
        assert response.memberships == sorted(response.memberships, key=lambda x: x.created_at, reverse=True)


def test_get_memberships_no_records(user):
    if FF_MANAGE_USERS:
        req = MembershipRequest(organization_id=user.organization_id, first_name="NonExistentFirstName")
        response = UserStatus.get_memberships(req)

        assert response is not None
        assert isinstance(response, ListMembershipResponse)
        assert len(response.memberships) == 0


def test_delete_membership(user):
    if FF_MANAGE_USERS:
        pat_req = PersonalAccessTokenCreateRequest(
            organization_id=user.organization_id,
            user_id=user.id,
            created_by=user.created_by,
            name=gen_random_str(),
            description=gen_random_str(100),
            expires_at=datetime.datetime.utcfromtimestamp(
                int(datetime.datetime.timestamp(datetime.datetime.now() + (datetime.timedelta(hours=24))))
            ).isoformat()
            + "Z",
        )
        PersonalAccessToken.create(pat_req)
        req = MembershipDeleteRequest(user_id=user.id, organization_id=user.organization_id)
        UserStatus.delete(req)
        returned_pat = PersonalAccessToken.find(user.organization_id, user.id)
        deleted_req = MembershipRequest(organization_id=user.organization_id, first_name=user.first_name)
        returned_status = UserStatus.get_memberships(deleted_req)

        assert len(returned_status.memberships) == 0
        assert len(returned_pat.personal_access_tokens) == 0

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from models.membership import ListUserMembershipResponse, Membership, UserMembershipRequest, UserMembershipResponse
from models.organization import Organization
from models.user import User

from config.env import FF_MANAGE_USERS


def test_get_user_membership(user):
    if FF_MANAGE_USERS:
        req = UserMembershipRequest(user_id=user.id)
        response = Membership.get_user_memberships(req)

        assert response is not None
        assert isinstance(response, ListUserMembershipResponse)
        assert len(response.memberships) > 0
        for membership in response.memberships:
            assert isinstance(membership, UserMembershipResponse)
            assert membership.organization_id == user.organization_id


def test_get_user_membership_by_organization_name():
    if FF_MANAGE_USERS:
        # setup
        orga = Organization.randomize()
        orga_returned = orga.create()
        usera1 = User.randomize(organization_id=orga_returned.id)
        usera1_returned = usera1.create()

        # test
        req = UserMembershipRequest(user_id=usera1_returned.id, organization_name=orga_returned.name)
        response = Membership.get_user_memberships(req)

        assert response is not None
        assert isinstance(response, ListUserMembershipResponse)
        assert len(response.memberships) > 0
        for membership in response.memberships:
            assert isinstance(membership, UserMembershipResponse)
            assert membership.organization_name == orga_returned.name


def test_get_user_membership_with_pagination(user):
    if FF_MANAGE_USERS:
        req = UserMembershipRequest(user_id=user.id, limit=3)
        response = Membership.get_user_memberships(req)

        assert response is not None
        assert isinstance(response, ListUserMembershipResponse)
        assert len(response.memberships) <= 5


def test_get_user_memberships_with_sorting(user):
    if FF_MANAGE_USERS:
        req = UserMembershipRequest(user_id=user.id, sort_by="createdAt", sort_direction="desc")
        response = Membership.get_user_memberships(req)

        assert response is not None
        assert isinstance(response, ListUserMembershipResponse)
        assert len(response.memberships) > 0
        assert response.memberships == sorted(response.memberships, key=lambda x: x.created_at, reverse=True)


def test_get_user_memberships_no_records(user):
    if FF_MANAGE_USERS:
        req = UserMembershipRequest(user_id=user.id, organization_name="NonExistentFirstName")
        response = Membership.get_user_memberships(req)

        assert response is not None
        assert isinstance(response, ListUserMembershipResponse)
        assert len(response.memberships) == 0

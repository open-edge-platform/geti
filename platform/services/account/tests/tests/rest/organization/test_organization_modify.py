# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from fixtures.organization import organization
from models.organization import Organization, OrganizationWithAdmins
from models.user import User

from config.env import FEATURE_FLAG_REQ_ACCESS


def test_modify_organization_with_auth_token(user, signed_token, organization):
    organization.country = "POL"
    returned_org = organization.modify(headers={"x-auth-request-access-token": signed_token})
    assert returned_org.modified_by == user.id

    org_from_get = OrganizationWithAdmins.get(returned_org.id)
    assert org_from_get.modified_by == user.id


def test_modify_organization_set_del_status_cascade_users(user, organization):
    user_before_from_get = User.get_by_id(user.id, organization.id)
    assert user_before_from_get.status == "ACT"

    organization.status = "DEL"
    returned_org = organization.modify()

    org_from_get = OrganizationWithAdmins.get(returned_org.id)
    assert org_from_get.status == "DEL"
    user_from_get = User.get_by_id(user.id, returned_org.id)
    assert user_from_get.status == "DEL"


organization_active = organization
organization_to_be_set_deleted = organization


def test_modify_organization_set_del_status_cascade_users_multiple(
    organization_active: Organization, organization_to_be_set_deleted: Organization
):
    users_in_organization_active = []
    users_in_organization_to_be_set_deleted = []
    for _ in range(5):
        new_user_in_organization_active = User.randomize(organization_active.id)
        new_user_in_organization_active.create()
        users_in_organization_active.append(new_user_in_organization_active)
        new_user_in_organization_to_be_set_deleted = User.randomize(organization_to_be_set_deleted.id)
        new_user_in_organization_to_be_set_deleted.create()
        users_in_organization_to_be_set_deleted.append(new_user_in_organization_to_be_set_deleted)

    for user in users_in_organization_active:
        user_returned = User.get_by_id(user.id, organization_active.id)
        assert user_returned.status == "ACT"

    for user in users_in_organization_to_be_set_deleted:
        user_returned = User.get_by_id(user.id, organization_to_be_set_deleted.id)
        assert user_returned.status == "ACT"

    organization_to_be_set_deleted.status = "DEL"
    returned_organization_to_be_set_deleted = organization_to_be_set_deleted.modify()

    org_from_get = OrganizationWithAdmins.get(returned_organization_to_be_set_deleted.id)
    assert org_from_get.status == "DEL"

    for user in users_in_organization_active:
        user_returned = User.get_by_id(user.id, organization_active.id)
        assert user_returned.status == "ACT"

    for user in users_in_organization_to_be_set_deleted:
        user_returned = User.get_by_id(user.id, organization_to_be_set_deleted.id)
        assert user_returned.status == "DEL"


def test_modify_organization_set_del_no_users(organization):
    organization.status = "DEL"
    returned_org = organization.modify()

    org_from_get = OrganizationWithAdmins.get(returned_org.id)
    assert org_from_get.status == "DEL"


def test_activate_organization_and_users():
    if FEATURE_FLAG_REQ_ACCESS:
        organization = Organization.randomize()
        organization.status = "REQ"
        organization.create()
        users_in_organization = []
        for _ in range(5):
            new_user_in_organization = User.randomize(organization.id)
            new_user_in_organization.status = "REQ"
            new_user_in_organization.create()
            users_in_organization.append(new_user_in_organization)

        for user in users_in_organization:
            user_returned = User.get_by_id(user.id, organization.id)
            assert user_returned.status == "REQ"

        org_from_get = OrganizationWithAdmins.get(organization.id)
        assert org_from_get.status == "REQ"

        organization.status = "ACT"
        organization.modify()

        org_from_get = OrganizationWithAdmins.get(organization.id)
        assert org_from_get.status == "ACT"

        for user in users_in_organization:
            user_returned = User.get_by_id(user.id, organization.id)
            assert user_returned.status == "ACT"


def test_request_access_reason(organization):
    organization.request_access_reason = "test reason"
    returned_org = organization.modify()

    org_from_get = OrganizationWithAdmins.get(returned_org.id)
    assert org_from_get.request_access_reason == "test reason"

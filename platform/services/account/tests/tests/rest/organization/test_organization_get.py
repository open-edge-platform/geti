# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from models.organization import OrganizationWithAdmins


def test_get_organization(organization):
    returned_org_from_get = OrganizationWithAdmins.get(organization.id)
    assert returned_org_from_get == organization


def test_get_organization_with_admins(organization, organization_admin):
    returned_org_from_get = OrganizationWithAdmins.get(organization.id)
    assert returned_org_from_get == organization
    assert len(returned_org_from_get.admins) == 1
    assert returned_org_from_get.admins[0].email == organization_admin.email.lower()


def test_get_organization_with_admins_through_invitation(organization_invitation):
    org_from_invitation, user_from_invitation = organization_invitation

    returned_org_from_get = OrganizationWithAdmins.get(org_from_invitation.id)

    assert len(returned_org_from_get.admins) == 1
    assert returned_org_from_get.admins[0].email == user_from_invitation.email

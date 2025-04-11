# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import http

import pytest
from models.error import AccountServiceError
from models.organization import FindOrganizationRequest, Organization, OrganizationWithAdmins
from models.user import User


def test_send_invitation():
    org = Organization.randomize()
    user = User.randomize(organization_id=org.id)

    try:
        org.send_invitation(user)

        find_org_req = FindOrganizationRequest(name=org.name)
        org_find_response = OrganizationWithAdmins.find(find_org_req)
        orgs_returned = org_find_response.organizations
        assert len(orgs_returned) == 1
        assert orgs_returned[0].name == org.name
        assert orgs_returned[0].request_access_reason == org.request_access_reason
    finally:
        orgs_returned[0].delete()


def test_send_invitation_user_conflict():
    org = Organization.randomize()
    user = User.randomize(organization_id=org.id)

    org.send_invitation(user)

    try:
        org.send_invitation(user)
    except AccountServiceError as err:
        assert err.status_code == http.HTTPStatus.CONFLICT
        assert err.message == f'user with email "{user.email}" already exists'

        # test if second organization creation was rolled back
        find_org_req = FindOrganizationRequest(name=org.name)
        org_find_response = OrganizationWithAdmins.find(find_org_req)
        assert len(org_find_response.organizations) == 1


@pytest.mark.parametrize(
    "invitation_request",
    [
        {},
        {"organizationData": {}},
        {"organizationData": {"name": "fake3"}},
        {"adminData": {}},
        {"organizationData": {}, "adminData": {}},
        {"organizationData": {}, "adminData": {"email": "fake@domain.com"}},
        {"organizationData": {"createdBy": "fuzzstring"}},
    ],
)
def test_send_invitation_bad_request(invitation_request):
    org = Organization.randomize()

    with pytest.raises(AccountServiceError) as ex:
        org.send_invitation(invitation_request=invitation_request)
    assert ex.value.status_code == http.HTTPStatus.BAD_REQUEST

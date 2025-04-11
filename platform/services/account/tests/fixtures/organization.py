# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from models.organization import FindOrganizationRequest, Organization, OrganizationWithAdmins
from models.user import User

from config.consts import TEST_PHOTO_FILEPATH


@pytest.fixture
def organization():
    org = Organization.randomize()
    org_returned = org.create()
    yield org_returned
    org.delete()


@pytest.fixture
def organization_photo(organization):
    organization.add_photo(TEST_PHOTO_FILEPATH)
    yield
    organization.delete_photo()


@pytest.fixture
def organization_invitation():
    org = Organization.randomize()
    user = User.randomize(organization_id=org.id)

    org.send_invitation(user)

    find_org_req = FindOrganizationRequest(name=org.name)
    org_find_response = OrganizationWithAdmins.find(find_org_req)
    orgs_returned = org_find_response.organizations
    yield orgs_returned[0], user
    orgs_returned[0].delete()

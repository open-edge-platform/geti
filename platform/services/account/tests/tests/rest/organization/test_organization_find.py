# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import http
import itertools

import pytest
from fixtures.organization import organization
from models.error import AccountServiceError
from models.organization import FindOrganizationRequest, Organization, OrganizationWithAdmins

organization2 = organization
organization3 = organization
organization4 = organization


# noinspection PyUnusedLocal,PyShadowingNames
def test_find_organization(organization, organization2, organization3, organization4):
    find_request = FindOrganizationRequest(name=organization2.name)
    find_response = OrganizationWithAdmins.find(find_request)

    assert find_response.organizations == [organization2]
    assert find_response.total_count >= 4
    assert find_response.total_matched_count == 1


def test_find_organization_by_id(organization, organization2, organization3, organization4):
    find_request = FindOrganizationRequest(id=organization3.id)
    find_response = OrganizationWithAdmins.find(find_request)

    assert find_response.organizations == [organization3]
    assert find_response.total_count >= 4
    assert find_response.total_matched_count == 1


def test_find_by_like_request_access_reason(organization, organization2, organization3, organization4):
    find_request = FindOrganizationRequest(request_access_reason=organization3.request_access_reason)
    find_response = OrganizationWithAdmins.find(find_request)

    assert find_response.organizations == [organization3]
    assert find_response.total_count >= 4
    assert find_response.total_matched_count == 1


def test_find_organization_with_limit(organization, organization2, organization3, organization4):
    find_request = FindOrganizationRequest(limit=10, cell_id=organization.cell_id)
    find_response = OrganizationWithAdmins.find(find_request)

    assert find_response.total_count >= 4
    if find_response.next_page["limit"] == 0:
        assert len(find_response.organizations) <= 10
    else:
        assert len(find_response.organizations) == 10


fields = ["name", "location", "cell_id"]
data_find_values = [
    ("ONLYUPPER123", "onlyupper123"),
    ("onlylower456", "ONLYLOWER456"),
    ("AcMe", "acme"),
    ("acme", "aCmE"),
]


@pytest.mark.parametrize(
    ["field_name", "original_org_name", "find_name"],
    [(field, *values) for field, values in itertools.product(fields, data_find_values)],
)
def test_find_organization_name_case_insensitive(field_name, original_org_name, find_name):
    org = Organization.randomize(**{field_name: original_org_name})
    org_returned = org.create()

    try:
        find_request = FindOrganizationRequest(limit=1, **{field_name: find_name})
        find_response = OrganizationWithAdmins.find(find_request)

        assert find_response.total_matched_count == 1, org_returned
        assert find_response.organizations == [org_returned], org_returned
    finally:
        org.delete()


def test_find_sortby_organization():
    common_location = "Warsaw"
    find_request = FindOrganizationRequest(location=common_location, sort_by="cellId", sort_direction="asc")
    count_before = len(OrganizationWithAdmins.find(find_request).organizations)
    org0 = Organization.randomize(location=common_location, cell_id="456")
    org0.create()
    org1 = Organization.randomize(location=common_location, cell_id="789")
    org1.create()
    org2 = Organization.randomize(location=common_location, cell_id="123")
    org2.create()

    find_response = OrganizationWithAdmins.find(find_request)

    org0.delete()
    org1.delete()
    org2.delete()

    for returned_org in find_response.organizations:
        returned_org.created_at = None

    found_organization_ids = [organization.id for organization in find_response.organizations]
    for org_id in [org2.id, org0.id, org1.id]:
        assert org_id in found_organization_ids
    assert find_response.total_count >= 3
    assert find_response.total_matched_count == 3 + count_before


def test_find_sortby_status_no_pagination():
    find_request = FindOrganizationRequest(sort_by="status", sort_direction="asc")
    find_response = OrganizationWithAdmins.find(find_request)
    repeated_find_response = OrganizationWithAdmins.find(find_request)

    assert find_response.total_count == repeated_find_response.total_count

    for org1, org2 in zip(find_response.organizations, repeated_find_response.organizations):
        assert org1.id == org2.id


def test_find_sortby_status_with_pagination():
    full_request = FindOrganizationRequest(sort_by="status", sort_direction="asc")
    full_response = OrganizationWithAdmins.find(full_request)
    total_count = full_response.total_count
    limit = 2
    paginated_organizations = []
    num_pages = (total_count + limit - 1) // limit

    for page in range(num_pages):
        skip = page * limit
        paginated_request = FindOrganizationRequest(sort_by="status", sort_direction="asc", limit=limit, skip=skip)
        paginated_response = OrganizationWithAdmins.find(paginated_request)

        paginated_organizations.extend(paginated_response.organizations)

    assert len(paginated_organizations) == total_count
    for org1, org2 in zip(paginated_organizations, full_response.organizations):
        assert org1.id == org2.id


def test_find_organization_with_admins(organization, organization_admin):
    find_request = FindOrganizationRequest(name=organization.name)
    find_response = OrganizationWithAdmins.find(find_request)

    assert find_response.organizations[0].admins[0].email == organization_admin.email.lower()


def test_find_organization_with_admins_filter_by_organization_id(organization, organization_admin):
    find_request = FindOrganizationRequest(id=organization.id)
    find_response = OrganizationWithAdmins.find(find_request)

    assert find_response.organizations[0].admins[0].email == organization_admin.email.lower()


def test_find_organization_with_admins_cant_find_by_partial_organization_id(organization, organization_admin):
    find_request = FindOrganizationRequest(id=str(organization.id)[: (len(str(organization.id)) // 2)])
    with pytest.raises(AccountServiceError) as excinfo:
        OrganizationWithAdmins.find(find_request)

    assert excinfo.value.status_code == http.HTTPStatus.BAD_REQUEST
    assert "" in excinfo.value.message


def test_find_organization_with_admins_filter_by_admin_email(organization, organization_admin):
    find_request = FindOrganizationRequest(name=organization_admin.email)
    find_response = OrganizationWithAdmins.find(find_request)

    assert find_response.organizations[0].admins[0].email == organization_admin.email.lower()


def test_find_organization_with_admins_filter_by_partial_admin_email(organization, organization_admin):
    find_request = FindOrganizationRequest(
        name=str(organization_admin.email)[: (len(str(organization_admin.email)) // 2)]
    )
    find_response = OrganizationWithAdmins.find(find_request)

    assert find_response.organizations[0].admins[0].email == organization_admin.email.lower()


def test_find_organization_with_admins_filter_by_admin_email_wrong_capitalization(organization, organization_admin):
    find_request = FindOrganizationRequest(name=organization_admin.email.upper())
    find_response = OrganizationWithAdmins.find(find_request)

    assert find_response.organizations[0].admins[0].email == organization_admin.email.lower()


def test_find_organization_with_admins_filter_by_partial_admin_email_wrong_capitalization(
    organization, organization_admin
):
    find_request = FindOrganizationRequest(
        name=str(organization_admin.email)[: (len(str(organization_admin.email)) // 2)].upper()
    )
    find_response = OrganizationWithAdmins.find(find_request)

    assert find_response.organizations[0].admins[0].email == organization_admin.email.lower()


def test_find_organization_with_admins_through_invitation(organization_invitation):
    org_from_invitation, user_from_invitation = organization_invitation

    assert len(org_from_invitation.admins) == 1
    assert org_from_invitation.admins[0].email == user_from_invitation.email

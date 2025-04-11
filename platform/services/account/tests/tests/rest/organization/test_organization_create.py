# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from models.error import AccountServiceError
from models.organization import Organization, OrganizationWithAdmins
from utils.data_gen import gen_random_str

from config.consts import DEFAULT_MAX_FIELD_SIZE, DEFAULT_SHORT_FIELD_SIZE


def test_create_organization(organization):
    assert organization.id != ""
    # TEST if works
    assert organization.created_at is not None
    assert organization.modified_at is None
    assert organization.modified_by == ""


def test_create_organization_only_required_fields():
    org = Organization(name=gen_random_str(), status="SSP")
    org.create()
    org.delete()


@pytest.mark.parametrize(
    ("field_name", "length_limit"),
    [
        ("name", DEFAULT_MAX_FIELD_SIZE),
        ("country", DEFAULT_SHORT_FIELD_SIZE),
        ("location", DEFAULT_MAX_FIELD_SIZE),
        ("type", DEFAULT_SHORT_FIELD_SIZE),
        ("cell_id", DEFAULT_MAX_FIELD_SIZE),
        ("status", DEFAULT_SHORT_FIELD_SIZE),
    ],
)
def test_create_organization_fields_length_limits(field_name, length_limit):
    org = Organization.randomize(**{field_name: gen_random_str(length_limit)})
    try:
        org.create()
    except AccountServiceError:
        assert False, f"Account Service failed on an non-oversized field: '{field_name}' with length: {length_limit}"
    finally:
        org.delete()

    length_exceeded = length_limit + 1
    org = Organization.randomize(**{field_name: gen_random_str(length_limit + 1)})
    try:
        org.create()
    except AccountServiceError:
        return
    assert False, f"Account Service didn't fail on oversized field: '{field_name}' with length: {length_exceeded}"


def test_create_organization_with_auth_token(user, signed_token):
    randomized_org = Organization.randomize()
    returned_org = randomized_org.create(headers={"x-auth-request-access-token": signed_token})
    assert returned_org.created_by == user.id

    org_from_get = OrganizationWithAdmins.get(returned_org.id)
    assert org_from_get.created_by == user.id

    randomized_org.delete()


def test_create_organization_with_request_access_reason():
    org = Organization(name=gen_random_str(), status="REQ", request_access_reason="test reason")
    created_org = org.create()

    assert created_org.request_access_reason == "test reason"
    assert created_org.status == "REQ"

    org.delete()

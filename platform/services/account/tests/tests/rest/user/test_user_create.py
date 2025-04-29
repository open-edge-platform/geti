# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import http
import json

import pytest
import requests
from fixtures.organization import organization
from models.error import AccountServiceError
from models.user import User
from utils.data_gen import gen_random_email, gen_random_str

from config.consts import DEFAULT_MAX_EMAIL_SIZE, DEFAULT_MAX_FIELD_SIZE, DEFAULT_SHORT_FIELD_SIZE
from config.env import account_service_grpc_gateway_address, api_v1_prefix, protocol


def test_create_user(user):
    assert user.id != ""
    # You can add more assertions specific to the User attributes here, e.g.
    assert user.first_name != ""
    assert user.email != ""


def test_create_user_email_conflict(user):
    user_with_same_email = User.randomize(organization_id=user.organization_id, email=user.email)

    try:
        user_with_same_email.create()
        assert False, "didn't raise exception!"
    except AccountServiceError as ex:
        assert ex.status_code == http.HTTPStatus.CONFLICT

    user.status = "DEL"
    user.modify()

    user_returned = user_with_same_email.create()

    assert user_returned.id != user.id
    assert user_returned.email == user.email


different_organization = organization


# noinspection PyShadowingNames
def test_create_user_email_different_organization(user, different_organization):
    user_with_same_email = User.randomize(organization_id=different_organization.id, email=user.email)

    user_returned = user_with_same_email.create()
    assert user_returned.id == user.id
    assert user_returned.email == user.email
    assert user_returned.organization_id != user.organization_id
    assert user_returned.organization_id == different_organization.id
    assert user_with_same_email.id == user.id

    user_in_first_org = User.get_by_id(user_with_same_email.id, organization_id=user.organization_id)
    user_in_different_org = User.get_by_id(user_with_same_email.id, organization_id=different_organization.id)
    assert user_in_first_org.id == user_in_different_org.id


def test_create_user_email_conflict_multiple_status_modify(user):
    user.status = "SSP"
    user.modify()

    user.status = "ACT"
    user.modify()

    user.status = "SSP"
    user.modify()

    user_with_same_email = User.randomize(organization_id=user.organization_id, email=user.email)

    try:
        user_with_same_email.create()
        assert False, "didn't raise exception!"
    except AccountServiceError as ex:
        assert ex.status_code == http.HTTPStatus.CONFLICT

    user.status = "DEL"
    user.modify()

    user_returned = user_with_same_email.create()

    assert user_returned.id != user.id
    assert user_returned.email == user.email
    assert user_returned.status == "ACT"


def test_create_user_missing_organization_id_in_body(organization):
    """Endpoint should work, when organization_id is in query parameter, but missing from the body."""
    user_payload = User.randomize(organization.id)
    user_payload.organization_id = None
    response = requests.post(
        f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{organization.id}/users",
        json=user_payload.to_json(),
    )

    response.raise_for_status()
    json_returned = json.loads(response.content)
    returned_user = User.from_json(json_returned)

    assert user_payload.first_name == returned_user.first_name
    assert organization.id == returned_user.organization_id
    returned_user.delete()


def test_create_user_only_required_fields(organization):
    user = User(email=f"{gen_random_str()}@example.com", status="ACT", organization_id=organization.id)
    user.create()
    user.delete()


@pytest.mark.parametrize(
    ("field_name", "length_limit"),
    [
        ("first_name", DEFAULT_MAX_FIELD_SIZE),
        ("second_name", DEFAULT_MAX_FIELD_SIZE),
        ("email", DEFAULT_MAX_EMAIL_SIZE),
        ("external_id", DEFAULT_MAX_FIELD_SIZE),
        ("country", DEFAULT_SHORT_FIELD_SIZE),
        ("status", DEFAULT_SHORT_FIELD_SIZE),
    ],
)
def test_create_user_fields_length_limits(organization, field_name, length_limit):
    user = User.randomize(
        **{
            "organization_id": organization.id,
            field_name: gen_random_str(length_limit) if field_name != "email" else gen_random_email(length_limit),
        }
    )
    try:
        user.create()
    except AccountServiceError:
        assert False, f"Account Service failed on an non-oversized field: '{field_name}' with length: {length_limit}"
    finally:
        user.delete()

    length_exceeded = length_limit + 1
    user = User.randomize(**{"organization_id": organization.id, field_name: gen_random_str(length_exceeded)})
    try:
        user.create()
    except AccountServiceError:
        return
    assert False, f"Account Service didn't fail on oversized field: '{field_name}' with length: {length_exceeded}"


def test_create_user_with_auth_token(user, signed_token, organization):
    randomized_user = User.randomize(organization.id)
    returned_user = randomized_user.create(headers={"x-auth-request-access-token": signed_token})
    assert returned_user.created_by == user.id

    org_from_get = User.get_by_id(returned_user.id, organization.id)
    assert org_from_get.created_by == user.id

    randomized_user.delete()

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import http

import pytest
from fixtures.organization import organization
from models.error import AccountServiceError
from models.user import GetUsersRequest, User

org0 = organization
org1 = organization
org2 = organization


def test_get_user(org0, org1, org2):
    user = User.randomize(organization_id=org1.id)
    user_returned = user.create()

    returned_user_from_get = User.get_by_id(user_returned.id, user_returned.organization_id)
    assert returned_user_from_get.id == user.id
    assert returned_user_from_get.organization_id == user.organization_id

    user.delete()


def test_get_user_by_external_id(user):
    # NOTE: This functionality only works for as long as user is assigned only to 1 organization, otherwise
    # unwanted organization might be returned due to lack of organization id while making a request
    returned_user = User.get_by_external_id(user.external_id)

    assert returned_user.external_id == user.external_id
    assert returned_user.id == user.id
    assert returned_user.email == user.email.lower()


def test_get_user_by_external_id_worst_chars_in_ext_id(organization):
    # check if get by external id works with '/' , '+', '=' in external id
    user = User.randomize(organization_id=organization.id, external_id="Z2R/mYmZiZmdaiZmdiZm+diZmdnZw==")
    user_returned = user.create()

    returned_user = User.get_by_external_id(user.external_id)

    assert returned_user.external_id == user.external_id
    assert returned_user.id == user.id
    assert returned_user.email == user.email.lower()

    user_returned.delete()


# it is executed multiple times because in case of fixed bug, the test could return false positive,
# depending which record db randomly returned
@pytest.mark.parametrize("dummy_parameter_to_execute_test_multiple_times", range(10))
def test_get_user_by_external_id_del_user(user, recreated_user, dummy_parameter_to_execute_test_multiple_times):
    returned_user = User.get_by_external_id(recreated_user.external_id)

    assert returned_user.external_id == recreated_user.external_id
    assert returned_user.id == recreated_user.id
    assert returned_user.email == recreated_user.email.lower()


def test_get_active_user(user, signed_token):
    returned_user = User.get_active_user(user.organization_id, signed_token)
    assert returned_user is not None
    assert returned_user.id == user.id


def test_get_user_profile(user, signed_token):
    user.user_consent = "y"
    user.telemetry_consent = "y"
    user.modify()

    returned_user_profile = User.get_user_profile(signed_token)

    assert returned_user_profile is not None
    assert returned_user_profile.user_consent == user.user_consent
    assert returned_user_profile.user_consent_at is not None
    assert returned_user_profile.telemetry_consent == user.telemetry_consent
    assert returned_user_profile.telemetry_consent_at is not None

    for org in returned_user_profile.organizations:
        if org.organization_id == user.organization_id:
            assert org.organization_status == user.organization_status
            assert org.organization_created_at is not None and org.organization_created_at != ""
            break
    else:
        assert False, "Did not find matching organization id"


def test_get_user_profile_invalid_user(signed_token_invalid_user):
    try:
        User.get_user_profile(signed_token_invalid_user)
        pytest.fail("did not return error")
    except AccountServiceError as err:
        assert err.status_code == http.HTTPStatus.NOT_FOUND
        assert err.message == "User not found"


def test_get_user_profile_missing_external_token(user, invalid_token_missing_external):
    try:
        User.get_user_profile(invalid_token_missing_external)
        pytest.fail("did not return error")
    except AccountServiceError as err:
        assert err.status_code == http.HTTPStatus.BAD_REQUEST
        assert err.message == "Invalid request"


def test_get_user_profile_missing_email(user, invalid_token_missing_email):
    try:
        User.get_user_profile(invalid_token_missing_email)
        pytest.fail("did not return error")
    except AccountServiceError as err:
        assert err.status_code == http.HTTPStatus.BAD_REQUEST
        assert err.message == "Invalid request"


def test_get_user_profile_with_multiple_user_statuses(registered_user, registred_user_signed_token):
    # the test is executed for multiple statuses because for 1-2 statuses it might return false positive
    statuses_flow = ("ACT", "SSP", "ACT", "SSP")

    for status in statuses_flow:
        registered_user.status = status
        registered_user.modify()
        returned_user_profile = User.get_user_profile(registred_user_signed_token)

        assert returned_user_profile is not None
        for org in returned_user_profile.organizations:
            assert org.user_status == status

    # for 'DEL' status expect Not Found
    registered_user.status = "DEL"
    registered_user.modify()
    try:
        User.get_user_profile(registred_user_signed_token)
        pytest.fail("did not raise error")
    except AccountServiceError as err:
        assert err.status_code == http.HTTPStatus.NOT_FOUND


# it is executed multiple times because in case of fixed bug, the test could return false positive,
# depending which record db randomly returned
@pytest.mark.parametrize("dummy_parameter_to_execute_test_multiple_times", range(10))
def test_get_user_profile_multiple_users_with_same_email(
    recreated_user, signed_token, dummy_parameter_to_execute_test_multiple_times
):
    returned_user_profile = User.get_user_profile(signed_token)

    for org in returned_user_profile.organizations:
        if org.organization_id == recreated_user.organization_id:
            assert org.user_status == recreated_user.status
            break
    else:
        assert False, "Did not find matching organization id"


# it is executed multiple times because in case of fixed bug, the test could return false positive,
# depending which record db randomly returned
@pytest.mark.parametrize("dummy_parameter_to_execute_test_multiple_times", range(10))
def test_get_user_profile_multiple_users_with_same_email_but_different_org(
    recreated_user_in_different_organization, signed_token, dummy_parameter_to_execute_test_multiple_times
):
    returned_user_profile = User.get_user_profile(signed_token)

    for org in returned_user_profile.organizations:
        if org.organization_id == recreated_user_in_different_organization.organization_id:
            assert org.user_status == recreated_user_in_different_organization.status
            assert org.organization_status == recreated_user_in_different_organization.organization_status
            break
    else:
        assert False, "Did not find matching organization id"


def test_get_user_with_multiple_user_statuses(org0, org1, org2):
    user = User.randomize(organization_id=org1.id, status="RGS")
    user_returned = user.create()

    try:
        user_returned.status = "ACT"
        user_returned.modify()

        user_returned.status = "SSP"
        user_returned.modify()

        returned_user_from_get = User.get_by_id(user_returned.id, user_returned.organization_id)
        assert returned_user_from_get.id == user.id
        assert returned_user_from_get.organization_id == user.organization_id
        assert user_returned.status == "SSP"
    finally:
        user.delete()


def test_get_users(org0):
    req = GetUsersRequest()
    user = User.randomize(organization_id=org0.id)
    user.create()

    try:
        returned_users = User.get_users_list(req)
        assert len(returned_users.users) >= 1
    finally:
        user.delete()


def test_get_users_filters(org2):
    user = User.randomize(organization_id=org2.id)
    user.create()
    req = GetUsersRequest(first_name=user.first_name)

    try:
        returned_users = User.get_users_list(req)
        for user_result in returned_users.users:
            assert user_result.first_name == user.first_name
    finally:
        user.delete()


def test_get_users_filters_name(org2):
    user = User.randomize(organization_id=org2.id)
    user.create()
    req = GetUsersRequest(name=user.first_name)

    try:
        returned_users = User.get_users_list(req)
        for user_result in returned_users.users:
            assert user_result.first_name == user.first_name
    finally:
        user.delete()


def test_get_users_invalid_argument():
    get_request = GetUsersRequest(sort_by="first_name", sort_direction="Invalid")

    try:
        User.get_users_list(get_request)
        assert False, "Expected an AccountServiceError but got a response"
    except AccountServiceError as e:
        assert e.args[0] == "Wrong sort direction"

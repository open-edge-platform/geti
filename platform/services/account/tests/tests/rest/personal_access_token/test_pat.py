# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import hashlib
import http
from datetime import datetime, timedelta

import models.error
import pytest
from models.personal_access_token import (
    PersonalAccessToken,
    PersonalAccessTokenCreateRequest,
    PersonalAccessTokenCreateResponse,
    PersonalAccessTokenExtendRequest,
    PersonalAccessTokenFindRequest,
)
from utils.data_gen import gen_random_str


def to_base62(number):
    base62_chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if number == 0:
        return "0"
    result = []
    while number > 0:
        number, remainder = divmod(number, 62)
        result.append(base62_chars[remainder])
    return "".join(reversed(result))


def _create_pat(user, token_validity: timedelta = timedelta(hours=24)) -> PersonalAccessTokenCreateResponse:
    request = PersonalAccessTokenCreateRequest(
        organization_id=user.organization_id,
        user_id=user.id,
        created_by=user.created_by,
        name=gen_random_str(),
        description=gen_random_str(100),
        expires_at=datetime.utcfromtimestamp(int(datetime.timestamp(datetime.now() + token_validity))).isoformat()
        + "Z",
    )
    response: PersonalAccessTokenCreateResponse = PersonalAccessToken.create(request)
    return response


def _create_pat_um(
    user, signed_token: str, token_validity: timedelta = timedelta(hours=24)
) -> PersonalAccessTokenCreateResponse:
    request = PersonalAccessTokenCreateRequest(
        organization_id=user.organization_id,
        created_by=user.created_by,
        name=gen_random_str(),
        description=gen_random_str(100),
        expires_at=datetime.utcfromtimestamp(int(datetime.timestamp(datetime.now() + token_validity))).isoformat()
        + "Z",
    )
    response: PersonalAccessTokenCreateResponse = PersonalAccessToken.create(
        request, headers={"x-auth-request-access-token": signed_token}
    )

    return response


def _make_hash(pat: str) -> str:
    sha384_hash = hashlib.sha384(pat.encode("utf-8")).digest()
    pat_number = int.from_bytes(sha384_hash, byteorder="big")
    base62_hash = to_base62(pat_number)
    padded_hash = base62_hash.zfill(65)
    return padded_hash


def test_make_hash():
    pat = "geti_pat_zS7MrC1KWkHv28xPf3stTaep0y6PTblNX6V9nEcF8JM_2kuuLA"
    expected_hash = "3VGvMyLPT98vWyac4XQQmfLVRkOyqLE5u6K1lgYkDkaKPPdPlq9cXYm3PX4B9pNgs"

    assert expected_hash == _make_hash(pat)


def test_create_personal_access_token(user, signed_token):
    response = _create_pat(user)
    # uncomment if the FEATURE_FLAG_ACC_SVC_MOD is enabled
    # response = _create_pat_um(user, signed_token)

    assert response.id is not None
    assert response.personal_access_token != ""
    assert response.created_at != ""


def test_create_expired_personal_access_token(user, signed_token):
    with pytest.raises(models.error.AccountServiceError) as ex:
        _create_pat_um(user, signed_token=signed_token, token_validity=timedelta(seconds=-3))

    account_service_error: models.error.AccountServiceError = ex.value
    assert account_service_error.status_code == http.HTTPStatus.BAD_REQUEST
    assert account_service_error.message == "expiration date from the past"


def test_get_pat_by_hash(user, signed_token):
    created_pat = _create_pat(user)
    # uncomment if the FEATURE_FLAG_ACC_SVC_MOD is enabled
    # created_pat = _create_pat_um(user, signed_token)
    pat_hash = _make_hash(created_pat.personal_access_token)

    response = PersonalAccessToken.get_by_hash(pat_hash)

    assert response.partial == created_pat.partial
    assert response.created_at == created_pat.created_at
    assert response.name == created_pat.name


def test_get_org_from_token(user, signed_token):
    response = PersonalAccessToken.get_org_from_token(signed_token)
    assert response == user.organization_id


def test_find_pat(user, signed_token):
    pat = _create_pat(user)
    # uncomment if the FEATURE_FLAG_ACC_SVC_MOD is enabled
    # pat = _create_pat_um(user, signed_token)

    result = PersonalAccessToken.find(pat.organization_id, pat.user_id)

    assert len(result.personal_access_tokens) == 1
    returned_token = result.personal_access_tokens[0]
    assert returned_token.organization_id == pat.organization_id
    assert returned_token.user_id == pat.user_id
    assert returned_token.partial == pat.partial


@pytest.mark.parametrize("attribute_to_find_by", ("name", "description", "partial"))
def test_find_pat_by_simple_atrributes(user, attribute_to_find_by, signed_token):
    pats = []
    for _ in range(10):
        pat = _create_pat(user)
        # uncomment if the FEATURE_FLAG_ACC_SVC_MOD is enabled
        # pat = _create_pat_um(user, signed_token)
        pats.append(pat)

    pat_expected = pats[3]

    find_by = {attribute_to_find_by: getattr(pat_expected, attribute_to_find_by)}

    find_request = PersonalAccessTokenFindRequest(**find_by)

    result = PersonalAccessToken.find(pat_expected.organization_id, pat_expected.user_id, find_request)

    assert len(result.personal_access_tokens) == 1
    returned_token = result.personal_access_tokens[0]
    assert returned_token.organization_id == pat_expected.organization_id
    assert returned_token.user_id == pat_expected.user_id
    assert returned_token.partial == pat_expected.partial


def test_find_pat_by_expiration(user, signed_token):
    pats = []
    for _ in range(10):
        pat = _create_pat(user)
        # uncomment if the FEATURE_FLAG_ACC_SVC_MOD is enabled
        # pat = _create_pat_um(user, signed_token)
        pats.append(pat)

    pat_expected = pats[3]

    expiration_expected = datetime.now() + timedelta(days=1)

    find_request = PersonalAccessTokenFindRequest(
        expires_at_from=datetime.now().isoformat() + "Z", expires_at_to=expiration_expected.isoformat() + "Z"
    )

    result = PersonalAccessToken.find(pat_expected.organization_id, pat_expected.user_id, find_request)

    assert len(result.personal_access_tokens) == 10


def test_find_pat_sort(user, signed_token):
    pats = []
    for _ in range(10):
        pat = _create_pat(user)
        # uncomment if the FEATURE_FLAG_ACC_SVC_MOD is enabled
        # pat = _create_pat_um(user, signed_token)
        pats.append(pat)

    pats_sorted_by_name = sorted(pats, key=lambda token: str.lower(token.name), reverse=True)

    find_request = PersonalAccessTokenFindRequest(sort_by="name", sort_direction="desc")

    result = PersonalAccessToken.find(pats[0].organization_id, pats[0].user_id, find_request)

    assert len(result.personal_access_tokens) == 10
    for i in range(len(pats_sorted_by_name)):
        assert pats_sorted_by_name[i].name == result.personal_access_tokens[i].name


def test_find_pat_multiple_results(user, signed_token):
    _create_pat(user)
    _create_pat(user)
    _create_pat(user)

    # uncomment if the FEATURE_FLAG_ACC_SVC_MOD is enabled
    # _create_pat_um(user, signed_token)
    # _create_pat_um(user, signed_token)
    # _create_pat_um(user, signed_token)

    result = PersonalAccessToken.find(user.organization_id, user.id)

    assert len(result.personal_access_tokens) == 3
    assert result.personal_access_tokens[0].organization_id == user.organization_id
    assert result.personal_access_tokens[0].user_id == user.id


def test_call_get_by_hash_nonexisting_pat(user, signed_token):
    _create_pat(user)  # populate with some hashes
    _create_pat(user)  # populate with some hashes

    # uncomment if the FEATURE_FLAG_ACC_SVC_MOD is enabled
    # _create_pat_um(user, signed_token)  # populate with some hashes
    # _create_pat_um(user, signed_token)  # populate with some hashes

    wrong_hash = _make_hash("geti_pat_YHrvXVKzFoLhpFcHxSQaalwTOHTzRjrQEhdo9jGiGDP_3N5dIs")
    assert "_" not in wrong_hash

    try:
        response = PersonalAccessToken.get_by_hash(wrong_hash)
        assert False, f"Test should fail, received response {vars(response)}"
    except models.error.AccountServiceError as acc_err:
        assert acc_err.status_code == 404
        assert wrong_hash in acc_err.message
        assert "not found" in acc_err.message


def test_revoke_pat(user, signed_token):
    created_pat = _create_pat(user)
    # uncomment if the FEATURE_FLAG_ACC_SVC_MOD is enabled
    # created_pat = _create_pat_um(user, signed_token)
    result_before_revoke = PersonalAccessToken.find(user.organization_id, user.id)
    revoke_result = PersonalAccessToken.revoke(
        created_pat.organization_id,
        created_pat.user_id,
        created_pat.id,
        headers={"x-auth-request-access-token": signed_token},
    )
    result_after_revoke = PersonalAccessToken.find(user.organization_id, user.id)

    assert revoke_result.status_code == http.HTTPStatus.OK
    assert len(result_before_revoke.personal_access_tokens) - 1 == len(result_after_revoke.personal_access_tokens)


def test_extend_pat(user, signed_token):
    created_pat = _create_pat(user)
    # uncomment if the FEATURE_FLAG_ACC_SVC_MOD is enabled
    # created_pat = _create_pat_um(user, signed_token)

    new_timestamp = (
        datetime.utcfromtimestamp(int(datetime.timestamp(datetime.now() + timedelta(hours=48)))).isoformat() + "Z"
    )
    extension_request = PersonalAccessTokenExtendRequest(
        created_pat.organization_id, created_pat.user_id, created_pat.id, new_timestamp
    )

    result = PersonalAccessToken.extend(extension_request, headers={"x-auth-request-access-token": signed_token})

    time_before = datetime.strptime(created_pat.expires_at, "%Y-%m-%dT%H:%M:%SZ")
    time_after = datetime.strptime(result.expires_at, "%Y-%m-%dT%H:%M:%SZ")

    assert result.partial == created_pat.partial
    assert (
        (time_after - time_before).total_seconds() / 3600
    ) > 23  # checks if it got extended from today + 24h to today + 48h

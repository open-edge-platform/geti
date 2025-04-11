# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import datetime
import http

from models.error import AccountServiceError
from models.personal_access_token import PersonalAccessToken, PersonalAccessTokenCreateRequest
from models.user import User
from utils.data_gen import gen_random_str


def test_modify_user_with_auth_token(user, signed_token, organization):
    user.second_name = "fake-surname"
    returned_user = user.modify(headers={"x-auth-request-access-token": signed_token})
    assert returned_user.modified_by == user.id

    org_from_get = User.get_by_id(returned_user.id, organization.id)
    assert org_from_get.modified_by == user.id


def test_update_user(user):
    fake_new_email = f"{gen_random_str()}@example.com"
    user.email = fake_new_email
    user.modify()

    returned_user = User.get_by_id(user.id, user.organization_id)
    assert user.email.lower() == returned_user.email


def test_update_user_telemetry(user):
    user.telemetry_consent = "n"
    user.user_consent = "n"
    user.modify()

    returned_user = User.get_by_id(user.id, user.organization_id)
    assert user.user_consent == returned_user.user_consent
    assert returned_user.user_consent_at is not None


def test_update_user_with_changed_status(user):
    user.status = "DEL"
    user.modify()

    returned_user = User.get_by_id(user.id, user.organization_id)
    assert user.status == returned_user.status


def test_update_user_with_changed_status_with_pat(user):
    pat_req = PersonalAccessTokenCreateRequest(
        organization_id=user.organization_id,
        user_id=user.id,
        created_by=user.created_by,
        name=gen_random_str(),
        description=gen_random_str(100),
        expires_at=datetime.datetime.utcfromtimestamp(
            int(datetime.datetime.timestamp(datetime.datetime.now() + (datetime.timedelta(hours=24))))
        ).isoformat()
        + "Z",
    )
    PersonalAccessToken.create(pat_req)
    user.status = "DEL"
    user.modify()
    returned_pat = PersonalAccessToken.find(user.organization_id, user.id)

    returned_user = User.get_by_id(user.id, user.organization_id)
    assert user.status == returned_user.status
    assert len(returned_pat.personal_access_tokens) == 0


def test_cannot_set_deleted_user_on_single_org_admin(organization_admin):
    organization_admin.status = "DEL"
    try:
        organization_admin.modify()
    except AccountServiceError as ex:
        assert ex.status_code == http.HTTPStatus.BAD_REQUEST
        assert ex.message == "You cannot remove the last admin in the organization."
    else:
        assert False, "no exception raised when expected"


def test_set_deleted_user_on_single_org_admin_rgs_org(organization, organization_admin):
    organization.status = "RGS"
    organization.modify()

    organization_admin.status = "DEL"
    organization_admin.modify()
    returned_user = User.get_by_id(organization_admin.id, organization.id)

    assert returned_user.status == organization_admin.status

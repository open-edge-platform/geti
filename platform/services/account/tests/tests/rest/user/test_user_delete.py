# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import datetime

from models.personal_access_token import PersonalAccessToken, PersonalAccessTokenCreateRequest
from models.user import User
from utils.data_gen import gen_random_str


def test_delete_user(user):
    new_user = User(
        first_name=gen_random_str(),
        second_name=gen_random_str(),
        email=f"{gen_random_str()}@example.com",
        external_id=gen_random_str(),
        organization_id=user.organization_id,
        country="USA",
        status="ACT",
    )
    new_user.create()
    new_user.delete()

    assert User.get_by_id(new_user.id, new_user.organization_id) is None


def test_delete_user_with_pat(organization):
    new_user = User.randomize(organization.id)
    new_user.create()
    pat_req = PersonalAccessTokenCreateRequest(
        organization_id=new_user.organization_id,
        user_id=new_user.id,
        created_by=new_user.created_by,
        name=gen_random_str(),
        description=gen_random_str(100),
        expires_at=datetime.datetime.utcfromtimestamp(
            int(datetime.datetime.timestamp(datetime.datetime.now() + (datetime.timedelta(hours=24))))
        ).isoformat()
        + "Z",
    )
    PersonalAccessToken.create(pat_req)
    new_user.delete()
    returned_pat = PersonalAccessToken.find(new_user.organization_id, new_user.id)

    assert User.get_by_id(new_user.id, new_user.organization_id) is None
    assert len(returned_pat.personal_access_tokens) == 0

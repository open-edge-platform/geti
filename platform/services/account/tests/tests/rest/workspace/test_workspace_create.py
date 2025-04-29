# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import json

import pytest
import requests
from models.error import AccountServiceError
from models.workspace import Workspace
from utils.data_gen import gen_random_str

from config.consts import DEFAULT_MAX_FIELD_SIZE
from config.env import account_service_grpc_gateway_address, api_v1_prefix, protocol


def test_create_workspace(workspace):
    assert workspace.id != ""
    # TEST if works
    assert workspace.created_at is not None
    assert workspace.modified_at is None
    assert workspace.modified_by == ""


def test_create_workspace_missing_organization_id_in_body(organization):
    """Endpoint should work, when organization_id is in query parameter, but missing from the body."""
    payload = {"name": "dummy_workspace"}
    response = requests.post(
        f"{protocol}{account_service_grpc_gateway_address}{api_v1_prefix}/organizations/{organization.id}/workspaces",
        json=payload,
    )

    response.raise_for_status()
    json_returned = json.loads(response.content)
    returned_workspace = Workspace.from_json(json_returned)

    assert payload["name"] == returned_workspace.name
    assert organization.id == returned_workspace.organization_id
    returned_workspace.delete()


@pytest.mark.parametrize(
    ("field_name", "length_limit"),
    [
        ("name", DEFAULT_MAX_FIELD_SIZE),
    ],
)
def test_create_workspace_fields_length_limits(organization, field_name, length_limit):
    workspace = Workspace.randomize(
        **{
            "organization_id": organization.id,
            field_name: gen_random_str(length_limit),
        }
    )
    try:
        workspace.create()
    except AccountServiceError:
        assert False, f"Account Service failed on an non-oversized field: '{field_name}' with length: {length_limit}"
    finally:
        workspace.delete()

    length_exceeded = length_limit + 1
    workspace = Workspace.randomize(**{"organization_id": organization.id, field_name: gen_random_str(length_exceeded)})
    try:
        workspace.create()
    except AccountServiceError:
        return
    assert False, f"Account Service didn't fail on oversized field: '{field_name}' with length: {length_exceeded}"


def test_create_workspace_with_auth_token(user, signed_token, organization):
    randomized_workspace = Workspace.randomize(organization.id)
    returned_user = randomized_workspace.create(headers={"x-auth-request-access-token": signed_token})
    assert returned_user.created_by == user.id

    workspace_from_get = Workspace.get(returned_user.id, organization.id)
    assert workspace_from_get.created_by == user.id

    randomized_workspace.delete()

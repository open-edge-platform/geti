# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from models.workspace import Workspace


def test_modify_user_with_auth_token(user, signed_token, workspace):
    workspace.name = "some-new-name"
    returned_workspace = workspace.update(headers={"x-auth-request-access-token": signed_token})
    assert returned_workspace.modified_by == user.id

    workspace_from_get = Workspace.get(returned_workspace.id, workspace.organization_id)
    assert workspace_from_get.modified_by == user.id


def test_update_workspace(workspace):
    fake_new_name = "fake-new-name"
    workspace.name = fake_new_name
    workspace.update()

    returned_workspace = workspace.get(workspace.id, workspace.organization_id)
    returned_workspace.modified_at = None
    assert workspace == returned_workspace

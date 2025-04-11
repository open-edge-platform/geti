# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from models.workspace import Workspace
from utils.data_gen import gen_random_str


def test_delete_workspace(organization):
    workspace = Workspace(name=gen_random_str(), organization_id=organization.id)
    workspace.create()
    workspace.delete()

    assert workspace.get(workspace.id, workspace.organization_id) is None

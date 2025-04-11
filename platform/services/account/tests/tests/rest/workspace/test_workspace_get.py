# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from models.workspace import Workspace


def test_get_workspace(workspace):
    returned_org_from_get = Workspace.get(workspace.id, workspace.organization_id)
    assert returned_org_from_get == workspace

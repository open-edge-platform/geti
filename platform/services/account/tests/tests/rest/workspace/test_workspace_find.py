# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from fixtures.workspace import workspace
from models.workspace import FindWorkspaceRequest, Workspace

workspace1 = workspace
workspace2 = workspace


def test_find_workspaces(workspace: Workspace, workspace1: Workspace, workspace2: Workspace):
    find_request = FindWorkspaceRequest(name=workspace1.name)
    find_response = workspace.find(workspace1.organization_id, find_request)
    requested_workspaces = [workspace1]
    assert find_response.workspaces == requested_workspaces
    assert find_response.total_count > 3
    assert find_response.total_matched_count == 1

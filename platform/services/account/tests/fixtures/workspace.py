# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from models.workspace import Workspace


@pytest.fixture
def workspace(organization):
    workspace = Workspace.randomize(organization_id=organization.id)
    workspace_returned = workspace.create()
    yield workspace_returned
    workspace.delete()

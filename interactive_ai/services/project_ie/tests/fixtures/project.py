# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Project-related fixtures"""

from datetime import datetime, timezone

import pytest

from geti_types import ProjectIdentifier
from sc_sdk.entities.dataset_storage import NullDatasetStorage
from sc_sdk.entities.project import Project
from sc_sdk.entities.task_graph import TaskGraph


@pytest.fixture
def fxt_project_identifier_1(fxt_workspace_id, fxt_ote_id):
    yield ProjectIdentifier(
        workspace_id=fxt_workspace_id,
        project_id=fxt_ote_id(1),
    )


@pytest.fixture
def fxt_project_identifier_2(fxt_workspace_id, fxt_ote_id):
    yield ProjectIdentifier(
        workspace_id=fxt_workspace_id,
        project_id=fxt_ote_id(2),
    )


@pytest.fixture
def fxt_project_identifier(fxt_project_identifier_1):
    yield fxt_project_identifier_1


@pytest.fixture
def fxt_project(fxt_project_identifier):
    yield Project(
        name="dummy_empty_project",
        creator_id="",
        description="dummy empty project",
        dataset_storages=[NullDatasetStorage()],
        task_graph=TaskGraph(),
        id=fxt_project_identifier.project_id,
        creation_date=datetime.strptime("01/01/1970 00:00:01", "%d/%m/%Y %H:%M:%S").astimezone(timezone.utc),
        user_names=["test_username"],
    )

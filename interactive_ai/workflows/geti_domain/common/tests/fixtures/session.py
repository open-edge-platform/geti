# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os
from datetime import datetime

import pytest
from bson import ObjectId
from geti_types import ID, make_session, session_context

from jobs_common.tasks.utils.secrets import JobMetadata


@pytest.fixture
def fxt_organization_id():
    yield ID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def fxt_workspace_id():
    return ID("00000000-0000-0000-0000-000000000002")


@pytest.fixture(autouse=True)
def fxt_session_ctx(fxt_organization_id, fxt_workspace_id):
    session = make_session(
        organization_id=fxt_organization_id,
        workspace_id=fxt_workspace_id,
    )
    with session_context(session=session):
        yield session


@pytest.fixture(autouse=True)
def fxt_job_metadata():
    job_id = str(ObjectId())
    job_type = "dummy_job_type"
    job_name = "dummy_job_name"
    job_author = str(ObjectId())
    job_start_time = datetime.now()
    session_env_vars = {
        "JOB_METADATA_ID": job_id,
        "JOB_METADATA_TYPE": job_type,
        "JOB_METADATA_NAME": job_name,
        "JOB_METADATA_AUTHOR": job_author,
        "JOB_METADATA_START_TIME": job_start_time.isoformat(),
    }
    os.environ.update(session_env_vars)

    yield JobMetadata(
        id=job_id,
        type=job_type,
        name=job_name,
        author=job_author,
        start_time=job_start_time,
    )

    for key in session_env_vars:
        os.environ.pop(key)

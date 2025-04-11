# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.
import os
from datetime import datetime

import pytest
from bson import ObjectId
from geti_types import ID
from jobs_common.tasks.utils.secrets import JobMetadata


@pytest.fixture
def fxt_mongo_id():
    """
    Create a realistic MongoDB ID string for testing purposes.

    If you need multiple ones, call this fixture repeatedly with different arguments.
    """
    base_id: int = 0x60D31793D5F1FB7E6E3C1A4F

    def _build_id(offset: int = 0) -> str:
        return str(hex(base_id + offset))[2:]

    yield _build_id


@pytest.fixture
def fxt_ote_id(fxt_mongo_id):
    """
    Create a realistic OTE ID for testing purposes. Based on the fxt_mongo_id, but this
    fixture returns an actual ID entity instead of a string.
    """

    def _build_ote_id(offset: int = 0) -> ID:
        return ID(fxt_mongo_id(offset))

    yield _build_ote_id


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

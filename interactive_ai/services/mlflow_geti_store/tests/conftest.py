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

import json
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pytest
from mlflow_geti_store.utils import PYARROW_SCHEMA


@pytest.fixture(scope="module")
def fxt_organization_id() -> str:
    return "00001"


@pytest.fixture(scope="module")
def fxt_workspace_id() -> str:
    return "00002"


@pytest.fixture(scope="module")
def fxt_project_id() -> str:
    return "00003"


@pytest.fixture(scope="module")
def fxt_job_id() -> str:
    return "00004"


@pytest.fixture(scope="module")
def fxt_start_time():
    return datetime.now(tz=timezone.utc)


@pytest.fixture()
def fxt_project_json(tmpdir, fxt_project_id, fxt_workspace_id, fxt_organization_id, fxt_start_time):
    fpath = tmpdir / "project.json"
    obj = {
        "id": fxt_project_id,
        "name": "project_name",
        "creator_id": "project_creator",
        "description": "project_description",
        "creation_date": fxt_start_time.isoformat(),
        "workspace_id": fxt_workspace_id,
        "organization_id": fxt_organization_id,
    }
    with open(fpath, "w") as fp:
        json.dump(obj, fp)

    yield fpath


@pytest.fixture()
def fxt_run_info_json(tmpdir, fxt_job_id, fxt_start_time):
    fpath = tmpdir / "run_info.json"
    obj = {
        "run_uuid": fxt_job_id,
        "job_name": "job_name",
        "author": "job_author",
        "status": "SCHEDULED",
        "start_time": fxt_start_time.isoformat(),
        "end_time": "",
        "lifecycle_stage": "ACTIVE",
    }

    with open(fpath, "w") as fp:
        json.dump(obj, fp)

    yield fpath


@pytest.fixture()
def fxt_live_metrics(tmpdir: Path):
    root_dir = tmpdir / "live_metrics"
    root_dir.mkdir()
    fpath = root_dir / "metrics.arrow"

    keys = ["car", "cat", "dog"]

    with pa.ipc.new_file(
        fpath,
        schema=PYARROW_SCHEMA,
        options=pa.ipc.IpcWriteOptions(use_threads=False),
    ) as writer:
        table = pa.Table.from_pylist(
            [
                {
                    "key": key,
                    "value": 10 - idx,  # Reversed
                    "step": idx,
                    "timestamp": idx,
                }
                for idx in range(10)
                for key in keys
            ],
            schema=PYARROW_SCHEMA,
        )
        writer.write_table(table)

    yield fpath

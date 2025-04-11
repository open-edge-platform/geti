# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.


import os
from pathlib import Path

import pytest

from scripts.mlflow_io import AsyncCaller


@pytest.fixture
def fxt_dir_assets() -> Path:
    return Path(__file__).parent / "assets"


@pytest.fixture(autouse=True)
def fxt_model_templates_dir(tmpdir):
    os.environ["MODEL_TEMPLATES_DIR"] = str(tmpdir)
    yield
    os.environ.pop("MODEL_TEMPLATES_DIR")


@pytest.fixture(autouse=True)
def fxt_shard_files_dir(tmpdir):
    os.environ["SHARD_FILES_DIR"] = str(tmpdir)
    yield
    os.environ.pop("SHARD_FILES_DIR")


@pytest.fixture(autouse=True)
def fxt_async_caller():
    AsyncCaller().start()
    yield
    AsyncCaller().close()

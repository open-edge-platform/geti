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
"""
This module tests the data repo
"""

from unittest.mock import patch

import pytest
from geti_types import ID

from job.repos.data_repo import ImportDataRepo
from job.utils.exceptions import FileNotFoundException


@pytest.mark.JobsComponent
class TestDataRepo:
    """
    Unit tests for the ImportDataRepo
    """

    def test_import_data_repo__unzip_dataset__file_not_found(self, fxt_import_data_repo: ImportDataRepo):
        import_id = ID()

        with patch("job.repos.data_repo.safely_unzip", side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundException):
                fxt_import_data_repo.unzip_dataset(import_id)

    def test_import_data_repo__load_and_transform_dataset__file_not_found(self, fxt_import_data_repo: ImportDataRepo):
        import_id = ID()
        with patch("job.repos.data_repo.json.load", side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundException):
                fxt_import_data_repo.load_and_transform_dataset(import_id)

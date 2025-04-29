# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""This module tests commands to create task train dataset"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from jobs_common_extras.shard_dataset.commands.upload_shard_file_command import UploadShardFileCommand


@pytest.mark.JobsComponent
class TestUploadShardFileCommand:
    @pytest.fixture
    def fxt_fpath(self, tmp_path: Path) -> str:
        fpath = tmp_path / "TRAINING-0-of-3.arrow"

        with fpath.open("wb") as fp:
            fp.write(b"Nobody inspects the spammish repetition")

        return str(fpath)

    @patch("jobs_common_extras.mlflow.adapters.geti_otx_interface.MLFlowExperimentBinaryRepo")
    def test_upload_shard_file_command(
        self,
        mock_mlflow_binary_repo,
        fxt_mongo_id,
        fxt_project_identifier,
        fxt_job_metadata,
        fxt_fpath: str,
    ) -> None:
        # Arrange
        dataset_id = fxt_mongo_id(1003)

        # Act
        command = UploadShardFileCommand(
            dataset_id,
            project_identifier=fxt_project_identifier,
            fpath=fxt_fpath,
        )

        command.execute()

        # Assert
        # Calling save
        mock_mlflow_binary_repo.return_value.save_group.assert_called_once()

        # File removal after uploading
        assert not os.path.exists(fxt_fpath)

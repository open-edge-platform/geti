# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging
import os
from pathlib import Path

from geti_telemetry_tools import unified_tracing
from geti_types import ProjectIdentifier

from jobs_common.commands.interfaces.command import ICommand
from jobs_common.exceptions import DataShardCreationFailedException
from jobs_common.tasks.utils.secrets import JobMetadata
from jobs_common_extras.mlflow.adapters.geti_otx_interface import GetiOTXInterfaceAdapter

logger = logging.getLogger(__name__)


class UploadShardFileCommand(ICommand):
    """Upload a shard file .

    :param dataset_id: ID of Dataset to shard
    :param project_identifier: Project identifier
    :param fpath: File path of the shard file to upload
    """

    def __init__(self, dataset_id: str, project_identifier: ProjectIdentifier, fpath: str) -> None:
        super().__init__()
        self.dataset_id = dataset_id
        self.project_identifier = project_identifier
        self.fpath = fpath
        self._binary_filename: str | None = None
        self._otx_api_adapter = GetiOTXInterfaceAdapter(
            project_identifier=self.project_identifier, job_metadata=JobMetadata.from_env_vars()
        )

    @unified_tracing
    def execute(self) -> None:
        try:
            self._otx_api_adapter.push_input_dataset(shard_file_local_path=Path(self.fpath))
            self._binary_filename = os.path.basename(self.fpath)
        except Exception as exc:
            logger.exception(f"Could not upload a dataset shard file for Dataset[id={self.dataset_id}]")
            raise DataShardCreationFailedException from exc
        finally:
            try:
                os.remove(self.fpath)
            except FileNotFoundError:
                logger.warning(f"No shard file to remove at path {self.fpath}")
            except OSError:
                logger.exception(f"Failed to clean-up shard file at path {self.fpath}")

    @property
    def binary_filename(self) -> str:
        """Filename of the uploaded shard file in BinaryRepo"""
        if self._binary_filename is None:
            raise RuntimeError("Please do execute() first")

        return self._binary_filename

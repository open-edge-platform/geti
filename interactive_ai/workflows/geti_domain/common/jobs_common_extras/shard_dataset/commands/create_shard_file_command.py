# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module defines commands to create task train dataset"""

import logging
import os
import shutil
from uuid import uuid4

import datumaro as dm
from flytekit.core import utils
from geti_telemetry_tools import unified_tracing
from geti_telemetry_tools.tracing.common import tracer
from geti_types import DatasetStorageIdentifier
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.label_schema import LabelSchema
from iai_core.utils.crypto import get_sha256_checksum

from jobs_common.commands.interfaces.command import ICommand
from jobs_common.exceptions import DataShardCreationFailedException
from jobs_common_extras.datumaro_conversion.sc_extractor import ScExtractorForFlyteJob

logger = logging.getLogger(__name__)


class CreateShardFileCommand(ICommand):
    """
    Command to create dataset shards

    :param dataset_storage_identifier: ID of dataset storage
    :param dataset_id: ID of Dataset to shard
    :param dataset_items: DatasetItems will be included to the shard files
    :param label_schema: label schema to use for the task
    :param work_dir: working directory path to export the shard files
    :param shard_idx: Integer index of the shard file
    :param total_num_shards: Total number of shard files in the given subset
    :param num_threads: Number of threads for image bytes pulling
    """

    def __init__(  # noqa: PLR0913
        self,
        dataset_storage_identifier: DatasetStorageIdentifier,
        dataset_id: str,
        dataset_items: list[DatasetItem],
        label_schema: LabelSchema,
        work_dir: utils.AutoDeletingTempDir,
        shard_idx: int,
        total_num_shards: int,
        num_threads: int = 10,
    ) -> None:
        super().__init__()
        self.dataset_storage_identifier = dataset_storage_identifier
        self.dataset_items = dataset_items
        self.label_schema = label_schema
        # work_dir should be a unique directory to prevent that
        # there exist more than two shard files in the directory
        self.work_dir = os.path.join(str(work_dir), str(uuid4()))
        self.dataset_id = dataset_id
        self.shard_idx = shard_idx
        self.total_num_shards = total_num_shards
        self.num_threads = num_threads

        self._fsize: int | None = None
        self._fchecksum: str | None = None

    @unified_tracing
    def execute(self) -> None:
        """
        Create the dataset shards.

        :raises DataShardCreationFailedException: if the dataset cannot be created
        """
        logger.info(f"[Command {self.id_}] Creating dataset shard files for Dataset[id={self.dataset_id}]")
        try:
            os.makedirs(self.work_dir)

            dm_dataset = dm.Dataset(
                source=ScExtractorForFlyteJob(
                    dataset_storage_identifier=self.dataset_storage_identifier,
                    sc_dataset_or_list_of_sc_items=self.dataset_items,
                    label_schema=self.label_schema,
                    num_thread_pools=self.num_threads,
                )
            )
            logger.info("Created dm.Dataset class with ScExtractorForFlyteJob")

            with tracer.start_as_current_span("dm.Dataset.export"):
                dm_dataset.export(
                    self.work_dir,
                    format="arrow",
                    max_shard_size=len(self.dataset_items),
                    save_media=True,
                )
            logger.info("Exported dm.Dataset to 'arrow'")

            src_fnames = [fname for fname in os.listdir(self.work_dir) if os.path.splitext(fname)[-1] == ".arrow"]

            if len(src_fnames) != 1:
                raise Exception("Only one file should be created.")

            src = os.path.join(self.work_dir, src_fnames[0])
            shutil.move(src, self.fpath)

            # Update fsize
            self._fsize = os.path.getsize(self.fpath)

            # Update fchecksum
            with open(self.fpath, "rb") as fp:
                self._fchecksum = get_sha256_checksum(binary_buffer=fp)

        except Exception as exc:
            logger.exception(f"Could not create dataset shard files for Dataset[id={self.dataset_id}]")
            raise DataShardCreationFailedException from exc

    @property
    def fpath(self) -> str:
        return os.path.join(self.work_dir, self.fname)

    @property
    def fname(self) -> str:
        """Get shard file name"""
        return f"datum-{self.shard_idx}-of-{self.total_num_shards}.arrow"

    @property
    def fsize(self) -> int:
        """File size of the created shard file"""
        if self._fsize is None:
            raise RuntimeError("Cannot get fsize. Please do execute() first")

        return self._fsize

    @property
    def fchecksum(self) -> str:
        """File checksum (SHA-256) of the created shard file"""
        if self._fchecksum is None:
            raise RuntimeError("Cannot get fchecksum. Please do execute() first")

        return self._fchecksum

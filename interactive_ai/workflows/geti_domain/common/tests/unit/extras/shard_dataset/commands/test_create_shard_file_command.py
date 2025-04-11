# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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
"""This module tests commands to create task train dataset"""

import os
from pathlib import Path
from unittest.mock import patch

import cv2
import datumaro as dm
import numpy as np
import pytest

from jobs_common_extras.shard_dataset.commands.create_shard_file_command import CreateShardFileCommand


@pytest.mark.JobsComponent
class TestCreateShardFileCommand:
    def test_create_shard_file_command(
        self,
        fxt_dataset_storage,
        fxt_dataset_items_with_image_data,
        fxt_label_schema,
        fxt_mongo_id,
        tmp_path: Path,
    ) -> None:
        # Arrange
        dataset_id = fxt_mongo_id(1003)
        dir_path = tmp_path / "test"
        dir_path.mkdir()
        shard_idx = 0
        total_num_shards = 3

        img = np.zeros([4, 4, 3], dtype=np.uint8)
        _, np_img_bytes = cv2.imencode(".png", img)
        img_bytes = bytes(np_img_bytes)

        # Act
        with patch(
            "jobs_common_extras.datumaro_conversion.sc_extractor.get_image_bytes",
            return_value=img_bytes,
        ):
            command = CreateShardFileCommand(
                dataset_storage_identifier=fxt_dataset_storage.identifier,
                dataset_id=dataset_id,
                dataset_items=fxt_dataset_items_with_image_data,
                label_schema=fxt_label_schema,
                work_dir=str(dir_path),
                shard_idx=shard_idx,
                total_num_shards=total_num_shards,
            )
            command.execute()

        # Assert
        assert os.path.exists(command.fpath)
        dir_shard_file = os.path.dirname(command.fpath)

        dm_dataset = dm.Dataset.import_from(dir_shard_file, format="arrow")
        for item in dm_dataset:
            assert isinstance(item.media.data, np.ndarray)

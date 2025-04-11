# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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
This module implements rest views for dataset storage entities
"""

from typing import Any

from sc_sdk.entities.dataset_storage import DatasetStorage

ID_ = "id"
NAME = "name"
USE_FOR_TRAINING = "use_for_training"
CREATION_TIME = "creation_time"
DATASETS = "datasets"


class DatasetStorageRESTViews:
    @staticmethod
    def dataset_storage_to_rest(dataset_storage: DatasetStorage) -> dict[str, Any]:
        """
        :param dataset_storage: dataset storage entity
        :return: dataset storage entity converted to REST format
        """
        return {
            ID_: dataset_storage.id_,
            NAME: dataset_storage.name,
            USE_FOR_TRAINING: dataset_storage.use_for_training,
            CREATION_TIME: dataset_storage.creation_date.isoformat(),
        }

    @staticmethod
    def dataset_storages_to_rest(dataset_storages: tuple[DatasetStorage, ...]) -> dict[str, Any]:
        """
        :param dataset_storages: list of dataset storages
        :return: dict containing list of dataset storage REST representations
        """
        return {
            DATASETS: [
                DatasetStorageRESTViews.dataset_storage_to_rest(dataset_storage) for dataset_storage in dataset_storages
            ]
        }

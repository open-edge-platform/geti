#
# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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
#

"""This module contains the MongoDB mapper for primitive entities like Tensors, Numpy arrays and Datetime objects"""

import datetime

import numpy as np

from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperBackward, IMapperForward, IMapperSimple
from sc_sdk.utils.time_utils import now


class NumpyToMongo(IMapperSimple[np.ndarray, dict]):
    """MongoDB mapper for `np.ndarray`"""

    @staticmethod
    def forward(instance: np.ndarray) -> dict:
        # We get the shape of the original ndarray and flatten the array after that to a 1-D array by calling
        # array.reshape(-1). We pass the 1-D array and the shape so the ndarray can be reconstructed later using
        # this information.
        return {
            "array_shape": instance.shape,
            "array_values": instance.reshape(-1).tolist(),
        }

    @staticmethod
    def backward(instance: dict) -> np.ndarray:
        array_values = np.asarray(instance["array_values"])
        array_shape = instance["array_shape"]
        return array_values.reshape(array_shape)


class DatetimeToMongo(
    IMapperForward[datetime.datetime, datetime.datetime],
    IMapperBackward[datetime.datetime, None | str | datetime.datetime],
):
    """MongoDB mapper for `datetime.datetime` entities"""

    @staticmethod
    def forward(instance: datetime.datetime) -> datetime.datetime:
        return instance

    @staticmethod
    def backward(instance: None | str | datetime.datetime) -> datetime.datetime:
        if isinstance(instance, str):
            # Backward compatibility with the old SC format.
            # The old format is the ISO format in localtime, however the new format is UTC.
            try:
                modification_date = datetime.datetime.strptime(instance, "%Y-%m-%dT%H:%M:%S.%f")
                modification_date = modification_date.astimezone(datetime.timezone.utc)
            except (ValueError, TypeError):
                modification_date = now()

            return modification_date
        if isinstance(instance, datetime.datetime):
            # Mongo does not store the timezone, so we manually insert it.
            return instance.replace(tzinfo=datetime.timezone.utc)
        # Case where instance is None or we received an unexpected type.
        return now()

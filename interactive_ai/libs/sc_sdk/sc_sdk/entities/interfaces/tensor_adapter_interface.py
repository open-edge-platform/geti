"""This module implements the TensorAdapterInterface"""

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

import abc

import numpy as np


class TensorAdapterInterface(metaclass=abc.ABCMeta):
    """
    This interface describes how the Adapter looks like that allows an entity,
    such as a Tensor entity to fetch its data and shape lazily.
    """

    def __init__(self, repo_adapter, binary_filename: str) -> None:  # noqa: ANN001
        self.repo_adapter = repo_adapter
        self.binary_filename = binary_filename

    @property
    @abc.abstractmethod
    def shape(self) -> tuple[int, ...]:
        """Returns the shape of the Tensor"""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def numpy(self) -> np.ndarray:
        """Returns the numpy representation of the Tensor"""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def size_on_storage(self) -> int:
        """Returns the size of the Tensor on the filesystem"""
        raise NotImplementedError

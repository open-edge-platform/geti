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
import numpy as np

from repos.reference_feature_binary_repo import ReferenceFeatureBinaryRepo

from sc_sdk.adapters.binary_interpreters import NumpyBinaryInterpreter


class ReferenceFeatureAdapter:
    """
    ReferenceFeatureAdapter is responsible for fetching reference feature's numpy data stored in the binary repo

    :param binary_repo: The binary repo where the reference feature is stored
    :param binary_filename: The filename of the reference feature in the binary repo
    """

    def __init__(self, binary_repo: ReferenceFeatureBinaryRepo, binary_filename: str) -> None:
        self.binary_repo = binary_repo
        self.binary_filename = binary_filename

    def __eq__(self, other: object):
        if not isinstance(other, ReferenceFeatureAdapter):
            return False
        return self.binary_filename == other.binary_filename

    @property
    def numpy(self) -> np.ndarray:
        """Get the numpy data of the reference feature from the binary repo"""
        numpy = self.binary_repo.get_by_filename(
            filename=self.binary_filename, binary_interpreter=NumpyBinaryInterpreter()
        )
        if not isinstance(numpy, np.ndarray):
            raise ValueError(f"Expected numpy data, got {type(numpy)}")
        return numpy

    @property
    def size_on_storage(self) -> int:
        """Return the consumed storage (in bytes) of the entity"""
        return self.binary_repo.get_object_size(filename=self.binary_filename)

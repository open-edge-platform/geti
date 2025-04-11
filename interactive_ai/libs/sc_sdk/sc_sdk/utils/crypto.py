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
"""This module implements the file checksum utility"""

import hashlib
from typing import BinaryIO


def get_sha256_checksum(binary_buffer: BinaryIO, n_read_bytes: int = 65536) -> str:
    """
    Compute SHA-256 checksum from the given binary buffer

    :param binary_buffer: Input binary buffer
    :return: SHA-256 checksum string
    """
    if not binary_buffer.seekable():
        raise ValueError("binary_buffer should be seekable.")
    m = hashlib.sha256()
    binary_buffer.seek(0)
    while _bytes := binary_buffer.read(n_read_bytes):
        m.update(_bytes)
    return m.hexdigest()

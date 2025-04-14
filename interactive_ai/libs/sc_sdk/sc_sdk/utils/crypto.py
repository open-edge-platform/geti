# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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

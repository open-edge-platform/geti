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

from collections.abc import Generator


def read_file_in_chunks(filename: str, buffer_size: int = 2**10 * 8) -> Generator[bytes, None, None]:
    """
    Reads a file in chunks of bytes.

    :param filename: the path to the file to read
    :param buffer_size: the size of each chunk in bytes. Defaults to 8KB.
    :return: a generator yielding chunks of bytes from the file
    """
    with open(filename, mode="rb") as f:
        while chunk := f.read(buffer_size):
            yield chunk

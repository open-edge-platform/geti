# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

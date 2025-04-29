# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements methods for safely unzipping user-uploaded zip files
"""

import logging
import os
import shutil
import zipfile
from collections.abc import Callable

logger = logging.getLogger(__name__)


def safely_unzip(  # noqa: C901, PLR0915
    zip_file_path: str,
    extraction_path: str,
    max_size_bytes: int,
    max_num_files: int,
    unzip_buffer_size_bytes: int,
    progress_callback: Callable[[int, int], None] | None = None,
) -> None:
    """
    Unzip a local file to a target local path. This method:
     - protects from container escape, by checking that the target path for every extracted file or directory is
      within the target directory.
     - protects from zip bomb attacks, by reading the data in the archive with a buffer, which allows us to control the
      process and terminate it if the maximum size is exceeded. A check is also present to ensure the number of files
      does not exceed a maximum.

    :param zip_file_path: Local path to the zip file
    :param extraction_path: Target path to extract the zip file to
    :param max_size_bytes: The maximum size in bytes for the unpacked archive
    :param max_num_files: The maximum number of files allowed in the archive
    :param unzip_buffer_size_bytes: Number of bytes in the buffer used to unpack the zip file
    :param progress_callback: An optional callback function that takes two integers
                              (current progress, total) and returns None. It is called
                              to update the progress of the extraction.
    :raises ValueError: if the zip file failed the above described validation
    """
    extracted_files: list[str] = []
    extraction_path = os.path.realpath(extraction_path)
    os.makedirs(extraction_path, exist_ok=True)

    def cleanup():
        """In case the unzipping is terminated, remove the already extracted files."""
        for file in extracted_files:
            if os.path.isdir(file):
                shutil.rmtree(file)
            elif os.path.isfile(file):
                os.remove(file)

    def check_total_unpacked_size() -> int:
        """
        Check the total size of all files in the zip before extraction.

        :return: Returns the total size of the files in bytes.
        """
        total_size = 0
        with zipfile.ZipFile(zip_file_path, "r") as z:
            for entry in z.infolist():
                if not entry.is_dir():
                    total_size += entry.file_size
                    if total_size > max_size_bytes:
                        raise ValueError(
                            f"Total size of the files in the archive exceeds the limit of {max_size_bytes} bytes."
                        )
        return total_size

    def unpack_zip_with_buffer(total_size: int, progress_callback: Callable[[int, int], None] | None = None) -> None:
        """
        Unpack the zip file in a controlled manner by extracting with a buffer.

        :param total_size: The total size of the files to report progress.
        :param progress_callback: An optional callback function that takes two integers
                                  (current progress, total) and returns None. It is called
                                  to update the progress of the extraction.
        """
        extracted_size = 0
        with zipfile.ZipFile(zip_file_path, "r") as z:
            for entry in z.infolist():
                entry_target_location = os.path.normpath(os.path.join(extraction_path, entry.filename))
                if not entry_target_location.startswith(extraction_path):
                    raise ValueError("File in archive is set to be extracted outside target directory.")

                # For directories, create the directory and continue
                if entry.is_dir():
                    os.makedirs(entry_target_location, exist_ok=True)
                    extracted_files.append(entry_target_location)
                    continue

                # For files, create the parent directory before writing to the file
                entry_target_directory = os.path.dirname(entry_target_location)
                os.makedirs(entry_target_directory, exist_ok=True)

                # Write data to the file in steps to ensure the system is not overloaded
                with z.open(entry) as zf, open(entry_target_location, "wb") as f:
                    while True:
                        data = zf.read(unzip_buffer_size_bytes)
                        if not data:
                            break
                        if extracted_size + len(data) > max_size_bytes:
                            raise ValueError(f"Archive size exceeds the limit of {max_size_bytes} bytes.")
                        f.write(data)
                        extracted_size += len(data)
                        if progress_callback:
                            progress_callback(extracted_size, total_size)

                extracted_files.append(entry_target_location)
                if len(extracted_files) > max_num_files:
                    raise ValueError(f"Archive is not allowed to contain more than {max_num_files} files.")

    try:
        total = check_total_unpacked_size()
        unpack_zip_with_buffer(total_size=total, progress_callback=progress_callback)
    except ValueError as e:
        logger.error("Failed to unzip a file from %s to %s.", zip_file_path, extraction_path)
        cleanup()
        raise e

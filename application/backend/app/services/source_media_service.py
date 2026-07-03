# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import shutil
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from anyio import to_thread


class SourceMediaService:
    """Stores video files uploaded for use as 'video_file' pipeline sources.

    Uploaded files are kept on disk in a fixed, non-project-scoped location. No database
    record is created: the resulting filesystem path is returned directly to the caller,
    who is expected to store it as the 'video_path' of a video_file source.
    """

    def __init__(self, source_media_dir: Path) -> None:
        self._source_media_dir = source_media_dir

    async def upload(self, filename: str, file_obj: BinaryIO) -> Path:
        """
        Store an uploaded video file using a high-speed threaded block copy.

        A new UUID subdirectory is created under the configured source media root, and the
        incoming file stream is written to a file with the given filename inside it. The
        file copy operation is offloaded to a worker thread using AnyIO to prevent blocking
        the main asynchronous event loop.

        Args:
            filename: Target filename of the uploaded video within its dedicated subdirectory.
            file_obj: A readable binary stream (such as SpooledTemporaryFile) containing the
                video payload.

        Returns:
            The absolute path to the stored video file.
        """
        target_dir = self._source_media_dir / str(uuid4())
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename

        def _perform_copy() -> None:
            try:
                file_obj.seek(0)
            except (AttributeError, OSError, ValueError):
                pass

            temp_path = target_path.with_suffix(f"{target_path.suffix}.part")

            try:
                with temp_path.open("wb") as out_f:
                    shutil.copyfileobj(file_obj, out_f, length=1024 * 1024)
                temp_path.replace(target_path)
            except Exception:
                temp_path.unlink(missing_ok=True)
                raise

        await to_thread.run_sync(_perform_copy)

        return target_path.resolve()

# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Shared-memory based IPC for reporting status from worker processes to the main process."""

from multiprocessing.shared_memory import SharedMemory
from multiprocessing.synchronize import Lock
from typing import TypeVar

from pydantic import BaseModel

# 4 bytes length prefix + JSON payload
STATUS_SHM_SIZE = 4096

T = TypeVar("T", bound=BaseModel)


def write_status(status: BaseModel, shm: SharedMemory, lock: Lock) -> None:
    """Serialize and write a Pydantic model into shared memory (called from worker process).

    If the serialized payload exceeds the buffer, the ``message`` field (if any) is repeatedly
    halved until the payload fits. If it still doesn't fit (e.g. there is no ``message`` field to
    shrink, or the remaining fields alone are too large), a clear ValueError is raised.
    """
    buf = shm.buf
    if buf is None:
        raise ValueError("Shared memory buffer is not available (already closed?)")
    # The 4-byte length prefix precedes the JSON payload, so the usable payload space is shm.size - 4.
    max_payload = shm.size - 4
    data = status.model_dump_json().encode()
    while len(data) > max_payload:
        # Truncate message field if payload is too large (should not happen for status objects).
        message = getattr(status, "message", None)
        if not message:
            raise ValueError(
                f"Status payload ({len(data)} bytes) exceeds shared memory capacity "
                f"({max_payload} bytes) and cannot be truncated further."
            )
        # Halve the message and retry; integer division guarantees progress down to an empty string.
        status = status.model_copy(update={"message": message[: len(message) // 2]})
        data = status.model_dump_json().encode()
    with lock:
        buf[:4] = len(data).to_bytes(4, "little")
        buf[4 : 4 + len(data)] = data


def read_status(model_class: type[T], shm: SharedMemory, lock: Lock) -> T | None:
    """Read the latest status from shared memory and deserialize into the given Pydantic model class."""
    buf = shm.buf
    if buf is None:
        raise ValueError("Shared memory buffer is not available (already closed?)")
    with lock:
        size = int.from_bytes(bytes(buf[:4]), "little")
        if size == 0:
            return None
        data = bytes(buf[4 : 4 + size])
    return model_class.model_validate_json(data)

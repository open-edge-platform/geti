# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Persistent filesystem storage for resumable TUS uploads."""

import asyncio
import base64
import binascii
import json
import os
import re
import shutil
from collections.abc import AsyncIterator, Buffer
from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import cast
from uuid import UUID, uuid4

from anyio import to_thread

TUS_VERSION = "1.0.0"
_METADATA_KEY = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class TusUploadError(Exception):
    """Base error for resumable upload operations."""


class TusUploadNotFoundError(TusUploadError):
    """The requested upload does not exist or has expired."""


class TusUploadConflictError(TusUploadError):
    """The upload is not in a state that permits the requested operation."""


class TusUploadInvalidError(TusUploadError):
    """The upload request violates TUS protocol or configured limits."""


class TusUploadTooLargeError(TusUploadInvalidError):
    """The upload exceeds the configured or declared size limit."""


@dataclass(frozen=True)
class TusUpload:
    """Metadata and paths for a resumable upload."""

    id: UUID
    length: int
    offset: int
    metadata: dict[str, str]
    expires_at: float
    claimed: bool
    path: Path


class TusUploadService:
    """Persist TUS uploads on disk so clients can resume across requests and restarts."""

    def __init__(self, uploads_dir: Path, max_size: int, expiration_seconds: int) -> None:
        self._uploads_dir = uploads_dir
        self._max_size = max_size
        self._expiration_seconds = expiration_seconds
        self._locks: dict[UUID, asyncio.Lock] = {}
        self._active_claims: set[UUID] = set()
        self._uploads_dir.mkdir(parents=True, exist_ok=True)

    @property
    def max_size(self) -> int:
        """Return the maximum permitted upload size."""
        return self._max_size

    def create(self, length: int, metadata_header: str | None) -> TusUpload:
        """Create an upload and its empty data file."""
        if length < 0:
            raise TusUploadInvalidError("Upload length must be a non-negative integer.")
        if length > self._max_size:
            raise TusUploadTooLargeError(f"Upload length exceeds the {self._max_size}-byte limit.")
        metadata = self._parse_metadata(metadata_header)
        self.cleanup_expired()

        upload_id = uuid4()
        upload_dir = self._upload_dir(upload_id)
        upload_dir.mkdir(parents=True)
        data_path = self._data_path(upload_id)
        data_path.touch()
        expires_at = time() + self._expiration_seconds
        self._write_info(upload_id, {"length": length, "offset": 0, "metadata": metadata, "expires_at": expires_at})
        return TusUpload(upload_id, length, 0, metadata, expires_at, False, data_path)

    def get(self, upload_id: UUID) -> TusUpload:
        """Return upload state, removing it if it has expired."""
        info = self._read_info(upload_id)
        if info is None:
            raise TusUploadNotFoundError(str(upload_id))
        return self._as_upload(upload_id, info)

    async def append(self, upload_id: UUID, offset: int, chunks: AsyncIterator[bytes]) -> TusUpload:
        """Append a request body when its offset matches the persisted upload offset."""
        self.get(upload_id)
        lock = self._locks.setdefault(upload_id, asyncio.Lock())
        async with lock:
            current = self.get(upload_id)
            if current.claimed:
                raise TusUploadConflictError("Upload is currently being consumed.")
            if offset != current.offset:
                raise TusUploadConflictError(f"Upload offset mismatch: expected {current.offset}, received {offset}.")

            # If a request was interrupted after writing bytes but before the new offset was persisted,
            # truncate them here so a retry starts exactly at the last acknowledged offset.
            await to_thread.run_sync(self._truncate, current.path, offset)
            received = 0
            data_file = await to_thread.run_sync(lambda: current.path.open("r+b"))
            try:
                await to_thread.run_sync(lambda: data_file.seek(offset))
                async for chunk in chunks:
                    if not chunk:
                        continue
                    received += len(chunk)
                    if current.offset + received > current.length:
                        raise TusUploadTooLargeError("PATCH body exceeds the declared upload length.")
                    await to_thread.run_sync(lambda: data_file.write(cast(Buffer, chunk)))
                await to_thread.run_sync(data_file.flush)
                await to_thread.run_sync(lambda: os.fsync(data_file.fileno()))
            finally:
                await to_thread.run_sync(data_file.close)

            new_offset = current.offset + received
            info = self._read_info(upload_id)
            if info is None:
                raise TusUploadNotFoundError(str(upload_id))
            info["offset"] = new_offset
            await to_thread.run_sync(self._write_info, upload_id, info)
            return self._as_upload(upload_id, info)

    async def claim_completed(self, upload_id: UUID) -> TusUpload:
        """Reserve a completed upload for one consumer, rejecting concurrent reuse."""
        self.get(upload_id)
        lock = self._locks.setdefault(upload_id, asyncio.Lock())
        async with lock:
            upload_dir = self._upload_dir(upload_id)
            if not upload_dir.is_dir():
                raise TusUploadNotFoundError(str(upload_id))
            claim_path = self._claim_path(upload_id)
            try:
                with claim_path.open("x", encoding="utf-8"):
                    pass
            except FileExistsError as error:
                raise TusUploadConflictError("Upload is already being consumed.") from error

            try:
                upload = self.get(upload_id)
                if upload.offset != upload.length:
                    raise TusUploadConflictError("Upload is incomplete.")
                self._active_claims.add(upload_id)
                return upload
            except Exception:
                claim_path.unlink(missing_ok=True)
                raise

    def get_consumed_result(self, upload_id: UUID, consumer: str) -> dict | None:
        """Return a cached result for an idempotent retry of a completed consumer request."""
        self.get(upload_id)
        result_path = self._consumed_path(upload_id)
        try:
            consumed = json.loads(result_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except (OSError, json.JSONDecodeError) as error:
            raise TusUploadConflictError("Upload consumption state is invalid.") from error
        if not isinstance(consumed, dict) or not isinstance(consumed.get("result"), dict):
            raise TusUploadConflictError("Upload consumption state is invalid.")
        if consumed.get("consumer") != consumer:
            raise TusUploadConflictError("Upload was already consumed by a different operation.")
        return consumed["result"]

    def complete_claim(self, upload_id: UUID, consumer: str, result: dict) -> None:
        """Persist the successful result while retaining the claim for safe client retries."""
        if not self._claim_path(upload_id).exists():
            raise TusUploadConflictError("Upload is not claimed.")
        self._write_json_atomic(self._consumed_path(upload_id), {"consumer": consumer, "result": result})
        info = self._read_info(upload_id)
        if info is None:
            raise TusUploadNotFoundError(str(upload_id))
        info["consumed"] = True
        self._write_info(upload_id, info)
        self._data_path(upload_id).unlink(missing_ok=True)
        self._active_claims.discard(upload_id)

    def release_claim(self, upload_id: UUID) -> None:
        """Release a reservation after the consuming operation fails."""
        self._claim_path(upload_id).unlink(missing_ok=True)
        self._active_claims.discard(upload_id)

    async def delete(self, upload_id: UUID) -> None:
        """Delete upload data and metadata."""
        lock = self._locks.setdefault(upload_id, asyncio.Lock())
        async with lock:
            upload = self.get(upload_id)
            if upload.claimed:
                raise TusUploadConflictError("Upload is currently being consumed.")
            await to_thread.run_sync(lambda: shutil.rmtree(self._upload_dir(upload_id), ignore_errors=False))
            self._locks.pop(upload_id, None)

    def delete_claimed(self, upload_id: UUID) -> None:
        """Delete an upload after its consumer successfully processes it."""
        if not self._claim_path(upload_id).exists():
            raise TusUploadConflictError("Upload is not claimed.")
        shutil.rmtree(self._upload_dir(upload_id), ignore_errors=False)
        self._locks.pop(upload_id, None)

    def cleanup_expired(self) -> int:
        """Delete expired upload directories and return the number removed."""
        removed = 0
        for upload_dir in self._uploads_dir.iterdir():
            if not upload_dir.is_dir():
                continue
            try:
                upload_id = UUID(upload_dir.name)
            except ValueError:
                continue
            if self._is_locked(upload_id):
                continue
            if self._read_info(upload_id) is None:
                removed += 1
        return removed

    def _is_locked(self, upload_id: UUID) -> bool:
        lock = self._locks.get(upload_id)
        return lock is not None and lock.locked()

    def _read_info(self, upload_id: UUID) -> dict | None:
        info_path = self._info_path(upload_id)
        try:
            info = json.loads(info_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError):
            shutil.rmtree(self._upload_dir(upload_id), ignore_errors=True)
            return None
        if not isinstance(info, dict):
            shutil.rmtree(self._upload_dir(upload_id), ignore_errors=True)
            return None
        try:
            length = int(info["length"])
            offset = int(info["offset"])
            expires_at = float(info["expires_at"])
            metadata = info["metadata"]
            if length < 0 or offset < 0 or offset > length or not isinstance(metadata, dict):
                raise ValueError("Invalid persisted upload state")
        except (KeyError, TypeError, ValueError):
            shutil.rmtree(self._upload_dir(upload_id), ignore_errors=True)
            return None
        if expires_at <= time() and not self._is_locked(upload_id) and upload_id not in self._active_claims:
            shutil.rmtree(self._upload_dir(upload_id), ignore_errors=True)
            return None
        data_path = self._data_path(upload_id)
        if not info.get("consumed") and (not data_path.is_file() or data_path.stat().st_size < offset):
            shutil.rmtree(self._upload_dir(upload_id), ignore_errors=True)
            return None
        return info

    def _write_info(self, upload_id: UUID, info: dict) -> None:
        self._write_json_atomic(self._info_path(upload_id), info)

    @staticmethod
    def _write_json_atomic(path: Path, payload: dict) -> None:
        temporary_path = path.with_suffix(".json.part")
        with temporary_path.open("w", encoding="utf-8") as info_file:
            info_file.write(json.dumps(payload))
            info_file.flush()
            os.fsync(info_file.fileno())
        temporary_path.replace(path)

    @staticmethod
    def _truncate(path: Path, offset: int) -> None:
        with path.open("r+b") as data_file:
            data_file.truncate(offset)

    def _as_upload(self, upload_id: UUID, info: dict, claimed: bool | None = None) -> TusUpload:
        return TusUpload(
            id=upload_id,
            length=int(info["length"]),
            offset=int(info["offset"]),
            metadata={str(key): str(value) for key, value in info.get("metadata", {}).items()},
            expires_at=float(info["expires_at"]),
            claimed=self._claim_path(upload_id).exists() if claimed is None else claimed,
            path=self._data_path(upload_id),
        )

    @staticmethod
    def _parse_metadata(metadata_header: str | None) -> dict[str, str]:
        if not metadata_header:
            return {}
        if len(metadata_header) > 8192:
            raise TusUploadInvalidError("Upload-Metadata header is too large.")
        parsed: dict[str, str] = {}
        for item in metadata_header.split(","):
            parts = item.strip().split()
            if len(parts) not in (1, 2) or not _METADATA_KEY.fullmatch(parts[0]):
                raise TusUploadInvalidError("Upload-Metadata header is malformed.")
            key = parts[0]
            if key in parsed:
                raise TusUploadInvalidError("Upload-Metadata contains a duplicate key.")
            try:
                encoded_value = parts[1] if len(parts) == 2 else ""
                parsed[key] = base64.b64decode(encoded_value, validate=True).decode("utf-8")
            except (binascii.Error, UnicodeDecodeError) as error:
                raise TusUploadInvalidError("Upload-Metadata values must be base64-encoded UTF-8.") from error
        return parsed

    def _upload_dir(self, upload_id: UUID) -> Path:
        return self._uploads_dir / str(upload_id)

    def _data_path(self, upload_id: UUID) -> Path:
        return self._upload_dir(upload_id) / "data"

    def _info_path(self, upload_id: UUID) -> Path:
        return self._upload_dir(upload_id) / "info.json"

    def _claim_path(self, upload_id: UUID) -> Path:
        return self._upload_dir(upload_id) / ".claimed"

    def _consumed_path(self, upload_id: UUID) -> Path:
        return self._upload_dir(upload_id) / "consumed.json"

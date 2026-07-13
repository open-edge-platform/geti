# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import time
from abc import ABC
from typing import Any

import cv2
import numpy as np

from app.models import SourceType
from app.stream.stream_data import StreamData
from app.stream.video_stream import VideoStream


class BaseOpenCVStream(VideoStream, ABC):
    """Base class for OpenCV-based video streams with common functionality."""

    def __init__(
        self,
        source: str | int,
        source_type: SourceType,
        codec: str | None = None,
        timeout: int | None = None,
        api_preference: int = cv2.CAP_ANY,
        **metadata,
    ) -> None:
        """Initialize OpenCV stream.

        Args:
            source: Video source (device ID, file path, or URL)
            source_type: Type of the video source
            codec: Video codec
            timeout: Timeout in milliseconds for opening/reading the stream. Defaults to None.
            api_preference: OpenCV backend to use (e.g. cv2.CAP_V4L2). Defaults to cv2.CAP_ANY.
            **metadata: Additional metadata for the stream
        """
        self.source = source
        self.source_type = source_type
        self.codec = codec
        self.timeout = timeout
        self.api_preference = api_preference
        self.metadata = metadata
        self.cap: cv2.VideoCapture
        self._initialize_capture()

    def _initialize_capture(self) -> None:
        """Initialize the OpenCV VideoCapture."""
        self.cap = cv2.VideoCapture(self.source, self.api_preference)  # type: ignore[call-overload]
        if not self.cap.isOpened():
            raise RuntimeError(self._not_opened_message())
        if self.codec:
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*self.codec))  # type: ignore[attr-defined]
        if self.timeout:
            self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, self.timeout)
            self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, self.timeout)

    def _not_opened_message(self) -> str:
        """Build a user-facing message for a failed-to-open capture, tailored per source type.

        For IP cameras, ``self.source`` is the connection URL actually passed to OpenCV, which
        may embed credentials (see ``IPCameraConfig.get_configured_stream_url``). The original,
        credential-free URL is preserved in ``metadata['stream_url']`` and used here instead, so
        error text never leaks credentials.
        """
        match self.source_type:
            case SourceType.VIDEO_FILE:
                return f"Could not open video file: {self.source}"
            case SourceType.IP_CAMERA:
                display_url = self.metadata.get("stream_url", self.source)
                return f"Could not connect to IP camera stream: {display_url}"
            case _:
                return f"Could not open video source: {self.source}"

    def _read_frame(self) -> np.ndarray:
        """Read a frame from the capture device."""
        if self.cap is None:
            raise RuntimeError("Video capture not initialized")

        ret, frame = self.cap.read()
        if not ret:
            return self._handle_read_failure()
        return frame

    def _handle_read_failure(self) -> np.ndarray:
        """Handle frame read failure. Override in subclasses for specific behavior."""
        raise RuntimeError(f"Failed to capture frame from {self.source_type.value}")

    def _get_source_metadata(self) -> dict[str, Any]:
        """Get metadata specific to this source."""
        return {"source_type": self.source_type.value, **self.metadata}

    def get_data(self) -> StreamData | None:
        """Get the latest frame from the video stream."""
        frame = self._read_frame()
        return StreamData(
            frame_data=frame,
            timestamp=time.time(),
            source_metadata=self._get_source_metadata(),
        )

    def release(self) -> None:
        """Release OpenCV VideoCapture resources."""
        if self.cap is not None:
            self.cap.release()

# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Sequence
from typing import Protocol

import numpy as np

from app.models import MediaStorage, OmeImageInfo, Region


class OmeImageHandle(Protocol):
    """An opened OME image with lazy region reading."""

    info: OmeImageInfo

    def read_region(
        self,
        *,
        level: int = 0,
        region: Region | None = None,
        z: int = 0,
        t: int = 0,
        channels: Sequence[int] | None = None,
    ) -> np.ndarray: ...

    def close(self) -> None: ...

    def __enter__(self) -> "OmeImageHandle": ...

    def __exit__(self, *exc: object) -> None: ...


class OmeReader(Protocol):
    """Format-specific OME opener implementation (TIFF or Zarr)."""

    def probe(self, storage: MediaStorage) -> bool: ...

    def open(self, storage: MediaStorage, series: int = 0) -> OmeImageHandle: ...

# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


from uuid import UUID

import cv2
import numpy as np

from app.models.media import Media
from app.services.media_service import MediaService


class BinaryNotFoundError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class MediaNumpyLoader:
    def __init__(
        self,
        media_service: MediaService,
    ) -> None:
        self._media_service = media_service

    def load_media_binary(self, project_id: UUID, media: Media) -> np.ndarray:
        binary_path = self._media_service.get_media_binary_path(project_id=project_id, media=media)
        # IMREAD_UNCHANGED preserves the original bit depth (e.g. 16-bit PNG/TIFF images).
        binary_data = cv2.imread(str(binary_path), cv2.IMREAD_UNCHANGED)
        if binary_data is None:
            raise BinaryNotFoundError(f"Media {str(media.id)} binary cannot be found")
        # Add explicit channel dimension for 2D grayscale: (H, W) → (H, W, 1)
        if binary_data.ndim == 2:
            binary_data = binary_data[..., np.newaxis]
        # Convert only 3-channel BGR images to RGB; pass grayscale and other formats through.
        if binary_data.shape[-1] == 3:
            binary_data = cv2.cvtColor(binary_data, cv2.COLOR_BGR2RGB)
        return binary_data

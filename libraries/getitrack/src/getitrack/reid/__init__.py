# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Appearance / ReID layer: feature providers and per-track appearance memory.

`ReIDProvider` (with OpenVINO and torch implementations) turns boxes into
descriptors; `build_reid_provider` picks one from a `ReIDConfig`;
`AppearanceGallery` holds a bounded per-track appearance memory. Provider
implementations import their backend (openvino / torch / torchreid) lazily.
"""

from getitrack.reid.base import ReIDProvider
from getitrack.reid.export import export_torchreid_to_openvino
from getitrack.reid.factory import build_reid_provider
from getitrack.reid.gallery import AppearanceGallery
from getitrack.reid.openvino_provider import OpenVINOReIDProvider
from getitrack.reid.torchreid_provider import TorchReIDProvider

__all__ = [
    "AppearanceGallery",
    "OpenVINOReIDProvider",
    "ReIDProvider",
    "TorchReIDProvider",
    "build_reid_provider",
    "export_torchreid_to_openvino",
]

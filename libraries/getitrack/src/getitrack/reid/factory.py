# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Resolve a `ReIDConfig` into a concrete `ReIDProvider`.

Keeps backend selection (torch vs OpenVINO, torchreid model vs prebuilt IR) in
one place so trackers only depend on the `ReIDProvider` contract. Backend-specific
imports stay lazy, so choosing one backend never requires the other's stack.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from getitrack.config import ReIDBackend

if TYPE_CHECKING:
    from getitrack.config import ReIDConfig
    from getitrack.reid.base import ReIDProvider


def _torch_device(device: str) -> str:
    """Map a config device string to a torch device (``CPU``->``cpu``, ``GPU``->``cuda``)."""
    lowered = device.lower()
    if lowered.startswith(("cpu", "cuda")):
        return lowered
    return "cuda" if lowered == "gpu" else lowered


def build_reid_provider(config: ReIDConfig) -> ReIDProvider | None:
    """Build the ReID provider selected by ``config``, or None when unavailable.

    Returns None when ReID is disabled or no model source is configured (the
    caller then supplies ``Detections.embeddings`` directly). The torch backend
    runs a torchreid model natively; the OpenVINO backend runs a prebuilt IR, or
    auto-exports and caches one from the torchreid model when ``model_name`` is
    set.
    """
    if not config.enabled:
        return None

    if config.backend is ReIDBackend.TORCH:
        if config.model_name is None:
            msg = "ReID torch backend requires model_name (a torchreid architecture)."
            raise ValueError(msg)
        from getitrack.reid.torchreid_provider import TorchReIDProvider

        return TorchReIDProvider(
            config.model_name,
            weights_path=config.model_path,
            device=_torch_device(config.device),
            input_size=config.input_size,
        )

    from getitrack.reid.openvino_provider import OpenVINOReIDProvider

    if config.model_name is not None:
        from getitrack.reid.export import export_torchreid_to_openvino

        xml_path = export_torchreid_to_openvino(
            config.model_name,
            config.input_size,
            weights_path=config.model_path,
            cache_dir=config.cache_dir,
        )
        return OpenVINOReIDProvider(xml_path, input_size=config.input_size, device=config.device)

    if config.model_path is not None:
        return OpenVINOReIDProvider(config.model_path, input_size=config.input_size, device=config.device)

    return None

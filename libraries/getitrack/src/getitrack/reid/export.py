# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Export a torchreid model to an OpenVINO IR for the OpenVINO ReID backend.

This bridges torchreid's model zoo to `OpenVINOReIDProvider`: it builds the
torchreid ``nn.Module`` (downloading or loading its weights) and converts it to
an IR once, caching the result so repeated runs skip the conversion.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def _default_cache_dir() -> Path:
    """Return the default cache directory for exported ReID IRs."""
    return Path.home() / ".cache" / "getitrack" / "reid"


def _cache_stem(model_name: str, input_size: tuple[int, int], weights_path: str | Path | None) -> str:
    """Build a cache filename stem unique to the model, input size, and weights."""
    height, width = input_size
    if weights_path is None:
        tag = "pretrained"
    else:
        digest = hashlib.sha256(str(Path(weights_path).resolve()).encode()).hexdigest()[:8]
        tag = f"{Path(weights_path).stem}_{digest}"
    return f"{model_name}_{height}x{width}_{tag}"


def export_torchreid_to_openvino(
    model_name: str,
    input_size: tuple[int, int],
    *,
    weights_path: str | Path | None = None,
    cache_dir: str | Path | None = None,
) -> Path:
    """Export a torchreid model to an OpenVINO IR, returning the cached ``.xml``.

    The model is built on CPU and converted to a dynamic-batch IR. When the IR
    already exists in the cache it is returned without re-exporting.

    Args:
        model_name: torchreid architecture name (e.g. ``osnet_x1_0``).
        input_size: Model input ``(height, width)`` in pixels.
        weights_path: Optional ``.pth.tar`` checkpoint; torchreid downloads
            ImageNet-pretrained weights when omitted.
        cache_dir: Directory for the exported IR; defaults to
            ``~/.cache/getitrack/reid``.

    Returns:
        Path to the exported IR ``.xml`` (its ``.bin`` sits alongside).
    """
    cache = Path(cache_dir) if cache_dir is not None else _default_cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    xml_path = cache / f"{_cache_stem(model_name, input_size, weights_path)}.xml"
    if xml_path.exists():
        return xml_path

    # Lazy imports keep torch/torchreid/openvino optional for the wider package.
    import openvino as ov
    import torch
    from torchreid.reid.utils import FeatureExtractor

    height, width = input_size
    extractor = FeatureExtractor(
        model_name=model_name,
        model_path=str(weights_path) if weights_path is not None else "",
        image_size=input_size,
        device="cpu",
        verbose=False,
    )
    model = extractor.model.eval()
    ov_model = ov.convert_model(model, example_input=torch.zeros(1, 3, height, width))
    ov.save_model(ov_model, str(xml_path))
    return xml_path

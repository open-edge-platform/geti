# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Export a torchreid model to an OpenVINO IR for the OpenVINO ReID backend.

Builds the torchreid ``nn.Module`` (downloading or loading its weights) and
converts it to an IR, caching the result. Repeated runs reuse the cached IR.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def _default_cache_dir() -> Path:
    """Return the default cache directory for exported ReID IRs."""
    return Path.home() / ".cache" / "getitrack" / "reid"


def _weights_fingerprint(weights_path: str | Path) -> str:
    """Return an 8-char digest that changes when the checkpoint changes.

    Combines the resolved path with the file size and modification time so that
    replacing a checkpoint in place yields a new cache key. Falls back to the
    path alone when the file cannot be stat-ed (e.g. it does not exist yet).
    """
    resolved = Path(weights_path).resolve()
    try:
        stat = resolved.stat()
        fingerprint = f"{resolved}:{stat.st_size}:{stat.st_mtime_ns}"
    except OSError:
        fingerprint = str(resolved)
    return hashlib.sha256(fingerprint.encode()).hexdigest()[:8]


def _cache_stem(model_name: str, input_size: tuple[int, int], weights_path: str | Path | None) -> str:
    """Build a cache filename stem unique to the model, input size, and weights."""
    height, width = input_size
    tag = "pretrained" if weights_path is None else f"{Path(weights_path).stem}_{_weights_fingerprint(weights_path)}"
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

    # Import torch/torchreid/openvino lazily.
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

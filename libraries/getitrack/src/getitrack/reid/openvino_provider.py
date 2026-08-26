# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""OpenVINO-IR appearance-feature provider.

`OpenVINOReIDProvider` embeds bounding-box crops with a ReID model compiled from
an OpenVINO IR (``.xml`` + ``.bin``). It crops each box, resizes to the model
input, applies ImageNet normalisation, batches the crops through a single infer
call, and L2-normalises the descriptors.

No weights are bundled. Supply any IR that takes an ``(N, 3, H, W)`` NCHW batch
and returns ``(N, D)`` descriptors (set ``input_size`` to match); OSNet exported
from ``torchreid`` is one common choice.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast, runtime_checkable

import cv2
import numpy as np

from getitrack.matching.appearance import l2_normalize
from getitrack.reid.base import ReIDProvider
from getitrack.reid.crops import crop_boxes

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

# ImageNet normalisation constants (RGB).
_IMAGENET_MEAN = (0.485, 0.456, 0.406)
_IMAGENET_STD = (0.229, 0.224, 0.225)


@runtime_checkable
class InferResult(Protocol):
    """Minimal view of an OpenVINO inference result (index-addressable outputs)."""

    def __getitem__(self, index: int) -> np.ndarray:
        """Return the output tensor at ``index``."""


class CompiledModel(Protocol):
    """Minimal view of a compiled OpenVINO model: callable on an input batch."""

    def __call__(self, inputs: np.ndarray) -> InferResult:
        """Run inference on ``inputs`` and return the index-addressable outputs."""


class OpenVINOReIDProvider(ReIDProvider):
    """ReID feature provider backed by a compiled OpenVINO IR model.

    The OpenVINO runtime is imported lazily in the constructor.
    """

    def __init__(
        self,
        model_path: str | Path | None = None,
        *,
        input_size: tuple[int, int] = (256, 128),
        device: str = "CPU",
        mean: Sequence[float] = _IMAGENET_MEAN,
        std: Sequence[float] = _IMAGENET_STD,
        compiled_model: CompiledModel | None = None,
    ) -> None:
        """Initialise the provider.

        Args:
            model_path: Path to the OpenVINO IR ``.xml``. Ignored when
                ``compiled_model`` is supplied; required otherwise.
            input_size: Model input ``(height, width)`` in pixels.
            device: OpenVINO device to compile for (e.g. ``"CPU"``, ``"GPU"``).
            mean: Per-channel RGB mean used for normalisation.
            std: Per-channel RGB standard deviation used for normalisation.
            compiled_model: Pre-compiled model to use directly, bypassing the
                file load. Primarily an injection point for testing.

        Raises:
            ValueError: If neither ``model_path`` nor ``compiled_model`` is given.
        """
        self._input_size = input_size
        self._mean = np.asarray(mean, dtype=np.float32).reshape(1, 1, 3)
        self._std = np.asarray(std, dtype=np.float32).reshape(1, 1, 3)
        self._output_dim: int | None = None
        if compiled_model is not None:
            self._compiled: CompiledModel = compiled_model
            return
        if model_path is None:
            msg = "either model_path or compiled_model must be provided"
            raise ValueError(msg)
        # Import openvino lazily.
        import openvino as ov

        core = ov.Core()
        model = core.read_model(model_path)
        height, width = input_size
        # Force a dynamic batch dimension so one infer call embeds all boxes.
        model.reshape([-1, 3, height, width])
        # Cast openvino's broader ``__call__`` signature to the CompiledModel protocol.
        self._compiled = cast("CompiledModel", core.compile_model(model, device))

    def extract(self, frame_bgr: np.ndarray, boxes: np.ndarray) -> np.ndarray:
        """Embed each box crop into an L2-normalised descriptor (see `ReIDProvider.extract`)."""
        box_array = np.asarray(boxes, dtype=np.float32).reshape(-1, 4)
        if box_array.shape[0] == 0:
            return np.empty((0, self._output_dim or 0), dtype=np.float32)
        batch = self._preprocess(frame_bgr, box_array)
        result = self._compiled(batch)
        features = np.asarray(result[0], dtype=np.float32)
        features = features.reshape(features.shape[0], -1)
        self._output_dim = int(features.shape[1])
        return l2_normalize(features)

    def _preprocess(self, frame_bgr: np.ndarray, boxes: np.ndarray) -> np.ndarray:
        """Crop, resize, and normalise each box into an ``(N, 3, H, W)`` batch."""
        height, width = self._input_size
        batch = np.empty((boxes.shape[0], 3, height, width), dtype=np.float32)
        for i, crop in enumerate(crop_boxes(frame_bgr, boxes)):
            resized = cv2.resize(crop, (width, height), interpolation=cv2.INTER_LINEAR)
            rgb = resized[:, :, ::-1].astype(np.float32) / 255.0
            normalised = (rgb - self._mean) / self._std
            batch[i] = normalised.transpose(2, 0, 1)
        return batch

# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Adapter for getitune detection models.

getitune and torch are imported lazily inside the methods that need them, so
getitrack imports without either installed.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal

import cv2
import numpy as np

from getitrack.adapters.base import DetectionAdapter
from getitrack.core.detection import Detections

if TYPE_CHECKING:
    import torch
    from getitune.backend.lightning.models.detection.base import LightningDetectionModel
    from getitune.config.data import IntensityConfig
    from getitune.data.entity import PredictionBatch, SampleBatch

# Matches getitune placeholder class names like "label_0", "label_1".
_PLACEHOLDER_NAME = re.compile(r"^label_\d+$")

# Raw-value divisor per storage dtype for ``scale_to_unit`` intensity mapping.
_DTYPE_MAX_VALUE = {"uint8": 255.0, "uint16": 65535.0, "int16": 32767.0, "float32": 1.0}


def _intensity_scale(intensity_config: IntensityConfig | None) -> float:
    """Return the divisor mapping raw pixels to ``[0, 1]`` for the model's inputs.

    Reads the getitune ``intensity_config``; defaults to uint8 (255) when unset.
    Only ``scale_to_unit`` mode is supported, with the raw max taken from
    ``max_value`` or the storage dtype.
    """
    if intensity_config is None:
        return 255.0
    if intensity_config.mode != "scale_to_unit":
        msg = f"GetiAdapter supports intensity mode 'scale_to_unit', got '{intensity_config.mode}'"
        raise NotImplementedError(msg)
    if intensity_config.max_value is not None:
        return float(intensity_config.max_value)
    return _DTYPE_MAX_VALUE.get(intensity_config.storage_dtype, 255.0)


class GetiAdapter(DetectionAdapter):
    """Runs a getitune detection model on raw BGR frames.

    Wraps the preprocess, ``predict_step``, and postprocess round trip
    of a getitune Lightning detection model (RF-DETR, YOLOX, ...) for
    inference outside the getitune Trainer.

    Example:
        >>> adapter = GetiAdapter(model, device="cuda")
        >>> detections = adapter.detect(frame, frame_id=0)
    """

    def __init__(self, model: LightningDetectionModel, device: Literal["cpu", "cuda", "mps"] = "cpu") -> None:
        """Wrap a getitune detection model.

        Args:
            model: getitune detection model in eval mode, exposing
                ``data_input_params``, ``predict_step``, and ``label_info``.
            device: Torch device the model lives on.
        """
        self.model = model
        self.device = device
        # (mean, std) normalization tensors, built lazily on the first frame and
        # reused since the model's mean/std are fixed. None keeps torch out of __init__.
        self._norm: tuple[torch.Tensor, torch.Tensor] | None = None

    @property
    def class_names(self) -> dict[int, str] | None:
        """Class names read from the model's ``label_info``.

        getitune models trained or loaded against a dataset carry real
        names; models built from a bare class count carry generated
        ``label_N`` placeholders, for which this returns None so callers
        fall back to their own table.
        """
        names = getattr(getattr(self.model, "label_info", None), "label_names", None)
        if not names or all(_PLACEHOLDER_NAME.match(name) for name in names):
            return None
        return dict(enumerate(names))

    def detect(self, frame_bgr: np.ndarray, frame_id: int) -> Detections:
        """Run one BGR frame through the model.

        Composes `preprocess`, the model's ``predict_step``, and
        `to_detections` into the full frame-to-detections round trip.
        Requires getitune and torch.

        Args:
            frame_bgr: ``(H, W, 3)`` uint8 frame in BGR order.
            frame_id: Frame index to stamp on the returned `Detections`.

        Returns:
            `Detections` for the frame, in original frame coordinates.
        """
        import torch

        with torch.no_grad():
            preds = self.model.predict_step(self.preprocess(frame_bgr), batch_idx=0)
        return self.to_detections(preds, frame_id=frame_id)

    def preprocess(self, frame_bgr: np.ndarray) -> SampleBatch:
        """Preprocess a BGR frame into a getitune ``SampleBatch``.

        Resizes to the model's input size, maps raw pixels to ``[0, 1]`` using
        the model's ``intensity_config`` (uint8 or uint16 inputs), applies the
        model's mean/std, and sets ``scale_factor`` so predicted boxes map back
        to the original frame coordinates. Requires getitune and torch.

        Args:
            frame_bgr: ``(H, W, 3)`` uint8 or uint16 frame in BGR order, e.g.
                from ``cv2.VideoCapture``.

        Returns:
            A single-image getitune ``SampleBatch`` on ``self.device``.
        """
        import torch
        from getitune.data.entity import ImageInfo, SampleBatch

        params = self.model.data_input_params
        inp_h, inp_w = params.input_size
        ori_h, ori_w = frame_bgr.shape[:2]

        if self._norm is None:
            self._norm = (torch.tensor(params.mean).view(3, 1, 1), torch.tensor(params.std).view(3, 1, 1))
        mean_t, std_t = self._norm

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (inp_w, inp_h)).astype(np.float32)
        tensor = torch.from_numpy(resized).permute(2, 0, 1)
        tensor = tensor / _intensity_scale(params.intensity_config)
        tensor = (tensor - mean_t) / std_t

        img_info = ImageInfo(
            img_idx=0,
            img_shape=(inp_h, inp_w),
            ori_shape=(ori_h, ori_w),
            scale_factor=(inp_h / ori_h, inp_w / ori_w),
        )
        return SampleBatch(images=tensor.unsqueeze(0).to(self.device), imgs_info=[img_info])

    @staticmethod
    def to_detections(batch: PredictionBatch, frame_id: int, image_index: int = 0) -> Detections:
        """Convert one image's predictions from a getitune ``PredictionBatch``.

        Args:
            batch: A getitune ``PredictionBatch`` with per-image ``bboxes``,
                ``scores``, and ``labels`` torch tensors.
            frame_id: Frame index to stamp on the returned `Detections`.
            image_index: Which image of the batch to convert.

        Returns:
            `Detections` with float32 xyxy boxes, float32 scores, and int64
            class ids.

        Raises:
            ValueError: If the batch is missing bboxes, scores, or labels.
        """
        if batch.bboxes is None or batch.scores is None or batch.labels is None:
            msg = "PredictionBatch must carry bboxes, scores, and labels"
            raise ValueError(msg)
        return Detections(
            bboxes=batch.bboxes[image_index].detach().cpu().numpy().reshape(-1, 4).astype(np.float32),
            scores=batch.scores[image_index].detach().cpu().numpy().reshape(-1).astype(np.float32),
            class_ids=batch.labels[image_index].detach().cpu().numpy().reshape(-1).astype(np.int64),
            frame_id=frame_id,
        )

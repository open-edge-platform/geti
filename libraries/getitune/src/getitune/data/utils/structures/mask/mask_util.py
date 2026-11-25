# Copyright (C) 2023 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Utility functions for mask operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import pycocotools.mask as mask_utils
import torch
from torchvision.ops import roi_align

if TYPE_CHECKING:
    from torchvision import tv_tensors

#: Dense ``(N, H, W)`` instance masks above this many bytes are kept as :class:`RLEMasks` instead. A 20 MP image
#: with a few hundred instances is several GB dense, but a few hundred KB as RLE.
MAX_DENSE_MASK_BYTES = 256 * 1024 * 1024


def polygon_to_bitmap(
    polygons: np.ndarray,
    height: int,
    width: int,
) -> np.ndarray:
    """Convert polygons to a bitmap mask.

    Args:
        polygons: a ragged array containing np.ndarray objects of shape (Npoly, 2)
        height: bitmap height
        width: bitmap width

    Returns:
        np.ndarray: bitmap masks
    """
    # Convert to list of flat point arrays for pycocotools
    polygon_points = [points.reshape(-1) for points in polygons]
    rles = mask_utils.frPyObjects(polygon_points, height, width)
    return mask_utils.decode(rles).astype(bool).transpose((2, 0, 1))


def polygon_to_rle(
    polygons: np.ndarray,
    height: int,
    width: int,
) -> list[dict]:
    """Convert polygons to a list of RLE masks.

    Args:
        polygons: a ragged array containing np.ndarray objects of shape (Npoly, 2)
        height: bitmap height
        width: bitmap width

    Returns:
        list[dict]: List of RLE masks.
    """
    # Convert to list of flat point arrays for pycocotools
    polygon_points = [points.reshape(-1) for points in polygons]

    return mask_utils.frPyObjects(polygon_points, height, width)


def encode_rle(mask: torch.Tensor) -> dict:
    """Encodes a mask into RLE format.

    Rewrite of https://github.com/cocodataset/cocoapi/blob/master/PythonAPI/pycocotools/mask.py

    Example:
        Given M=[0 0 1 1 1 0 1] the RLE counts is [2 3 1 1].
        Or for M=[1 1 1 1 1 1 0] the RLE counts is [0 6 1].

    Args:
        mask (torch.Tensor): A binary mask (0 or 1) of shape (H, W).

    Returns:
        dict: A dictionary with keys "counts" and "size".
    """
    device = mask.device
    vector = mask.t().ravel()
    diffs = torch.diff(vector)
    next_diffs = torch.where(diffs != 0)[0] + 1

    counts = torch.diff(
        torch.cat(
            (
                torch.tensor([0], device=device),
                next_diffs,
                torch.tensor([len(vector)], device=device),
            ),
        ),
    )

    # odd counts are always the numbers of zeros
    if vector[0] == 1:
        counts = torch.cat((torch.tensor([0], device=device), counts))

    return {"counts": counts.tolist(), "size": list(mask.shape)}


def crop_and_resize_masks(
    annos: tv_tensors.Mask,
    bboxes: np.ndarray,
    out_shape: tuple,
    inds: np.ndarray,
    device: str = "cpu",
) -> torch.Tensor:
    """Crop and resize masks to the target size."""
    if len(annos) == 0:
        return torch.empty((0, *out_shape), dtype=torch.float, device=device)

    bboxes_tensor = torch.from_numpy(bboxes).to(device=device)
    inds_tensor = torch.from_numpy(inds).to(device=device)

    num_bbox = bboxes_tensor.shape[0]
    fake_inds = torch.arange(num_bbox, device=device).to(dtype=bboxes_tensor.dtype)[:, None]
    rois = torch.cat([fake_inds, bboxes_tensor], dim=1)  # Nx5
    rois = rois.to(device=device)
    if num_bbox > 0:
        gt_masks_th = annos.index_select(0, inds_tensor).to(dtype=rois.dtype)
        targets = roi_align(gt_masks_th[:, None, :, :], rois, out_shape, 1.0, 0, True).squeeze(1)
        resized_masks = targets >= 0.5
    else:
        resized_masks = torch.empty((0, *out_shape), device=device)
    return resized_masks.float()


@dataclass
class RLEMasks:
    """Instance masks of one image as COCO RLE, for images where a dense ``(N, H, W)`` tensor would not fit.

    The IS metric consumes RLE directly, so tiled evaluation of very large images never needs the dense masks.
    ``rles`` hold ``{"counts", "size": [H, W]}`` dicts, one per instance.
    """

    rles: list[dict]
    shape: tuple[int, int]

    def __len__(self) -> int:
        return len(self.rles)

    def __iter__(self):
        return iter(self.rles)

    def __getitem__(self, index) -> RLEMasks:  # noqa: ANN001
        """Select instances by slice, integer/boolean sequence or tensor."""
        if isinstance(index, slice):
            return RLEMasks(self.rles[index], self.shape)
        index = torch.as_tensor(index)
        if index.dtype == torch.bool:
            index = index.nonzero(as_tuple=True)[0]
        return RLEMasks([self.rles[i] for i in index.tolist()], self.shape)

    @classmethod
    def from_polygons(cls, polygons: np.ndarray | None, shape: tuple[int, int]) -> RLEMasks:
        """Rasterize polygons straight to RLE (no dense mask). ``shape`` is ``(H, W)``."""
        if polygons is None or len(polygons) == 0:
            return cls([], shape)
        return cls(list(polygon_to_rle(polygons, *shape)), shape)

    def to_dense(self, max_bytes: int = MAX_DENSE_MASK_BYTES) -> torch.Tensor:
        """Decode to a dense boolean ``(N, H, W)`` tensor. Refuses when that would exceed ``max_bytes``."""
        height, width = self.shape
        if len(self) * height * width > max_bytes:
            msg = f"{len(self)} masks of {height}x{width} do not fit in {max_bytes} bytes as a dense tensor"
            raise MemoryError(msg)
        if not self.rles:
            return torch.zeros((0, height, width), dtype=torch.bool)
        rles = [
            {**rle, "counts": mask_utils.frPyObjects(rle, height, width)["counts"]}
            if isinstance(rle["counts"], list)
            else rle
            for rle in self.rles
        ]
        return torch.from_numpy(mask_utils.decode(rles).astype(bool).transpose((2, 0, 1)))


def crop_to_rle(mask: np.ndarray, x: int, y: int, shape: tuple[int, int]) -> dict:
    """RLE of a full ``(H, W)`` canvas that holds ``mask`` with its top-left corner at ``(x, y)``.

    The canvas is never built: only the columns the mask touches are expanded (column-major, as RLE requires),
    so the cost depends on the object, not on the image size.

    Args:
        mask: Boolean ``(h, w)`` array.
        x: Left offset of the mask in the canvas.
        y: Top offset of the mask in the canvas.
        shape: Canvas ``(H, W)``.

    Returns:
        dict: ``{"counts": list[int], "size": [H, W]}``, equal to ``encode_rle`` of the pasted canvas.
    """
    height, width = shape
    mask = np.asarray(mask, dtype=bool)
    rows, cols = np.flatnonzero(mask.any(axis=1)), np.flatnonzero(mask.any(axis=0))
    if len(rows) == 0:
        return {"counts": [height * width], "size": [height, width]}
    mask = mask[rows[0] : rows[-1] + 1, cols[0] : cols[-1] + 1]
    x, y = x + int(cols[0]), y + int(rows[0])
    h, w = mask.shape
    # Full-height strip of the touched columns, flattened column-major.
    strip = np.zeros((height, w), dtype=bool)
    strip[y : y + h] = mask
    flat = strip.T.ravel()
    change = np.flatnonzero(flat[1:] != flat[:-1]) + 1
    runs = np.diff(np.concatenate(([0], change, [len(flat)])))
    lead = x * height
    if flat[0]:  # the strip starts with a one-run, so the zero run before it is exactly ``lead``
        counts = [lead, *runs.tolist()]
    else:  # merge the strip's first zero run into the leading zeros
        counts = [lead + int(runs[0]), *runs[1:].tolist()]
    trail = (width - x - w) * height
    if flat[-1]:  # ends with a one-run: the trailing zero run is new
        counts.append(trail)
    else:
        counts[-1] += trail
    if counts[-1] == 0 and len(counts) > 1:
        counts.pop()
    return {"counts": counts, "size": [height, width]}

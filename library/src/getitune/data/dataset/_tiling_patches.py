# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Runtime patches for Datumaro's experimental tiling.

Datumaro's :class:`InstanceMaskTiler` crops every instance mask to each tile but
does **not** implement ``is_filterable``.  As a result, instance masks are *never*
filtered during tiling: a tile keeps a mask entry for *every* instance of the
source image, even instances that do not overlap the tile at all.

Bounding boxes and (list) labels, on the other hand, *are* filterable
(``BboxTiler``/``LabelTiler``) and are pruned to the instances whose box
intersects the tile.  Consequently, after tiling an instance-segmentation
sample ends up with ``len(masks) != len(bboxes) == len(labels)``.

This desynchronisation corrupts training for every instance-segmentation model
(masks no longer correspond to their boxes/labels) and makes models that
concatenate boxes and masks per target — e.g. RF-DETR's Hungarian matcher —
crash outright with a shape-mismatch error.

The patch below re-registers a fixed ``InstanceMaskTiler`` that self-filters
instances using the **same tile-intersection criterion** as ``BboxTiler`` (the
instance's full-image mask bounding box must intersect the tile rectangle), so
masks stay aligned with boxes and labels.  Registration is idempotent and
mirrors the existing Kornia monkey-patch pattern used by the augmentation
pipeline.
"""

from __future__ import annotations

import numpy as np
import polars as pl
from datumaro.experimental.fields.masks import InstanceMaskField
from datumaro.experimental.tiling.tiler_registry import TilerRegistry
from datumaro.experimental.tiling.tilers import InstanceMaskTiler

_INSTANCE_MASK_TILER_PATCHED = False


def _instance_intersects_tile(instance: np.ndarray, x: int, y: int, width: int, height: int) -> bool:
    """Return whether an instance mask's bounding box intersects the tile.

    The criterion mirrors ``BboxTiler`` exactly: using the instance's full-image
    bounding box ``(x1, y1, x2, y2)`` (derived from its non-zero pixels, with
    ``x2``/``y2`` exclusive), the instance is kept iff::

        (x2 > tile_x) & (x1 < tile_x2) & (y2 > tile_y) & (y1 < tile_y2)

    An all-zero mask (no pixels) has no bounding box and is dropped.

    Args:
        instance: Full-image instance mask of shape ``(H, W)``.
        x: Tile left coordinate.
        y: Tile top coordinate.
        width: Tile width.
        height: Tile height.

    Returns:
        ``True`` if the instance overlaps the tile rectangle, else ``False``.
    """
    rows = np.nonzero(instance.any(axis=1))[0]
    cols = np.nonzero(instance.any(axis=0))[0]
    if rows.size == 0 or cols.size == 0:
        return False
    y1, y2 = int(rows[0]), int(rows[-1]) + 1
    x1, x2 = int(cols[0]), int(cols[-1]) + 1
    return bool((x2 > x) and (x1 < x + width) and (y2 > y) and (y1 < y + height))


class _FilteringInstanceMaskTiler(InstanceMaskTiler):
    """``InstanceMaskTiler`` that drops instances not overlapping the tile.

    Unlike the upstream tiler, this implementation prunes each tile's instance
    masks to those whose bounding box intersects the tile, keeping the mask
    count consistent with the (independently filtered) bounding boxes and
    labels.  Instances are kept in their original order, so alignment with
    boxes/labels is preserved.
    """

    def tile(self, df: pl.DataFrame, tiles_df: pl.DataFrame, slice_offset: int = 0) -> pl.DataFrame:
        """Extract and filter instance mask regions for each tile."""
        column_name = self.field_spec.name  # type: ignore[attr-defined]
        shape_column = f"{column_name}_shape"
        results_data = []
        results_shape = []

        for tile_row in tiles_df["tile"]:
            image_id = tile_row["source_sample_idx"] - slice_offset
            instances_data = df[column_name][image_id]  # Flattened 3D array
            instances_shape = df[shape_column][image_id]  # (num_instances, height, width)

            x = tile_row["x"]
            y = tile_row["y"]
            width = tile_row["width"]
            height = tile_row["height"]

            instances = instances_data.reshape(instances_shape).to_numpy()  # (N, H, W)

            # Keep only instances whose full-image bounding box intersects the
            # tile, mirroring BboxTiler so masks stay aligned with boxes/labels.
            if instances.shape[0] > 0:
                keep = np.array(
                    [_instance_intersects_tile(inst, x, y, width, height) for inst in instances],
                    dtype=bool,
                )
                instances = instances[keep]

            tile_result = instances[:, y : y + height, x : x + width]  # (M, tile_h, tile_w)

            results_data.append(tile_result.reshape(-1))
            results_shape.append(tile_result.shape)

        return pl.DataFrame(
            {
                column_name: results_data,
                shape_column: results_shape,
            }
        )


def patch_instance_mask_tiler() -> None:
    """Register the filtering instance-mask tiler (idempotent).

    Must be called before any tiling transform is created so that the fixed
    tiler is picked up by ``create_tilers``.
    """
    global _INSTANCE_MASK_TILER_PATCHED  # noqa: PLW0603
    if _INSTANCE_MASK_TILER_PATCHED:
        return
    TilerRegistry.register(InstanceMaskField)(_FilteringInstanceMaskTiler)
    _INSTANCE_MASK_TILER_PATCHED = True

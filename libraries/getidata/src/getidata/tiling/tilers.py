# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Implementations of tilers for specific field types.
"""

import operator
from collections.abc import Callable
from functools import partial
from typing import Any, Generic, TypeVar

import numpy as np
import polars as pl
import pyarrow as pa
from shapely import GeometryCollection, MultiPolygon, box, make_valid
from shapely import Polygon as ShapelyPolygon
from shapely.errors import GEOSException
from shapely.geometry.base import BaseGeometry

from getidata.fields import (
    BBoxField,
    ImageField,
    ImageInfoField,
    InstanceMaskField,
    LabelField,
    MaskField,
    PolygonField,
    SubsetField,
)
from getidata.schema import AttributeSpec
from getidata.type_registry import polars_to_numpy_dtype

from .tiler_registry import Tiler, TilerRegistry

_T = TypeVar("_T")


class _LastImageCache(Generic[_T]):
    """Single-slot cache keyed on the source image index.

    Tiles are generated grouped by source image: ``_calculate_tiles`` iterates
    images in order and emits every tile of one image before moving on to the
    next, so a tiler's :meth:`tile` sees tiles contiguously per image. A cache
    holding only the **last seen** image therefore captures all the reuse
    (every run of tiles that share a source image) while keeping memory bounded
    to a single image's derived data.

    This is preferred over a per-image dictionary, which would grow unbounded
    across the whole dataset and risk out-of-memory errors on large datasets
    (many images) or memory-heavy per-image payloads (e.g. reshaped mask
    stacks).
    """

    __slots__ = ("_image_id", "_value")

    def __init__(self) -> None:
        self._image_id: int | None = None
        self._value: _T | None = None

    def get(self, image_id: int, factory: Callable[[], _T]) -> _T:
        """Return the cached value for ``image_id``, computing it on a miss.

        On a cache miss (a different image than the previous call) the previous
        entry is evicted before ``factory`` is invoked, so at most one image's
        data is retained at any time.
        """
        if image_id != self._image_id:
            self._image_id = image_id
            self._value = factory()
        return self._value  # type: ignore[return-value]


@TilerRegistry.register(SubsetField)
class PassthroughTiler(Tiler):
    """Tiler for fields which do not require any changes (e.g. subset)."""

    field_spec: AttributeSpec[Any]

    def tile(self, df: pl.DataFrame, tiles_df: pl.DataFrame, slice_offset: int = 0) -> pl.DataFrame:
        """Process labels, adding keep column for list fields."""
        column_name = self.field_spec.name
        source_sample_idx = (
            tiles_df.select(pl.col("tile").struct["source_sample_idx"])["source_sample_idx"] - slice_offset
        )

        # Just a passthrough of the data
        return pl.DataFrame({column_name: df[column_name].gather(source_sample_idx)})


@TilerRegistry.register(MaskField)
class MaskTiler(Tiler):
    """Tiler for semantic segmentation masks.

    Extracts the corresponding region from the mask for each tile.
    The mask values (class labels) are preserved as is.
    """

    field_spec: AttributeSpec[MaskField]

    def tile(self, df: pl.DataFrame, tiles_df: pl.DataFrame, slice_offset: int = 0) -> pl.DataFrame:
        """Extract mask regions for each tile."""
        column_name = self.field_spec.name
        shape_column = f"{column_name}_shape"
        results_data = []
        results_shape = []

        # Cache the reshaped mask per source image so the O(H*W) reshape +
        # to_numpy conversion is paid at most once per image instead of once per
        # tile. Tiles are processed contiguously per image, so a single-slot
        # cache is sufficient and keeps memory bounded to one image.
        mask_cache: _LastImageCache[np.ndarray] = _LastImageCache()

        for tile_row in tiles_df["tile"]:
            image_id = tile_row["source_sample_idx"] - slice_offset
            mask = mask_cache.get(
                image_id,
                lambda: df[column_name][image_id].reshape(df[shape_column][image_id]).to_numpy(),
            )

            # Get tile coordinates
            x = tile_row["x"]
            y = tile_row["y"]
            width = tile_row["width"]
            height = tile_row["height"]

            # Extract tile region from the (cached) reshaped mask
            tile_mask = mask[y : y + height, x : x + width]

            # Return flattened tile
            results_data.append(tile_mask.reshape(-1))
            results_shape.append(list(tile_mask.shape))

        return pl.DataFrame({column_name: results_data, shape_column: results_shape})


def _instance_bounding_boxes(instances: np.ndarray) -> np.ndarray:
    """Compute per-instance full-image bounding boxes from a mask stack.

    Scans each instance mask **once** to derive its bounding box
    ``(x1, y1, x2, y2)`` (from non-zero pixels, with ``x2``/``y2`` exclusive).
    Instances with no pixels (all-zero masks) yield a degenerate ``(0, 0, 0, 0)``
    box which never intersects any tile (see :func:`_boxes_intersect_tile`), so
    they are effectively dropped.

    Args:
        instances: Full-image instance masks of shape ``(N, H, W)``.

    Returns:
        Integer array of shape ``(N, 4)`` holding ``(x1, y1, x2, y2)`` per
        instance.
    """
    num_instances = instances.shape[0]
    boxes = np.zeros((num_instances, 4), dtype=np.int64)
    if num_instances == 0:
        return boxes

    # Reduce over the full mask once per instance (the only O(H*W) pass).
    rows_any = instances.any(axis=2)  # (N, H): rows containing any pixel
    cols_any = instances.any(axis=1)  # (N, W): cols containing any pixel
    for i in range(num_instances):
        rows = np.nonzero(rows_any[i])[0]
        cols = np.nonzero(cols_any[i])[0]
        if rows.size == 0 or cols.size == 0:
            continue
        boxes[i] = (cols[0], rows[0], cols[-1] + 1, rows[-1] + 1)
    return boxes


def _boxes_intersect_tile(boxes: np.ndarray, x: int, y: int, width: int, height: int) -> np.ndarray:
    """Vectorized bbox-vs-tile intersection test.

    The criterion mirrors :class:`BboxTiler` exactly: an instance whose
    full-image bounding box is ``(x1, y1, x2, y2)`` is kept iff::

        (x2 > tile_x) & (x1 < tile_x2) & (y2 > tile_y) & (y1 < tile_y2)

    Args:
        boxes: Integer array of shape ``(N, 4)`` of ``(x1, y1, x2, y2)`` boxes.
        x: Tile left coordinate.
        y: Tile top coordinate.
        width: Tile width.
        height: Tile height.

    Returns:
        Boolean array of shape ``(N,)`` marking intersecting instances.
    """
    if boxes.shape[0] == 0:
        return np.zeros((0,), dtype=bool)
    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    return (x2 > x) & (x1 < x + width) & (y2 > y) & (y1 < y + height)


@TilerRegistry.register(InstanceMaskField)
class InstanceMaskTiler(Tiler):
    """Tiler for instance segmentation masks.

    Extracts the corresponding region from each instance mask and prunes
    instances that do not overlap the tile.

    Instance masks are stored as a flattened array plus a separate shape column.
    When bounding boxes or polygons are available, the tiling transform passes
    their shared keep flags to preserve instance alignment. Otherwise, masks are
    filtered by whether their bounding boxes intersect the tile.
    """

    field_spec: AttributeSpec[InstanceMaskField]

    def tile(
        self,
        df: pl.DataFrame,
        tiles_df: pl.DataFrame,
        slice_offset: int = 0,
        keep_masks: pl.Series | None = None,
    ) -> pl.DataFrame:
        """Extract and filter instance mask regions for each tile."""
        column_name = self.field_spec.name
        shape_column = f"{column_name}_shape"
        results_data = []
        results_shape = []
        keeps = []

        # Cache per source image so the O(H*W) mask reshape (and, when no keep flags are
        # supplied, the bbox derivation) is paid at most once per image instead of once per tile.
        # Many tiles typically share the same source image, so this avoids
        # O(num_tiles * num_instances * H * W) work on large / dense images.
        # Tiles are processed contiguously per image (see _calculate_tiles), so a
        # single-slot cache captures all the reuse while keeping memory bounded
        # to one image -- avoiding the unbounded growth (and OOM risk on large
        # datasets) of a per-image dictionary.
        cache: _LastImageCache[tuple[np.ndarray, np.ndarray | None]] = _LastImageCache()

        def _load(image_id: int) -> tuple[np.ndarray, np.ndarray | None]:
            instances_data = df[column_name][image_id]  # Flattened 3D array
            instances_shape = df[shape_column][image_id]  # (num_instances, height, width)
            # Reshape flattened data once per image: (N, H, W)
            instances = instances_data.reshape(instances_shape).to_numpy()
            return instances, _instance_bounding_boxes(instances) if keep_masks is None else None

        for tile_index, tile_row in enumerate(tiles_df["tile"]):
            image_id = tile_row["source_sample_idx"] - slice_offset
            instances, boxes = cache.get(image_id, lambda: _load(image_id))

            # Get tile coordinates
            x = tile_row["x"]
            y = tile_row["y"]
            width = tile_row["width"]
            height = tile_row["height"]

            if keep_masks is not None:
                keep = np.asarray(keep_masks[tile_index], dtype=bool)
                if len(keep) != len(instances):
                    raise ValueError("Instance masks are not aligned with the other annotations")
            elif boxes is not None:
                keep = _boxes_intersect_tile(boxes, x, y, width, height)
            else:
                keep = np.zeros(0, dtype=bool)
            kept_instances = instances[keep]

            # Extract tile region: shape (num_kept_instances, tile_height, tile_width)
            tile_result = kept_instances[:, y : y + height, x : x + width]

            # Flatten result for storage
            results_data.append(tile_result.reshape(-1))
            results_shape.append(tile_result.shape)
            keeps.append(keep.tolist())

        return pl.DataFrame(
            {
                column_name: results_data,
                shape_column: results_shape,
                "keep": pl.Series(keeps, dtype=pl.List(pl.Boolean())),
            }
        )


@TilerRegistry.register(BBoxField)
class BboxTiler(Tiler):
    """Tiler for bounding box annotations.

    Handles:
    - Adjusting bbox coordinates relative to tile origin
    - Filtering out boxes that don't intersect with tile, or whose visible area is below
      ``threshold_drop_ann`` of their full area
    - Adding keep flags for filtering
    """

    field_spec: AttributeSpec[BBoxField]
    threshold_drop_ann: float = 0.5  # Proportion of area below which to drop annotation

    def is_filterable(self) -> bool:
        return True

    def tile(self, df: pl.DataFrame, tiles_df: pl.DataFrame, slice_offset: int = 0) -> pl.DataFrame:
        """Process bounding boxes for each tile."""
        column_name = self.field_spec.name

        if self.field_spec.field.format != "x1y1x2y2":
            raise RuntimeError(f"The format {self.field_spec.field.format} is not supported.")

        out_dtype = self.field_spec.field.dtype
        np_dtype = polars_to_numpy_dtype(out_dtype) if out_dtype is not None else np.float32
        bboxes_out: list[np.ndarray] = []
        keeps_out: list[np.ndarray] = []

        # The per-image boxes only depend on the source image, not the tile. Tiles are processed contiguously per
        # image, so a single-slot cache is enough. Plain numpy per tile: a polars query per tile dominates the cost
        # for images with hundreds of tiles.
        boxes_cache: _LastImageCache[np.ndarray] = _LastImageCache()

        def _load_boxes(image_id: int) -> np.ndarray:
            raw = df[image_id, column_name]
            if raw is None or len(raw) == 0:
                return np.zeros((0, 4), dtype=np_dtype)
            return np.asarray(raw, dtype=np_dtype).reshape(-1, 4)

        for tile_row in tiles_df["tile"]:
            image_id = tile_row["source_sample_idx"] - slice_offset
            boxes = boxes_cache.get(image_id, partial(_load_boxes, image_id))

            tile_x = tile_row["x"]
            tile_y = tile_row["y"]
            tile_x2 = tile_x + tile_row["width"]
            tile_y2 = tile_y + tile_row["height"]
            x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]

            # Area of the original box (before clipping), for the threshold rule below.
            full_area = (x2 - x1) * (y2 - y1)
            keep = (x2 > tile_x) & (x1 < tile_x2) & (y2 > tile_y) & (y1 < tile_y2)

            # Visible (clipped) part of the box, relative to the tile origin.
            cx1 = np.maximum(x1, tile_x) - tile_x
            cy1 = np.maximum(y1, tile_y) - tile_y
            cx2 = np.minimum(x2, tile_x2) - tile_x
            cy2 = np.minimum(y2, tile_y2) - tile_y

            # Drop annotations whose visible part is below the configured ratio of their full area
            # (visible_area >= 0 * full_area is always true, so threshold 0 keeps any intersection).
            visible_area = (cx2 - cx1) * (cy2 - cy1)
            keep &= visible_area >= self.threshold_drop_ann * full_area

            bboxes_out.append(np.stack([cx1, cy1, cx2, cy2], axis=1).astype(np_dtype, copy=False))
            keeps_out.append(keep)

        # Build both list columns from flat buffers plus offsets (one Arrow call each) instead of per-tile python
        # lists, which polars converts element by element: tens of millions of boxes for a large tiled dataset.
        offsets = pa.array(np.concatenate([[0], np.cumsum([len(k) for k in keeps_out])]).astype(np.int32))
        flat_boxes = np.concatenate(bboxes_out) if bboxes_out else np.zeros((0, 4), dtype=np_dtype)
        flat_keep = np.concatenate(keeps_out) if keeps_out else np.zeros(0, dtype=bool)
        boxes_arrow = pa.ListArray.from_arrays(
            offsets, pa.FixedSizeListArray.from_arrays(pa.array(flat_boxes.reshape(-1)), 4)
        )
        keep_arrow = pa.ListArray.from_arrays(offsets, pa.array(flat_keep))
        return pl.DataFrame(
            {
                column_name: pl.from_arrow(boxes_arrow).cast(df.schema[column_name]),
                "keep": pl.from_arrow(keep_arrow).cast(pl.List(pl.Boolean())),
            }
        )


@TilerRegistry.register(LabelField)
class LabelTiler(Tiler):
    """Tiler for label fields.

    For single labels, just passes through the data.
    For list fields, adds a keep column to mark all elements for inclusion
    in final filtering.
    """

    field_spec: AttributeSpec[LabelField]

    def is_filterable(self) -> bool:
        return self.field_spec.field.is_list

    def tile(self, df: pl.DataFrame, tiles_df: pl.DataFrame, slice_offset: int = 0) -> pl.DataFrame:
        """Process labels, adding keep column for list fields."""
        column_name = self.field_spec.name

        # For list fields, need to create keep flags for each element
        if self.field_spec.field.is_list:
            keeps = []
            labels = []
            for tile_row in tiles_df["tile"]:
                source_sample_idx = tile_row["source_sample_idx"] - slice_offset
                source_labels = df[source_sample_idx, column_name]
                # Create list of True values matching label list length
                keeps.append([True] * len(source_labels))
                labels.append(source_labels)

            # Return both the original labels and keep flags
            return pl.DataFrame({column_name: labels, "keep": keeps})

        # For non-list fields, just pass through the data
        return pl.DataFrame({column_name: df[column_name].take(tiles_df["source_sample_idx"])})


@TilerRegistry.register(ImageInfoField)
class ImageInfoTiler(Tiler):
    """Tiler for image info metadata.

    This tiler updates image dimensions and metadata for each tile.
    """

    field_spec: AttributeSpec[ImageInfoField]

    def tile(self, df: pl.DataFrame, tiles_df: pl.DataFrame, slice_offset: int = 0) -> pl.DataFrame:
        """Update image info for each tile."""
        results = []

        # Process each tile
        for tile_row in tiles_df["tile"]:
            # Get basic tile info
            source_sample_idx = tile_row["source_sample_idx"] - slice_offset
            tile_width = tile_row["width"]
            tile_height = tile_row["height"]

            # Create new image info for the tile
            tile_info = {
                "width": tile_width,
                "height": tile_height,
                "source_sample_idx": source_sample_idx,
            }

            # Add any additional info from original image
            original_info = df[source_sample_idx][self.field_spec.name]
            if isinstance(original_info, dict):
                # Copy relevant metadata but exclude size information
                for key, value in original_info.items():
                    if key not in ("width", "height"):
                        tile_info[key] = value

            results.append({self.field_spec.name: tile_info})

        return pl.DataFrame(results)


@TilerRegistry.register(ImageField)
class ImageTiler(Tiler):
    """Tiler for image data stored as numpy arrays."""

    field_spec: AttributeSpec[ImageField]

    def tile(self, df: pl.DataFrame, tiles_df: pl.DataFrame, slice_offset: int = 0) -> pl.DataFrame:
        """Tile images in the DataFrame."""

        column_name = self.field_spec.name
        shape_column = f"{column_name}_shape"

        def extract_tile(
            image_data: np.ndarray,
            image_shape: tuple[int, ...],
            tile_box: tuple[int, int, int, int],
        ) -> np.ndarray:
            """Extract a tile from flattened image data."""
            # Reshape the flattened data
            image = image_data.reshape(image_shape).to_numpy()

            # Extract coordinates
            y1, x1, h, w = tile_box
            y2, x2 = y1 + h, x1 + w

            # Extract tile
            tile = image[y1:y2, x1:x2]

            # Return flattened tile
            return tile.reshape(-1), tile.shape

        results_data = []
        results_shape = []
        for tile_row in tiles_df["tile"]:
            source_idx = tile_row["source_sample_idx"] - slice_offset

            # Get image data and shape
            image_data = df[source_idx, column_name]
            image_shape = df[source_idx, shape_column]

            # Extract tile
            tile_box = (tile_row["y"], tile_row["x"], tile_row["height"], tile_row["width"])
            tile_data, tile_shape = extract_tile(image_data, image_shape, tile_box)

            results_data.append(tile_data)
            results_shape.append(tile_shape)

        results = {column_name: pl.Series(results_data), f"{column_name}_shape": results_shape}

        return pl.DataFrame(results)


def _polygons_of_image(df: pl.DataFrame, row: int, column_name: str) -> "_ImagePolygons":
    return _ImagePolygons(df[row, column_name])


class _ImagePolygons:
    """Polygon rings of one source image with their bounding boxes, for cheap per-tile pre-selection."""

    def __init__(self, raw: pl.Series | None) -> None:
        polygons = [] if raw is None else raw.to_list()
        self.rings = [
            np.asarray(p, dtype=np.float64).reshape(-1, 2) if p is not None else np.zeros((0, 2)) for p in polygons
        ]
        self.count = len(self.rings)
        self.repaired: set[int] = set()  # rings that were invalid (e.g. self-intersecting) and got repaired
        bounds = np.array(
            [[*r.min(axis=0), *r.max(axis=0)] if len(r) else [np.inf, np.inf, -np.inf, -np.inf] for r in self.rings]
        ).reshape(-1, 4)
        self.x0, self.y0, self.x1, self.y1 = bounds.T
        self._polygons: dict[int, ShapelyPolygon | BaseGeometry | None] = {}

    def shoelace_area(self, i: int) -> float:
        x, y = self.rings[i].T
        return abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))) / 2

    def polygon(self, i: int) -> BaseGeometry | None:
        """Shapely geometry of polygon ``i``; invalid (e.g. self-intersecting) input is repaired, else None."""
        if i not in self._polygons:
            try:
                polygon = ShapelyPolygon(self.rings[i])
                if not polygon.is_valid:
                    self.repaired.add(i)
                    polygon = make_valid(polygon)
                self._polygons[i] = polygon
            except ValueError:  # fewer than 3 distinct points
                self._polygons[i] = None
        return self._polygons[i]


@TilerRegistry.register(PolygonField)
class PolygonTiler(Tiler):
    """Tiler for polygon annotations."""

    field_spec: AttributeSpec[PolygonField]
    threshold_drop_ann: float = 0.5  # Proportion of area below which to drop annotation

    def is_filterable(self) -> bool:
        return True

    def tile(self, df: pl.DataFrame, tiles_df: pl.DataFrame, slice_offset: int = 0) -> pl.DataFrame:
        """Tile polygon annotations in the DataFrame.

        Args:
            df: Input DataFrame containing polygon annotations
            tiles_df: DataFrame containing tile parameters
            slice_offset: Integer offset to subtract when accessing df based on
                        source_sample_idx. Used when df is a subset of another
                        DataFrame. Defaults to 0.

        Returns:
            DataFrame containing:
            - column_name: tiled polygon annotations
            - keep: List[bool] series indicating which polygons to keep
        """
        column_name = self.field_spec.name
        out_dtype = self.field_spec.field.dtype
        np_dtype = polars_to_numpy_dtype(out_dtype) if out_dtype is not None else np.float32

        # Per-image data, computed once per image (tiles of one image are contiguous, see ``_LastImageCache``).
        image_cache: _LastImageCache[_ImagePolygons] = _LastImageCache()

        vertices: list[np.ndarray] = []  # kept rings, in tile then polygon order
        ring_lengths: list[np.ndarray] = []  # per tile: vertices of every polygon (0 for dropped ones)
        keeps: list[np.ndarray] = []

        for tile_row in tiles_df["tile"]:
            source_idx = tile_row["source_sample_idx"] - slice_offset
            image = image_cache.get(source_idx, partial(_polygons_of_image, df, source_idx, column_name))
            tx0, ty0 = tile_row["x"], tile_row["y"]
            tx1, ty1 = tx0 + tile_row["width"], ty0 + tile_row["height"]

            lengths = np.zeros(image.count, dtype=np.int64)
            keep = np.zeros(image.count, dtype=bool)
            # Polygons whose bounding box misses the tile cannot intersect it. Those fully inside are kept as they are;
            # only the ones crossing the tile edge need a (comparatively slow) geometric clip.
            overlaps = (image.x1 > tx0) & (image.x0 < tx1) & (image.y1 > ty0) & (image.y0 < ty1)
            inside = overlaps & (image.x0 >= tx0) & (image.x1 <= tx1) & (image.y0 >= ty0) & (image.y1 <= ty1)
            tile_poly = None
            for i in np.flatnonzero(overlaps):
                polygon = image.polygon(i)  # cached per image; repairs invalid rings
                if polygon is None:
                    continue
                if inside[i] and i not in image.repaired:
                    ring = image.rings[i]
                    if image.shoelace_area(i) <= 0:
                        continue
                    ring = np.vstack([ring, ring[:1]])  # closed ring, as a clip would return
                else:
                    if polygon.area <= 0:
                        continue
                    tile_poly = tile_poly or box(tx0, ty0, tx1, ty1)
                    ring, clipped_area = self._clip(polygon, tile_poly)
                    if ring is None or clipped_area is None or clipped_area < self.threshold_drop_ann * polygon.area:
                        continue
                vertices.append(ring - (tx0, ty0))
                lengths[i] = len(ring)
                keep[i] = True
            ring_lengths.append(lengths)
            keeps.append(keep)

        # Build the nested list column from flat buffers plus offsets (one Arrow call per level) instead of
        # per-polygon polars Series. Dropped polygons are empty rings; the keep flags remove them afterwards.
        flat = np.concatenate(vertices).astype(np_dtype, copy=False) if vertices else np.zeros((0, 2), dtype=np_dtype)
        polygon_offsets = pa.array(np.concatenate([[0], np.cumsum(np.concatenate(ring_lengths))]).astype(np.int32))
        tile_offsets = pa.array(np.concatenate([[0], np.cumsum([len(k) for k in keeps])]).astype(np.int32))
        rings_arrow = pa.ListArray.from_arrays(
            polygon_offsets, pa.FixedSizeListArray.from_arrays(pa.array(flat.reshape(-1)), 2)
        )
        polygons_arrow = pa.ListArray.from_arrays(tile_offsets, rings_arrow)
        flat_keep = np.concatenate(keeps) if keeps else np.zeros(0, dtype=bool)
        keep_arrow = pa.ListArray.from_arrays(tile_offsets, pa.array(flat_keep))
        return pl.DataFrame(
            {
                column_name: pl.from_arrow(polygons_arrow).cast(df.schema[column_name]),
                "keep": pl.from_arrow(keep_arrow).cast(pl.List(pl.Boolean())),
            }
        )

    @staticmethod
    def _clip(polygon: BaseGeometry, tile_poly: BaseGeometry) -> tuple[np.ndarray | None, float | None]:
        """Return (exterior ring, area) of the largest polygonal part of ``polygon`` inside ``tile_poly``.

        ``(None, None)`` when nothing usable remains, including when GEOS rejects an invalid input geometry.
        """
        try:
            intersection = polygon.intersection(tile_poly)
        except GEOSException:
            return None, None
        # NOTE: intersection may return a GeometryCollection or MultiPolygon
        if isinstance(intersection, GeometryCollection | MultiPolygon):
            shapes = [g for g in intersection.geoms if isinstance(g, ShapelyPolygon) and g.is_valid]
            if not shapes:
                return None, None
            intersection = max(shapes, key=operator.attrgetter("area"))
        if not isinstance(intersection, ShapelyPolygon) or intersection.is_empty or not intersection.is_valid:
            return None, None
        return np.asarray(intersection.exterior.coords), intersection.area

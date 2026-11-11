# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Implementations of tilers for specific field types.
"""

import operator
from collections.abc import Callable
from typing import Any, Generic, TypeVar

import numpy as np
import polars as pl
from shapely import GeometryCollection, MultiPolygon, box, transform
from shapely import Polygon as ShapelyPolygon
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

    Instance masks are stored as a flattened array plus a separate shape column,
    a format that the coordinated ``keep``-column filtering mechanism (used by
    :class:`BboxTiler` and :class:`LabelTiler`) cannot express. To keep masks
    aligned with the independently filtered bounding boxes and labels, this
    tiler self-filters instances using the **same tile-intersection criterion**
    as :class:`BboxTiler` (the instance's full-image mask bounding box must
    intersect the tile rectangle). Instances are kept in their original order so
    alignment with boxes/labels is preserved.
    """

    field_spec: AttributeSpec[InstanceMaskField]

    def tile(self, df: pl.DataFrame, tiles_df: pl.DataFrame, slice_offset: int = 0) -> pl.DataFrame:
        """Extract and filter instance mask regions for each tile."""
        column_name = self.field_spec.name
        shape_column = f"{column_name}_shape"
        results_data = []
        results_shape = []

        # Cache per source image so the O(H*W) mask scan (reshape + bbox
        # derivation) is paid at most once per image instead of once per tile.
        # Many tiles typically share the same source image, so this avoids
        # O(num_tiles * num_instances * H * W) work on large / dense images.
        # Tiles are processed contiguously per image (see _calculate_tiles), so a
        # single-slot cache captures all the reuse while keeping memory bounded
        # to one image -- avoiding the unbounded growth (and OOM risk on large
        # datasets) of a per-image dictionary.
        cache: _LastImageCache[tuple[np.ndarray, np.ndarray]] = _LastImageCache()

        def _load(image_id: int) -> tuple[np.ndarray, np.ndarray]:
            instances_data = df[column_name][image_id]  # Flattened 3D array
            instances_shape = df[shape_column][image_id]  # (num_instances, height, width)
            # Reshape flattened data once per image: (N, H, W)
            instances = instances_data.reshape(instances_shape).to_numpy()
            return instances, _instance_bounding_boxes(instances)

        for tile_row in tiles_df["tile"]:
            image_id = tile_row["source_sample_idx"] - slice_offset
            instances, boxes = cache.get(image_id, lambda: _load(image_id))

            # Get tile coordinates
            x = tile_row["x"]
            y = tile_row["y"]
            width = tile_row["width"]
            height = tile_row["height"]

            # Keep only instances whose (cached) full-image bounding box
            # intersects the tile, mirroring BboxTiler so masks stay aligned
            # with boxes/labels. This is a cheap vectorized check per tile.
            if instances.shape[0] > 0:
                keep = _boxes_intersect_tile(boxes, x, y, width, height)
                kept_instances = instances[keep]
            else:
                kept_instances = instances

            # Extract tile region: shape (num_kept_instances, tile_height, tile_width)
            tile_result = kept_instances[:, y : y + height, x : x + width]

            # Flatten result for storage
            results_data.append(tile_result.reshape(-1))
            results_shape.append(tile_result.shape)

        return pl.DataFrame(
            {
                column_name: results_data,
                shape_column: results_shape,
            }
        )


@TilerRegistry.register(BBoxField)
class BboxTiler(Tiler):
    """Tiler for bounding box annotations.

    Handles:
    - Adjusting bbox coordinates relative to tile origin
    - Filtering out boxes that don't intersect with tile
    - Adding keep flags for filtering
    """

    field_spec: AttributeSpec[BBoxField]

    def is_filterable(self) -> bool:
        return True

    def tile(self, df: pl.DataFrame, tiles_df: pl.DataFrame, slice_offset: int = 0) -> pl.DataFrame:
        """Process bounding boxes for each tile."""
        column_name = self.field_spec.name

        if self.field_spec.field.format != "x1y1x2y2":
            raise RuntimeError(f"The format {self.field_spec.field.format} is not supported.")

        results = []

        # Cache the per-image exploded/split boxes (the part that only depends on
        # the source image, not the tile) so it is computed once per image rather
        # than once per tile. Tiles are processed contiguously per image, so a
        # single-slot cache is sufficient and keeps memory bounded to one image.
        # NOTE: bbox payloads are small, so this is a modest speedup rather than
        # an OOM safeguard (unlike the mask tilers), but it keeps the caching
        # strategy consistent across tilers.
        boxes_cache: _LastImageCache[pl.DataFrame] = _LastImageCache()

        def _load_boxes(image_id: int) -> pl.DataFrame:
            boxes = df[image_id].select(column_name).explode(column_name)
            return boxes.with_columns(
                x1=pl.col(column_name).arr.get(0),
                y1=pl.col(column_name).arr.get(1),
                x2=pl.col(column_name).arr.get(2),
                y2=pl.col(column_name).arr.get(3),
            )

        for tile_row in tiles_df["tile"]:
            image_id = tile_row["source_sample_idx"] - slice_offset
            # with_columns below returns new frames, so the cached frame is never mutated.
            boxes = boxes_cache.get(image_id, lambda: _load_boxes(image_id))

            # Get tile coordinates
            tile_x = tile_row["x"]
            tile_y = tile_row["y"]
            tile_width = tile_row["width"]
            tile_height = tile_row["height"]
            tile_x2 = tile_x + tile_width
            tile_y2 = tile_y + tile_height

            # Check if box intersects with tile
            boxes = boxes.with_columns(
                keep=(pl.col("x2") > tile_x)
                & (pl.col("x1") < tile_x2)
                & (pl.col("y2") > tile_y)
                & (pl.col("y1") < tile_y2)
            )

            # Calculate intersection
            boxes = boxes.with_columns(
                pl.col("x1").clip(lower_bound=tile_x) - tile_x,
                pl.col("y1").clip(lower_bound=tile_y) - tile_y,
                pl.col("x2").clip(upper_bound=tile_x2) - tile_x,
                pl.col("y2").clip(upper_bound=tile_y2) - tile_y,
            )

            boxes = boxes.with_columns(bboxes=pl.concat_arr("x1", "y1", "x2", "y2"))

            boxes = boxes.group_by(pl.lit(1)).agg(pl.col("bboxes", "keep")).drop("literal")

            results.append(boxes)

        return pl.concat(results)


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


def _apply_offset(geom: BaseGeometry, offset_x: float, offset_y: float) -> BaseGeometry:
    """Apply offset to geometry."""
    return transform(geometry=geom, transformation=lambda x, y: (x - offset_x, y - offset_y), interleaved=False)


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
        results = []
        keeps = []

        column_name = self.field_spec.name

        for tile_row in tiles_df["tile"]:
            source_idx = tile_row["source_sample_idx"] - slice_offset
            source_polygons = df[source_idx, column_name]

            # Create tile polygon
            tile_poly = box(
                tile_row["x"],
                tile_row["y"],
                tile_row["x"] + tile_row["width"],
                tile_row["y"] + tile_row["height"],
            )

            # Process each polygon
            tiled_polygons = []
            polygon_keeps = []  # Track which polygons to keep

            for poly_coords in source_polygons:
                polygon = ShapelyPolygon(poly_coords)

                # Get intersection and apply offset
                intersection = polygon.intersection(tile_poly)

                # NOTE: intersection may return a GeometryCollection or MultiPolygon
                if isinstance(intersection, GeometryCollection | MultiPolygon):
                    shapes = [(geom, geom.area) for geom in list(intersection.geoms) if geom.is_valid]
                    if not shapes:
                        tiled_polygons.append(None)  # Placeholder for dropped polygon
                        polygon_keeps.append(False)
                        continue

                    intersection, _ = max(shapes, key=operator.itemgetter(1))

                if not isinstance(intersection, ShapelyPolygon) or intersection.is_empty or not intersection.is_valid:
                    tiled_polygons.append(None)  # Placeholder for dropped polygon
                    polygon_keeps.append(False)
                    continue

                prop_area = intersection.area / polygon.area

                if prop_area < self.threshold_drop_ann:
                    tiled_polygons.append(None)  # Placeholder for dropped polygon
                    polygon_keeps.append(False)
                    continue

                offset_poly = _apply_offset(intersection, tile_row["x"], tile_row["y"])

                tiled_polygons.append(np.array(offset_poly.exterior.coords))
                polygon_keeps.append(True)

            # Always create output row
            results.append(
                pl.Series(
                    [pl.Series(polygon, dtype=pl.Array(self.field_spec.field.dtype, 2)) for polygon in tiled_polygons]
                )
            )
            keeps.append(polygon_keeps)

        # Create DataFrame with results and keep column as List[Boolean]
        return pl.DataFrame({column_name: results, "keep": pl.Series(keeps, dtype=pl.List(pl.Boolean()))})

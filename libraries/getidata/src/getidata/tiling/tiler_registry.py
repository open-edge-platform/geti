# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Registry system for tiling operations on datasets.

This module provides the foundation for tiling operations, including tiler
registration and configuration management.
"""

import copy
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import NamedTuple

import polars as pl

from getidata.fields import ImageInfoField, TileField, TileInfo
from getidata.schema import AttributeInfo, AttributeSpec, Field, Schema
from getidata.transform import Transform


@dataclass
class TilingConfig:
    """Configuration for tiling operations.

    This class defines the parameters for how an image or other 2D data should be
    divided into tiles. It supports both regular tiling and overlapping tiles.

    Attributes:
        tile_width: Width of each tile in pixels
        tile_height: Height of each tile in pixels
        overlap_x: Horizontal overlap between adjacent tiles in pixels
        overlap_y: Vertical overlap between adjacent tiles in pixels

    Example:
        ```python
        # Create config for 512x512 tiles with 64px overlap
        config = TilingConfig(
            tile_width=512,
            tile_height=512,
            overlap_x=64,
            overlap_y=64
        )
        ```
    """

    tile_width: int
    tile_height: int
    overlap_x: float = 0.0
    overlap_y: float = 0.0


def _calculate_tiles(
    df: pl.DataFrame,
    config: TilingConfig,
    image_info_spec: AttributeSpec[ImageInfoField],
    tile_info_spec: AttributeSpec[TileField],
    slice_offset: int,
) -> pl.DataFrame:
    """Calculate tile parameters for each image in the dataset.

    This function divides each image into tiles according to the provided configuration,
    handling edge cases and overlaps. For each tile, it calculates the position and
    dimensions while ensuring tiles don't exceed image boundaries.

    Args:
        df: Input DataFrame containing image info. Must have columns for image
            dimensions (height, width) under the image_info_spec field.
        config: Tiling configuration specifying tile sizes and overlap.
        image_info_spec: Specification for the input image info field, used to
            extract image dimensions.
        tile_info_spec: Specification for the output tile info field, defines
            the structure of the tile parameters.

    Returns:
        DataFrame containing tile parameters using TileInfo structure. Each row
        represents one tile with its position (x, y), dimensions (width, height)
        and reference to the source image (source_sample_idx).
    """
    tiles = []
    field = tile_info_spec.field

    for idx, row in enumerate(df.iter_rows(named=True)):
        # Get image dimensions directly from row
        image_info = row[image_info_spec.name]
        if image_info is None:
            continue

        height = image_info["height"]
        width = image_info["width"]

        increment_x = int(config.tile_width * (1 - config.overlap_x))
        increment_y = int(config.tile_height * (1 - config.overlap_y))

        for y in range(0, height, increment_y):
            for x in range(0, width, increment_x):
                # Ensure tiles don't exceed image boundaries
                tile_width = min(config.tile_width, width - x)
                tile_height = min(config.tile_height, height - y)

                tile_info = TileInfo(
                    source_sample_idx=idx + slice_offset,
                    x=x,
                    y=y,
                    width=tile_width,
                    height=tile_height,
                )

                # Convert tile info to polars using the field
                tile_data = field.to_polars(tile_info_spec.name, tile_info)
                tiles.append(tile_data)

    # Combine all tile data into a single DataFrame
    return pl.concat([pl.DataFrame(t) for t in tiles])


class Tiler(ABC):
    """Base class for all tilers.

    A Tiler is responsible for processing a specific type of field (images, masks,
    annotations, etc.) during the tiling operation. Each tiler implements the logic
    for how its field type should be divided across tiles.

    Tilers can optionally support filtering by implementing is_filterable() and
    providing a 'keep' column in their output DataFrame. This is useful for
    annotations like polygons or bounding boxes that may or may not be present
    in each tile.

    Attributes:
        field_spec: Specification of the field this tiler handles

    Example:
        ```python
        @TilerRegistry.register(ImageField)
        class ImageTiler(Tiler):
            def tile(self, df, tiles_df):
                # Implementation for tiling image data
                ...
        ```
    """

    def is_filterable(self) -> bool:
        """Whether this tiler supports element filtering.

        Returns:
            True if the tiler produces a 'keep' column indicating which elements
            should be kept in each tile, False otherwise.
        """
        return False

    @abstractmethod
    def tile(self, df: pl.DataFrame, tiles_df: pl.DataFrame, slice_offset: int = 0) -> pl.DataFrame:
        """Apply tiling operation to a DataFrame.

        Args:
            df: Input DataFrame containing the data to tile
            tiles_df: DataFrame containing tile parameters
            slice_offset: Integer offset to subtract when accessing df based on
                        source_sample_idx. Used when df is a subset of another
                        DataFrame. Defaults to 0.

        Returns:
            DataFrame with tiled data. The output will have the same
            number of rows as tiles_df.
        """


class TilerRegistry:
    """Registry for tiler implementations.

    This class provides a central registry for all tiler implementations, mapping
    field types to their corresponding tilers. It uses a decorator pattern for
    registration, making it easy to add new tilers for different field types.

    The registry is used by the tiling system to automatically find and instantiate
    the appropriate tiler for each field in a dataset.

    Example:
        ```python
        @TilerRegistry.register(ImageField)
        class ImageTiler(Tiler):
            def tile(self, df, tiles_df):
                # Implementation for tiling image data
                ...

        # Later, get tiler for field type
        tiler_cls = TilerRegistry.get_tiler(ImageField)
        ```
    """

    _tilers: dict[type[Field], type[Tiler]] = {}

    @classmethod
    def register(cls, field_type: type[Field]):
        """Decorator to register a tiler for a specific field type.

        This decorator associates a Tiler implementation with a specific Field type.
        When the tiling system encounters a field of this type, it will use the
        registered tiler to process it.

        Args:
            field_type: The Field subclass this tiler handles

        Returns:
            Decorator function that registers the tiler class

        Example:
            ```python
            @TilerRegistry.register(ImageField)
            class ImageTiler(Tiler):
                ...
            ```
        """

        def wrapper(tiler_cls: type[Tiler]):
            cls._tilers[field_type] = tiler_cls
            return tiler_cls

        return wrapper

    @classmethod
    def get_tiler(cls, field_type: type[Field]) -> type[Tiler] | None:
        """Get the registered tiler for a field type.

        Args:
            field_type: The Field type to get a tiler for

        Returns:
            The registered Tiler class for the field type, or None if no
            tiler is registered
        """
        return cls._tilers.get(field_type)


class TilerEntry(NamedTuple):
    field_name: str
    tiler: Tiler


def create_tilers(schema: Schema, threshold_drop_ann: float) -> dict[str, list[TilerEntry]]:
    """Create tiler instances based on schema fields.

    This function instantiates appropriate tilers for each field in the schema,
    organizing them by their semantic type (e.g., annotations, metadata).
    Each tiler is configured with its field specification and annotation
    dropping threshold.

    Args:
        schema: Input schema defining the DataFrame structure. Each field
               in the schema may have a corresponding tiler.
        threshold_drop_ann: Threshold for dropping annotations. If an annotation's
                          area within a tile is below this ratio, it will be
                          dropped.

    Returns:
        Dictionary mapping semantic tags (strings) to lists of TilerEntry objects.
        Each TilerEntry contains:
        - field_name: Name of the field this tiler handles
        - tiler: The configured tiler instance
        This allows processing fields with similar semantics together.

    Example:
        ```python
        schema = Schema(...)
        tilers = create_tilers(schema, threshold_drop_ann=0.5)
        # Access annotation tilers
        for entry in tilers["annotation"]:
            print(f"Field: {entry.field_name}")
            print(f"Tiler: {entry.tiler.__class__.__name__}")
        ```
    """
    tilers = defaultdict(list)

    for field_name, field in schema.attributes.items():
        tiler_cls = TilerRegistry.get_tiler(type(field.field))
        if tiler_cls:
            # Create field spec and tiler instance
            field_spec = AttributeSpec(name=field_name, field=field.field)
            tiler = tiler_cls()
            setattr(tiler, "field_spec", field_spec)  # Set the field spec
            setattr(tiler, "threshold_drop_ann", threshold_drop_ann)  # Set the threshold
            tilers[field.field.semantic].append(TilerEntry(field_name, tiler))

    return tilers


def zip_list(op: Callable[[pl.Expr, pl.Expr], pl.Expr], *args: str) -> pl.Expr:
    """
    Apply an operation element-wise between a set of columns.

    Args:
        op: Operation function to apply element-wise
        args: List of columns to zip together

    Returns:
        Polars expression for the computed list column

    Note:
        See https://github.com/pola-rs/polars/issues/7210 for implementation details
    """
    return pl.concat_list(pl.struct(*args)).list.eval(op(*(pl.element().struct.field(arg).explode() for arg in args)))


@dataclass
class TilingPlan:
    """Stores the complete plan for executing tiling operations.

    This class organizes all the components needed for tiling a dataset:
    - Tiler grouping for coordinated filtering
    - Field specifications
    - Target schema
    - Tiling configuration

    The plan is created by _create_tiling_plan() and used by the tiling transform
    to execute the tiling operation.

    Attributes:
        tilers_filter_group_id: Maps field names to their filter group IDs.
            Fields in the same group are filtered together.
        tilers_by_group_id: Maps group IDs to lists of field names in that group.
            Used to coordinate filtering operations.
        tilers_instance_by_name: Maps field names to their tiler instances.
            Contains the actual objects that perform tiling.
        image_info_spec: Specification for the image info field, used to
            get image dimensions.
        tile_info_spec: Specification for the tile info field that will
            store tile parameters.
        target_schema: The schema for the output DataFrame after tiling.
            Includes all original fields plus tile information.
        config: The configuration controlling tile sizes and overlaps.
    """

    tilers_filter_group_id: dict[str, int]
    tilers_by_group_id: defaultdict[int, list[str]]
    tilers_instance_by_name: dict[str, Tiler]
    image_info_spec: AttributeSpec[ImageInfoField]
    tile_info_spec: AttributeSpec[TileField]
    target_schema: Schema
    config: TilingConfig


def _create_tiling_plan(schema: Schema, config: TilingConfig, threshold_drop_ann: float = 0.8):
    """Create a plan for tiling operations on a dataset.

    This function analyzes the schema, identifies relevant fields, and creates
    a structured plan for how to tile the dataset. It handles:
    1. Finding the image info field
    2. Creating tiler instances
    3. Grouping tilers for coordinated filtering
    4. Preparing the output schema

    Args:
        schema: The input dataset's schema, defining all fields.
        config: Configuration specifying tile sizes and overlaps.
        threshold_drop_ann: Threshold for dropping annotations. Annotations with
            area ratios below this threshold will be dropped from tiles.
            Defaults to 0.8 (80% of original area must be in tile).

    Returns:
        A TilingPlan containing all information needed for the tiling operation.

    Raises:
        ValueError: If the schema does not contain an ImageInfoField.

    Example:
        ```python
        schema = Schema(...)  # Your dataset schema
        config = TilingConfig(tile_width=512, tile_height=512)
        plan = _create_tiling_plan(schema, config)
        ```
    """
    # Find image info field in schema
    image_info_spec = None
    for field_name, field in schema.attributes.items():
        if isinstance(field.field, ImageInfoField):
            image_info_spec = AttributeSpec(name=field_name, field=field)
            break

    if image_info_spec is None:
        raise ValueError("Schema must contain an ImageInfoField")

    # Create tile info field spec
    tile_info_spec = AttributeSpec(name="tile", field=TileField(semantic="default"))

    # Create tilers for each field type
    tilers = create_tilers(schema, threshold_drop_ann)

    tilers_filter_group_id = {}
    tilers_by_group_id = defaultdict(list)
    tilers_instance_by_name = {}

    # Group filterable tilers
    for semantic_tilers in tilers.values():
        filterable_tilers = [tiler for tiler in semantic_tilers if tiler.tiler.is_filterable()]

        group_id = id(filterable_tilers)
        tilers_filter_group_id.update((tiler.field_name, group_id) for tiler in filterable_tilers)
        tilers_by_group_id[group_id] = [tiler.field_name for tiler in filterable_tilers]
        tilers_instance_by_name.update((tiler.field_name, tiler.tiler) for tiler in semantic_tilers)

    # Update schema with tile information
    new_fields = dict(schema.attributes)
    new_fields[tile_info_spec.name] = AttributeInfo(type=TileInfo, field=tile_info_spec.field)
    target_schema = Schema(new_fields)

    return TilingPlan(
        tilers_filter_group_id,
        tilers_by_group_id,
        tilers_instance_by_name,
        image_info_spec,
        tile_info_spec,
        target_schema,
        config,
    )


def _get_fields_set(fields: set[str], plan: TilingPlan) -> set[str]:
    """Get all fields including all the other fields in the same groups"""
    fields_set = set(fields)

    for field in fields:
        group_id = plan.tilers_filter_group_id.get(field, None)
        if group_id is not None:
            fields_set.update(plan.tilers_by_group_id[group_id])
    return fields_set


def _apply_tiling(
    input_df: pl.DataFrame,
    output_df: pl.DataFrame | None,
    plan: TilingPlan,
    fields: set[str],
    slice_offset: int = 0,
) -> tuple[pl.DataFrame, set[str]]:
    """Apply tiling operations to a DataFrame according to the tiling plan.

    This function executes the tiling plan on the input data, handling:
    1. Field group expansion (ensuring related fields are tiled and filtered together)
    2. Tile parameter calculation
    3. Individual field tiling
    4. Coordinated filtering of related fields
    5. Result combination

    Args:
        input_df: Source DataFrame containing the data to tile
        output_df: Optional pre-existing output DataFrame with tile parameters.
                  If None, tile parameters will be calculated.
        plan: The TilingPlan containing all tiling specifications
        fields: Set of field names to process in this operation
        slice_offset: Integer offset to subtract when accessing input_df based on
                     source_sample_idx. Used when input_df is a subset of another
                     DataFrame to identify the start of the subset. Defaults to 0.

    Returns:
        A tuple of:
        - The output DataFrame containing all tiled data
        - Set of field names that were actually processed (may include
          additional fields from the same groups)

    Example:
        ```python
        plan = _create_tiling_plan(schema, config)
        output_df, processed_fields = _apply_tiling(
            input_df,
            None,
            plan,
            {"image", "masks", "polygons"}
        )
        ```
    """
    fields_set = _get_fields_set(fields, plan)

    if output_df is None:
        output_df = _calculate_tiles(input_df, plan.config, plan.image_info_spec, plan.tile_info_spec, slice_offset)

    # Apply each tiler and collect keep flags and columns to filter
    tiled_data = []
    keep_mask_by_group_id = {}
    columns_to_filter_by_group_id = defaultdict(set)

    for field_name in fields_set:
        tiler = plan.tilers_instance_by_name[field_name]
        tiled_df = tiler.tile(input_df, output_df, slice_offset)

        # If tiler provides a keep column, update our mask and track columns
        if tiler.is_filterable():
            if "keep" not in tiled_df.columns:
                raise RuntimeError("Expected the 'keep' column to be present since the tiler is filterable.")

            group_id = plan.tilers_filter_group_id[field_name]

            # Initialize keep_mask if needed
            if group_id not in keep_mask_by_group_id:
                keep_mask_by_group_id[group_id] = tiled_df["keep"]
            else:
                # Update keep_mask at list element level
                keep_mask = keep_mask_by_group_id[group_id]
                keep_mask = tiled_df.with_columns(keep_mask=keep_mask).with_columns(
                    keep_mask=zip_list(lambda a, b: a & b, "keep", "keep_mask")
                )["keep_mask"]
                keep_mask_by_group_id[group_id] = keep_mask

            tiled_df = tiled_df.drop("keep")

            # Track which columns from this tiler need filtering
            columns_to_filter_by_group_id[group_id].update(tiled_df.columns)

        tiled_data.append(tiled_df)

    # Combine all tiled data with tile parameters
    for tiled_df in tiled_data:
        # Only keep columns that aren't in the result yet
        new_cols = [col for col in tiled_df.columns if col not in output_df.columns]
        if new_cols:
            output_df = output_df.with_columns([tiled_df.get_column(col).alias(col) for col in new_cols])

    # Apply list filtering if we have a keep mask
    for group_id, keep_mask in keep_mask_by_group_id.items():
        columns_to_filter = columns_to_filter_by_group_id[group_id]

        output_df = output_df.with_columns(keep=keep_mask).with_columns(
            zip_list(lambda a, b: pl.struct(a, b), col, "keep")
            .list.filter(pl.element().struct["keep"])
            .list.eval(pl.element().struct[col])
            .alias(col)
            for col in columns_to_filter
        )
        output_df = output_df.drop("keep")

    return output_df, fields_set


class TilingTransform(Transform):
    """Transform that implements tiling operations on a dataset.

    This transform divides dataset items into tiles according to a tiling plan.
    It handles:
    - Lazy evaluation of fields when possible
    - Batch-based tile parameter calculation
    - Proper slicing of tiled datasets
    - Coordinated filtering of related fields

    The transform maintains state about which fields have been processed and
    caches intermediate results to avoid redundant computation.

    Example:
        ```python
        # Create configuration and transform
        config = TilingConfig(tile_width=512, tile_height=512)
        transform = create_tiling_transform(config)

        # Apply to dataset
        tiled_dataset = dataset.transform(transform)
        ```
    """

    def __init__(self, parent: Transform, tiling_plan: TilingPlan):
        """Initialize tiling transform.

        Args:
            parent: The parent transform providing input data
            tiling_plan: The plan specifying how to tile the data
        """
        super().__init__(tiling_plan.target_schema)

        # Tiling does not support a lazy image info field
        # so remove it from the list of lazy outputs.
        lazy_outputs = parent.get_lazy_attributes()
        lazy_outputs.discard(tiling_plan.image_info_spec.name)

        self._lazy_outputs = lazy_outputs

        # Add image info to the list of batch outputs to compute immediately.
        # It is needed inside apply() to calculate the list of tiles.
        batch_outputs = self.get_batch_attributes()
        batch_outputs.add(tiling_plan.image_info_spec.name)

        self._parent = parent
        self._tiling_plan = tiling_plan
        self._df = None
        self._slice_offset = 0

        # Calculate tile parameters
        self._applied_tilers = set()

        self.apply(batch_outputs)

    def apply(self, fields: Sequence[str]) -> pl.DataFrame:
        fields_set = set(fields)

        # Do not request the tile_info from the parent transform as it is generated by this transform.
        fields_set.discard(self._tiling_plan.tile_info_spec.name)
        fields_set -= self._applied_tilers

        # Request all required attributes from the parent transform
        input_df = self._parent.apply(list(fields_set))

        # Apply tiling
        self._df, fields_set = _apply_tiling(input_df, self._df, self._tiling_plan, fields_set, self._slice_offset)

        # Update the list of applied attributes to avoid recomputing them.
        self._applied_tilers.update(fields_set)
        return self._df

    def get_lazy_attributes(self) -> set[str]:
        return self._lazy_outputs

    def slice(self, offset: int, length: int | None = None) -> "Transform":
        instance = copy.copy(self)

        if self._df is None:
            raise RuntimeError("apply() should have been called in the constructor.")

        # Find the start and end of this slice in the source dataset
        source_sample_offset = self._df[offset, self._tiling_plan.tile_info_spec.name]["source_sample_idx"]

        if length is None:
            source_sample_length = None
        else:
            source_sample_last = self._df[offset + length - 1, self._tiling_plan.tile_info_spec.name][
                "source_sample_idx"
            ]
            source_sample_length = source_sample_last - source_sample_offset + 1

        # Slice the parent transform based on the source offset and length
        instance._parent = self._parent.slice(source_sample_offset, source_sample_length)

        # Slice the output dataframe
        instance._applied_tilers = copy.copy(self._applied_tilers)
        instance._df = self._df.slice(offset, length)
        instance._slice_offset += source_sample_offset
        return instance

    def __len__(self):
        return len(self._df)


class _TilingTransformFactory:
    """Module-level callable that builds a :class:`TilingTransform` from a parent transform.

    Defined at module scope (instead of a local ``factory`` closure) so instances
    pickle by reference. This allows the returned transform to be safely passed
    across process boundaries (e.g. multiprocessing).
    """

    __slots__ = ("config", "threshold_drop_ann")

    def __init__(self, config: TilingConfig, threshold_drop_ann: float = 0.8):
        self.config = config
        self.threshold_drop_ann = threshold_drop_ann

    def __call__(self, parent: Transform) -> TilingTransform:
        plan = _create_tiling_plan(parent.schema, self.config, self.threshold_drop_ann)
        return TilingTransform(parent, plan)


def create_tiling_transform(
    config: TilingConfig, threshold_drop_ann: float = 0.8
) -> Callable[[Transform], TilingTransform]:
    """Create a transform factory for tiling operations.

    This is the main entry point for creating a tiling transform. It returns
    a picklable callable that will create TilingTransform instances when needed.
    This pattern allows the transform to be used in dataset pipelines.

    Args:
        config: The configuration specifying tile sizes and overlaps
        threshold_drop_ann: Threshold for dropping annotations. Annotations with
            area ratios below this threshold will be dropped from tiles.
            Defaults to 0.8 (80% of original area must be in tile).

    Returns:
        A picklable callable that creates TilingTransform instances.

    Example:
        ```python
        # Create the transform factory
        config = TilingConfig(tile_width=512, tile_height=512)
        tiling_transform = create_tiling_transform(config)

        # Use in a dataset pipeline
        dataset = dataset.transform(tiling_transform)
        ```
    """
    return _TilingTransformFactory(config, threshold_drop_ann)

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from typing import Any

import cv2
import numpy as np
import polars as pl

from getidata.categories import Colormap, LabelCategories, MaskCategories, RgbColor, generate_colormap
from getidata.converters.base import Converter, copy_columns_with_shape
from getidata.converters.registry import converter
from getidata.fields.annotations import LabelField, PolygonField
from getidata.fields.images import ImageInfoField
from getidata.fields.masks import InstanceMaskCallableField, InstanceMaskField, MaskCallableField, MaskField
from getidata.schema import AttributeSpec
from getidata.type_registry import polars_to_numpy_dtype

# A single polygon's coordinates: anything convertible by ``np.asarray`` into an
# ``(N, 2)`` array of ``(x, y)`` points (e.g. ``numpy.ndarray``, ``polars.Series``,
# or a nested ``list``/``tuple`` of points).
PolygonCoords = Any


def polygons_to_mask(
    polygons_data: Sequence[PolygonCoords],
    labels_data: Sequence[int],
    img_size: tuple[int, int],
    *,
    dtype: np.dtype = np.uint8,
    normalize: bool = False,
    background_index: int = 0,
    mask_size: tuple[int, int] | None = None,
) -> tuple[np.ndarray, list[int]]:
    """Rasterize polygons into a single indexed (semantic) mask using OpenCV contour filling.

    The mask uses:

    - ``background_index`` (default ``0``): Background (empty areas)
    - Index 1+: Polygon class labels (shifted by 1 to reserve 0 for background)

    Args:
        polygons_data: Sequence of polygon coordinates. Each element is
            converted with ``np.asarray`` into an ``(N, 2)`` array of
            ``(x, y)`` points, so ``numpy.ndarray``, ``polars.Series``, or
            nested ``list``/``tuple`` are all accepted.
        labels_data: Class label index for each polygon.
        img_size: Image size as a ``(width, height)`` tuple.
        dtype: Output numpy dtype for the mask.
        normalize: If True, polygon coordinates are treated as normalized
            (in ``[0, 1]``) and are scaled by the image dimensions.
        background_index: Fill value used for background pixels.
        mask_size: Optional output mask size as a ``(width, height)`` tuple.
            Defaults to ``img_size``. When it differs from the image size,
            polygon coordinates are scaled to fit the mask.

    Returns:
        A tuple ``(flattened_mask, shape)`` where ``flattened_mask`` is the
        flattened ``(H * W,)`` mask array and ``shape`` is ``[height, width]``.
    """
    # Extract image dimensions
    image_width, image_height = img_size

    # Resolve target mask dimensions (default to the image dimensions)
    out_width, out_height = mask_size if mask_size is not None else img_size

    # Scale factors to map image-space coordinates into mask-space
    scale_x = out_width / image_width
    scale_y = out_height / image_height
    needs_scaling = scale_x != 1.0 or scale_y != 1.0

    # Initialize mask with background index
    mask = np.full(
        shape=(out_height, out_width),
        fill_value=background_index,
        dtype=dtype,
    )

    # Rasterize each polygon
    for i, polygon_data in enumerate(polygons_data):
        coords = polygon_data.to_numpy() if hasattr(polygon_data, "to_numpy") else np.asarray(polygon_data)
        class_index = labels_data[i]

        # Denormalize coordinates if needed
        if normalize:
            coords = coords.astype(np.float64, copy=True)
            coords[:, 0] *= image_width
            coords[:, 1] *= image_height

        # Scale coordinates to mask dimensions if they differ from the image
        if needs_scaling:
            coords = coords.astype(np.float64, copy=True)
            coords[:, 0] *= scale_x
            coords[:, 1] *= scale_y

        # Convert to OpenCV contour format
        contour = coords.astype(np.int32)

        # Fill polygon with class index + 1 (to reserve 0 for background)
        cv2.fillPoly(mask, [contour], int(class_index) + 1)

    return mask.reshape(-1), [out_height, out_width]


def polygons_to_instance_masks(
    polygons_data: Sequence[PolygonCoords],
    img_size: tuple[int, int],
    *,
    dtype: np.dtype = np.uint8,
    normalize: bool = False,
    mask_size: tuple[int, int] | None = None,
) -> tuple[np.ndarray, list[int]]:
    """Rasterize polygons into binary instance masks using OpenCV contour filling.

    Produces a stack of binary masks of shape ``(N, H, W)`` where ``N`` is the
    number of polygons. Each mask represents a single instance without category
    information.

    Args:
        polygons_data: Sequence of polygon coordinates. Each element is
            converted with ``np.asarray`` into an ``(N, 2)`` array of
            ``(x, y)`` points, so ``numpy.ndarray``, ``polars.Series``, or
            nested ``list``/``tuple`` are all accepted.
        img_size: Image size as a ``(width, height)`` tuple.
        dtype: Output numpy dtype for the masks.
        normalize: If True, polygon coordinates are treated as normalized
            (in ``[0, 1]``) and are scaled by the image dimensions.
        mask_size: Optional output mask size as a ``(width, height)`` tuple.
            Defaults to ``img_size``. When it differs from the image size,
            polygon coordinates are scaled to fit the mask.

    Returns:
        A tuple ``(flattened_masks, shape)`` where ``flattened_masks`` is the
        flattened ``(N * H * W,)`` mask array and ``shape`` is
        ``[num_instances, height, width]``.
    """
    image_width, image_height = img_size
    n = len(polygons_data)

    # Resolve target mask dimensions (default to the image dimensions)
    out_width, out_height = mask_size if mask_size is not None else img_size

    # Scale factors to map image-space coordinates into mask-space
    scale_x = out_width / image_width
    scale_y = out_height / image_height
    needs_scaling = scale_x != 1.0 or scale_y != 1.0

    if n == 0:
        empty_mask = np.array([], dtype=dtype)
        return empty_mask, [0, out_height, out_width]

    # Pre-allocate the full (N, H, W) output in one shot as uint8 (required by OpenCV)
    stacked_masks = np.zeros((n, out_height, out_width), dtype=np.uint8)

    for i, polygon_data in enumerate(polygons_data):
        coords = polygon_data.to_numpy() if hasattr(polygon_data, "to_numpy") else np.asarray(polygon_data)

        if normalize:
            coords = coords.astype(np.float64, copy=True)
            coords[:, 0] *= image_width
            coords[:, 1] *= image_height

        # Scale coordinates to mask dimensions if they differ from the image
        if needs_scaling:
            coords = coords.astype(np.float64, copy=True)
            coords[:, 0] *= scale_x
            coords[:, 1] *= scale_y

        contour = coords.astype(np.int32)
        # fillPoly is faster than drawContours for single-polygon fills
        cv2.fillPoly(stacked_masks[i], [contour], 1)

    if dtype != np.uint8:
        stacked_masks = stacked_masks.astype(dtype)

    return stacked_masks.reshape(-1), list(stacked_masks.shape)


@converter(lazy=True)
class PolygonToMaskConverter(Converter):
    """
    Converts polygon annotations to rasterized masks.

    Transforms polygon coordinates into binary or indexed masks using
    OpenCV contour filling for efficient rasterization.
    """

    input_polygon: AttributeSpec[PolygonField]
    input_labels: AttributeSpec[LabelField]
    input_image_info: AttributeSpec[ImageInfoField]
    output_mask: AttributeSpec[MaskField]

    # Configuration options
    background_index: int = 0  # Background value

    def filter_output_spec(self) -> bool:
        """
        Configure mask output specification.

        Returns:
            True if the converter should be applied, False otherwise
        """

        # Copy label categories and create mask categories
        mask_categories = None
        if self.input_labels.categories is not None and isinstance(self.input_labels.categories, LabelCategories):
            # Create mask categories based on label categories
            # Create a colormap for mask categories
            # Generate colors for all labels plus background
            num_classes = len(self.input_labels.categories) + 1  # +1 for background
            colormap_dict = generate_colormap(num_classes, include_background=True)
            colormap_struct_dict = {i: RgbColor(*color) for i, color in colormap_dict.items()}

            # Create mask categories with the generated colormap
            labels = ("background", *self.input_labels.categories.labels)
            mask_categories = MaskCategories(colormap=Colormap(data=colormap_struct_dict), labels=labels)

        # Configure output for mask format
        self.output_mask = AttributeSpec(
            name=self.output_mask.name,
            field=MaskField(
                semantic=self.input_polygon.field.semantic,
                dtype=self.output_mask.field.dtype,
                channels_first=self.output_mask.field.channels_first,
                has_channels_dim=self.output_mask.field.has_channels_dim,
            ),
            categories=mask_categories,
        )

        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Rasterize polygon coordinates into indexed masks.

        Args:
            df: DataFrame with polygon coordinates, labels, and image info

        Returns:
            DataFrame with mask data in output column
        """
        input_column_name = self.input_polygon.name
        labels_column_name = self.input_labels.name
        image_info_column_name = self.input_image_info.name
        output_column_name = self.output_mask.name
        output_shape_column_name = self.output_mask.name + "_shape"

        # Pre-compute dtype and normalize flag once
        _numpy_dtype = polars_to_numpy_dtype(self.output_mask.field.dtype)
        _normalize = self.input_polygon.field.normalize
        _background_index = self.background_index

        # Apply conversion using map_batches
        def apply_conversion_batch(batch_df: pl.DataFrame) -> pl.DataFrame:
            """Apply polygon-to-mask conversion for a batch."""
            batch_polygons = batch_df.struct["polygons"]
            batch_labels = batch_df.struct["labels"]
            batch_img_infos = batch_df.struct["img_info"]

            results_batch_polygons = []
            results_batch_shape = []
            for polygons, labels, img_infos in zip(batch_polygons, batch_labels, batch_img_infos):
                mask_data, shape_data = polygons_to_mask(
                    polygons,
                    labels,
                    (img_infos["width"], img_infos["height"]),
                    dtype=_numpy_dtype,
                    normalize=_normalize,
                    background_index=_background_index,
                )
                results_batch_polygons.append(pl.Series(mask_data))
                results_batch_shape.append(shape_data)

            return pl.struct(
                pl.Series(results_batch_polygons).alias("mask"),
                pl.Series("shape", results_batch_shape, dtype=pl.List(pl.Int32())),
                eager=True,
            )

        mask_data = pl.struct(
            [
                pl.col(input_column_name).alias("polygons"),
                pl.col(labels_column_name).alias("labels"),
                pl.col(image_info_column_name).alias("img_info"),
            ]
        ).map_batches(
            apply_conversion_batch,
            return_dtype=pl.Struct({"mask": pl.List(self.output_mask.field.dtype), "shape": pl.List(pl.Int32())}),
        )

        return df.with_columns(
            [
                mask_data.struct.field("mask").alias(output_column_name),
                mask_data.struct.field("shape").alias(output_shape_column_name),
            ]
        )


@converter(lazy=True)
class PolygonToInstanceMaskConverter(Converter):
    """
    Converts polygon annotations to instance masks.

    Transforms polygon coordinates into binary instance masks of shape (N, H, W)
    where N is the number of instances. Each mask represents a single instance
    without category information.
    """

    input_polygon: AttributeSpec[PolygonField]
    input_image_info: AttributeSpec[ImageInfoField]
    output_instance_mask: AttributeSpec[InstanceMaskField]

    def filter_output_spec(self) -> bool:
        """Configure output specification for instance mask format."""
        # Configure output for instance mask format
        self.output_instance_mask = AttributeSpec(
            name=self.output_instance_mask.name,
            field=InstanceMaskField(
                semantic=self.input_polygon.field.semantic,
                dtype=self.output_instance_mask.field.dtype,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Rasterize polygon coordinates into instance masks.

        Args:
            df: DataFrame with polygon coordinates and image info

        Returns:
            DataFrame with instance mask data in output column
        """
        input_column_name = self.input_polygon.name
        image_info_column_name = self.input_image_info.name
        output_column_name = self.output_instance_mask.name
        output_shape_column_name = self.output_instance_mask.name + "_shape"

        # Pre-compute dtype and normalize flag once
        _numpy_dtype = polars_to_numpy_dtype(self.output_instance_mask.field.dtype)
        _numpy_dtype = polars_to_numpy_dtype(self.output_instance_mask.field.dtype)
        _normalize = self.input_polygon.field.normalize
        # Always use uint8 for internal Polars storage (List(Boolean) construction is extremely slow)
        _use_uint8_storage = self.output_instance_mask.field.dtype.is_(pl.Boolean)
        _storage_pl_dtype = pl.UInt8() if _use_uint8_storage else self.output_instance_mask.field.dtype
        # For Boolean output, rasterize as uint8 for fast Polars List(UInt8) storage;
        # the cast to Boolean happens after collection.
        _storage_numpy_dtype = np.uint8 if _use_uint8_storage else _numpy_dtype

        # Apply conversion using map_batches
        def apply_conversion_batch(batch_df: pl.DataFrame, **kwargs) -> pl.DataFrame:  # noqa: ARG001
            """Apply polygon-to-instance-mask conversion for a batch."""
            batch_polygons = batch_df.struct["polygons"]
            batch_img_infos = batch_df.struct["img_info"]

            results_batch_mask = []
            results_batch_shape = []

            for polygons, img_info in zip(batch_polygons, batch_img_infos):
                mask_data, shape_data = polygons_to_instance_masks(
                    polygons,
                    (img_info["width"], img_info["height"]),
                    dtype=_storage_numpy_dtype,
                    normalize=_normalize,
                )
                results_batch_mask.append(pl.Series(mask_data))
                results_batch_shape.append(shape_data)

            return pl.struct(
                pl.Series(results_batch_mask).alias("mask"),
                pl.Series(results_batch_shape, dtype=pl.List(pl.Int32())).alias("shape"),
                eager=True,
            )

        mask_data = pl.struct(
            [
                pl.col(input_column_name).alias("polygons"),
                pl.col(image_info_column_name).alias("img_info"),
            ]
        ).map_batches(
            apply_conversion_batch,
            return_dtype=pl.Struct({"mask": pl.List(_storage_pl_dtype), "shape": pl.List(pl.Int32())}),
        )

        mask_col = mask_data.struct.field("mask")
        # Cast from uint8 storage back to target dtype if needed
        if _use_uint8_storage:
            mask_col = mask_col.cast(pl.List(self.output_instance_mask.field.dtype))

        return df.with_columns(
            [
                mask_col.alias(output_column_name),
                mask_data.struct.field("shape").alias(output_shape_column_name),
            ]
        )


@converter(lazy=True)
class InstanceMaskCallableToInstanceMaskConverter(Converter):
    """
    Lazy converter that executes callables to generate instance mask data.

    This converter takes a callable stored in a InstanceMaskCallableField and
    executes it to get instance mask data as a 3D numpy array (N,H,W), producing
    an InstanceMaskField output. Each mask in the output is a binary mask
    representing a single instance.
    """

    input_callable: AttributeSpec[InstanceMaskCallableField]
    output_mask: AttributeSpec[InstanceMaskField]

    def filter_output_spec(self) -> bool:
        """Configure output mask specification based on input."""
        self.output_mask = AttributeSpec(
            name=self.output_mask.name,
            field=InstanceMaskField(
                semantic=self.input_callable.field.semantic,
                dtype=self.input_callable.field.dtype,  # Use dtype from callable field
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Execute callables to generate instance mask data.

        Args:
            df: DataFrame containing callable column

        Returns:
            DataFrame with instance mask tensor data and shape information
        """
        input_col = self.input_callable.name
        output_col = self.output_mask.name

        # Execute callables to generate mask data
        mask_data: list[Any] = []
        mask_shapes: list[list[int]] = []

        for callable_obj in df[input_col]:
            # Execute the callable to get instance mask array
            mask_array = callable_obj()

            if mask_array is None:
                mask_data.append(None)
                mask_shapes.append(None)
                continue

            # Validate that we got a numpy array
            if not isinstance(mask_array, np.ndarray):
                raise TypeError(f"Callable must return numpy.ndarray, got {type(mask_array)}")

            # Check array shape - should be 3D for instance masks (N, height, width)
            if len(mask_array.shape) != 3:
                raise ValueError(f"Instance mask array must be 3D (N,H,W), got shape {mask_array.shape}")

            # Check that the array has the expected dtype
            expected_dtype = self.output_mask.field.dtype
            expected_numpy_dtype = polars_to_numpy_dtype(expected_dtype)
            if mask_array.dtype != expected_numpy_dtype:
                raise TypeError(f"Expected {expected_numpy_dtype} mask array, got {mask_array.dtype}")

            # Store flattened mask data and shape
            mask_data.append(mask_array.flatten())
            mask_shapes.append(list(mask_array.shape))

        # Create output columns
        return df.with_columns(
            [
                pl.Series(output_col, mask_data),
                pl.Series(f"{output_col}_shape", mask_shapes),
            ]
        ).drop(input_col)


@converter(lazy=True)
class MaskCallableToMaskConverter(Converter):
    """
    Lazy converter that executes callables to generate mask data.

    This converter takes a callable stored in a MaskCallableField and
    executes it to get mask data as a 2D numpy array (H,W), producing
    a MaskField output. The mask can be either a binary mask or a
    category mask.
    """

    input_callable: AttributeSpec[MaskCallableField]
    output_mask: AttributeSpec[MaskField]

    def filter_output_spec(self) -> bool:
        """Configure output mask specification based on input."""
        self.output_mask = AttributeSpec(
            name=self.output_mask.name,
            field=MaskField(
                semantic=self.input_callable.field.semantic,
                dtype=self.input_callable.field.dtype,  # Use dtype from callable field
                channels_first=self.output_mask.field.channels_first,
                has_channels_dim=self.output_mask.field.has_channels_dim,
            ),
            categories=self.input_callable.categories,
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Execute callables to generate mask data.

        Args:
            df: DataFrame containing callable column

        Returns:
            DataFrame with mask tensor data and shape information
        """
        input_col = self.input_callable.name
        output_col = self.output_mask.name

        # Execute callables to generate mask data
        mask_data: list[Any] = []
        mask_shapes: list[list[int]] = []

        for callable_obj in df[input_col]:
            # Execute the callable to get mask array
            mask_array = callable_obj()

            if mask_array is None:
                mask_data.append(None)
                mask_shapes.append(None)
                continue

            # Validate that we got a numpy array
            if not isinstance(mask_array, np.ndarray):
                raise TypeError(f"Callable must return numpy.ndarray, got {type(mask_array)}")

            # Check array shape - should be 2D for masks (height, width)
            if len(mask_array.shape) != 2:
                raise ValueError(f"Mask array must be 2D (H,W), got shape {mask_array.shape}")

            # Check that the array has the expected dtype
            expected_dtype = self.output_mask.field.dtype
            expected_numpy_dtype = polars_to_numpy_dtype(expected_dtype)
            if mask_array.dtype != expected_numpy_dtype:
                raise TypeError(f"Expected {expected_numpy_dtype} mask array, got {mask_array.dtype}")

            # Store flattened mask data and shape
            mask_data.append(mask_array.flatten())
            mask_shapes.append(list(mask_array.shape))

        # Create output columns
        return df.with_columns(
            [
                pl.Series(output_col, mask_data),
                pl.Series(f"{output_col}_shape", mask_shapes),
            ]
        ).drop(input_col)


@converter
class MaskChannelsFirstConverter(Converter):
    """
    Converter that updates the channels_first metadata for mask fields.

    This converter handles the transition between channels-first and
    channels-last format specifications for masks. The actual data transposition
    is handled by the MaskField.from_polars() method when data is accessed,
    so this converter only needs to update the field metadata.
    """

    input_mask: AttributeSpec[MaskField]
    output_mask: AttributeSpec[MaskField]

    def filter_output_spec(self) -> bool:
        """
        Check if channels_first conversion is needed and configure output.

        Returns:
            True if the converter should be applied (channels_first differs), False otherwise
        """
        input_channels_first = self.input_mask.field.channels_first
        output_channels_first = self.output_mask.field.channels_first

        self.output_mask = AttributeSpec(
            name=self.output_mask.name,
            field=MaskField(
                semantic=self.input_mask.field.semantic,
                dtype=self.input_mask.field.dtype,
                channels_first=output_channels_first,
                has_channels_dim=self.input_mask.field.has_channels_dim,
            ),
            categories=self.input_mask.categories,
        )

        # Apply converter only if channels_first status differs
        return input_channels_first != output_channels_first

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Update mask field metadata for channels_first change.

        The actual transposition is handled by MaskField.from_polars(),
        so this just ensures the column names are properly mapped.
        """

        return copy_columns_with_shape(df, self.input_mask.name, self.output_mask.name)

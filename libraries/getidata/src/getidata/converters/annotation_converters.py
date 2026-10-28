# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging

import polars as pl

from getidata.categories import LabelCategories
from getidata.converters.base import Converter, list_eval_ref
from getidata.converters.registry import converter
from getidata.fields.annotations import (
    BBoxField,
    EllipseField,
    KeypointsField,
    LabelField,
    PolygonField,
    RotatedBBoxField,
)
from getidata.fields.images import ImageField
from getidata.schema import AttributeSpec

log = logging.getLogger(__name__)


@converter
class LabelIndexConverter(Converter):
    """
    Converter for updating label indices when label categories change.

    This converter handles remapping label values in LabelField when the order
    of labels has changed between input and output categories. It only applies
    when both input and output categories are LabelCategories and have different
    label orders but the same set of labels.
    """

    input_labels: AttributeSpec[LabelField]
    output_labels: AttributeSpec[LabelField]

    def filter_output_spec(self) -> bool:
        """
        Check if this converter is applicable based on input/output categories.

        Returns True only if:
        1. Both input and output have LabelCategories
        2. The categories have the same set of labels but different order
        3. The field types are the same (no field conversion needed)
        """
        # Check that both specs have categories
        if self.input_labels.categories is None or self.output_labels.categories is None:
            return False

        # Check that both are LabelCategories
        if not isinstance(self.input_labels.categories, LabelCategories) or not isinstance(
            self.output_labels.categories, LabelCategories
        ):
            return False

        input_cats = self.input_labels.categories
        output_cats = self.output_labels.categories

        # Check that the sets of labels are the same but order might differ
        input_labels_set = set(input_cats.labels)
        output_labels_set = set(output_cats.labels)

        if input_labels_set != output_labels_set:
            return False

        # Only apply if the order actually differs
        if input_cats.labels == output_cats.labels:
            return False

        index_mapping = {}
        for old_idx, label in enumerate(input_cats.labels):
            semantic = None
            for sem, lbl in input_cats.label_semantics.items():
                if lbl == label:
                    semantic = sem
                    break
            if semantic is not None:
                new_label = output_cats.label_semantics[semantic]
                new_idx, _ = output_cats.find(new_label)
            else:
                new_idx, _ = output_cats.find(label)
            if new_idx is not None:
                index_mapping[old_idx] = new_idx
        self._index_mapping = index_mapping
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert label indices based on category mapping.

        If label semantics are defined, use them to match input and output labels for mapping.
        Otherwise, fall back to label name.
        """
        # Use the precomputed index mapping from filter_output_spec
        index_mapping = getattr(self, "_index_mapping", None)
        if index_mapping is None:
            raise RuntimeError("index_mapping not computed. Call filter_output_spec first.")

        input_col = self.input_labels.name
        output_col = self.output_labels.name
        field = self.input_labels.field

        if field.multi_label or field.is_list:
            mapping_expr = pl.col(input_col).list.eval(
                pl.element().replace_strict(list(index_mapping.keys()), list(index_mapping.values()), default=None)
            )
        else:
            mapping_expr = pl.col(input_col).replace_strict(
                list(index_mapping.keys()), list(index_mapping.values()), default=None
            )

        return df.with_columns(mapping_expr.alias(output_col))


@converter
class BBoxCoordinateConverter(Converter):
    """
    Convert bounding box coordinates between normalized and absolute formats.

    This converter handles transformations between normalized coordinates
    (range [0,1]) and absolute pixel coordinates using image dimensions.
    """

    input_bbox: AttributeSpec[BBoxField]
    input_image: AttributeSpec[ImageField]
    output_bbox: AttributeSpec[BBoxField]

    def filter_output_spec(self) -> bool:
        """
        Check if bbox normalization conversion is needed and configure output.

        Returns:
            True if conversion is needed (normalization status differs), False otherwise
        """
        input_normalized = self.input_bbox.field.normalize
        output_normalized = self.output_bbox.field.normalize

        # Determine the target normalization from output specification
        target_normalized = output_normalized

        # Configure output specification with correct normalization
        self.output_bbox = AttributeSpec(
            name=self.output_bbox.name,
            field=BBoxField(
                semantic=self.input_bbox.field.semantic,
                dtype=self.input_bbox.field.dtype,
                format=self.input_bbox.field.format,
                normalize=target_normalized,
            ),
        )

        # Apply converter only if normalization status needs to change
        return input_normalized != target_normalized

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert bbox coordinates between normalized and absolute formats.

        Uses image dimensions to transform coordinates. For normalized to absolute:
        multiplies by image dimensions. For absolute to normalized: divides by
        image dimensions.

        Args:
            df: Input DataFrame containing bbox and image data

        Returns:
            DataFrame with converted bounding box coordinates
        """
        input_bbox_name = self.input_bbox.name
        input_image_name = self.input_image.name
        output_bbox_name = self.output_bbox.name

        # Get the image shape column name
        image_shape_name = f"{input_image_name}_shape"

        input_normalized = self.input_bbox.field.normalize

        # Create temporary column names for dimensions
        temp_width_col = f"{input_image_name}_width"
        temp_height_col = f"{input_image_name}_height"

        # Coordinate order for width/height mapping: [height, width, height, width]
        coordinates_order = [1, 0, 1, 0]

        def op(x: pl.Expr, y: pl.Expr) -> pl.Expr:
            """Choose operation based on conversion direction."""
            xy = x * y if input_normalized else x / y
            return xy.cast(self.output_bbox.field.dtype)

        # Extract width and height from image shape
        df_with_temp = df.with_columns(
            [
                pl.col(image_shape_name).list.get(1).alias(temp_width_col),  # width
                pl.col(image_shape_name).list.get(0).alias(temp_height_col),  # height
            ]
        )

        # Apply coordinate transformation
        result_df = df_with_temp.with_columns(
            list_eval_ref(
                input_bbox_name,
                image_shape_name,
                lambda element, ref: pl.concat_arr(
                    op(element.arr.get(0), ref.list.get(coordinates_order[0])),  # x1
                    op(element.arr.get(1), ref.list.get(coordinates_order[1])),  # y1
                    op(element.arr.get(2), ref.list.get(coordinates_order[2])),  # x2
                    op(element.arr.get(3), ref.list.get(coordinates_order[3])),  # y2
                ),
            ).alias(output_bbox_name)
        )

        # Clean up temporary columns
        return result_df.drop([temp_width_col, temp_height_col])


def _create_fixed_array_cast_expr(target_dtype: pl.DataType, array_size: int) -> pl.Expr:
    """
    Create a Polars expression to cast a fixed-size array to a target dtype.

    Args:
        target_dtype: The target Polars data type
        array_size: The size of the fixed array (e.g., 4 for BBox, 5 for RotatedBBox)

    Returns:
        Polars expression that casts each element and reconstructs the array
    """
    return pl.concat_arr(*[pl.element().arr.get(i).cast(target_dtype) for i in range(array_size)])


def _convert_fixed_array_dtype(
    df: pl.DataFrame, input_col: str, output_col: str, target_dtype: pl.DataType, array_size: int
) -> pl.DataFrame:
    """
    Convert a column containing List[Array[dtype, N]] to a new dtype.

    Args:
        df: Input DataFrame
        input_col: Name of the input column
        output_col: Name of the output column
        target_dtype: Target Polars dtype
        array_size: Size of the fixed arrays

    Returns:
        DataFrame with converted column
    """
    return df.with_columns(
        pl.col(input_col).list.eval(_create_fixed_array_cast_expr(target_dtype, array_size)).alias(output_col)
    )


@converter
class BBoxDtypeConverter(Converter):
    """Convert BBox field between different data types."""

    input_bbox: AttributeSpec[BBoxField]
    output_bbox: AttributeSpec[BBoxField]

    def filter_output_spec(self) -> bool:
        """Configure output bbox specification with target dtype."""
        self.output_bbox = AttributeSpec(
            name=self.output_bbox.name,
            field=BBoxField(
                semantic=self.input_bbox.field.semantic,
                dtype=self.output_bbox.field.dtype,
                format=self.input_bbox.field.format,
                normalize=self.input_bbox.field.normalize,
            ),
        )
        return self.input_bbox.field.dtype != self.output_bbox.field.dtype

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """Convert bbox data to target dtype."""
        return _convert_fixed_array_dtype(
            df, self.input_bbox.name, self.output_bbox.name, self.output_bbox.field.dtype, array_size=4
        )


@converter
class RotatedBBoxDtypeConverter(Converter):
    """Convert RotatedBBox field between different data types."""

    input_rotated_bbox: AttributeSpec[RotatedBBoxField]
    output_rotated_bbox: AttributeSpec[RotatedBBoxField]

    def filter_output_spec(self) -> bool:
        """Configure output rotated bbox specification with target dtype."""
        self.output_rotated_bbox = AttributeSpec(
            name=self.output_rotated_bbox.name,
            field=RotatedBBoxField(
                semantic=self.input_rotated_bbox.field.semantic,
                dtype=self.output_rotated_bbox.field.dtype,
                format=self.input_rotated_bbox.field.format,
                normalize=self.input_rotated_bbox.field.normalize,
            ),
        )
        return self.input_rotated_bbox.field.dtype != self.output_rotated_bbox.field.dtype

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """Convert rotated bbox data to target dtype."""
        return _convert_fixed_array_dtype(
            df,
            self.input_rotated_bbox.name,
            self.output_rotated_bbox.name,
            self.output_rotated_bbox.field.dtype,
            array_size=5,
        )


@converter
class LabelShapeConverter(Converter):
    """Convert Label field between different multi_label and is_list configurations.

    This converter handles changes to both the ``multi_label`` and ``is_list``
    flags of a :class:`LabelField` in a single step.  It is activated whenever
    at least one of the two flags differs between input and output.

    The Polars column type is built as::

        base = dtype
        if multi_label: base = List(base)   # inner dimension
        if is_list:     base = List(base)   # outer dimension

    Supported conversions (non-exhaustive examples):

    multi_label changes (is_list unchanged):
      - ``dtype → List(dtype)``: wrap scalar in a list
      - ``List(dtype) → List(List(dtype))``: wrap each element (is_list=True)

    is_list changes (multi_label unchanged):
      - ``dtype → List(dtype)``: wrap scalar in a list
      - ``List(dtype) → List(List(dtype))``: wrap whole list (multi_label=True)

    Both change simultaneously:
      - ``dtype → List(List(dtype))``: wrap scalar twice

    Flag swap:
      - ``is_list=True, multi_label=False``-> ``is_list=False, multi_label=True``:
        both map to ``List(dtype)``; removes duplicate labels
      - ``is_list=False, multi_label=True``-> ``is_list=True, multi_label=False``:
        both map to ``List(dtype)``; the conversion is a no-op on the data.

    Lossy conversions (keep last element, logs a warning):
      - ``List(dtype) → dtype`` (multi_label or is_list reduction): keeps the last element only
    """

    input_label: AttributeSpec[LabelField]
    output_label: AttributeSpec[LabelField]

    def filter_output_spec(self) -> bool:
        """Configure output label specification with target multi_label and is_list settings."""
        self.output_label = AttributeSpec(
            name=self.output_label.name,
            field=LabelField(
                semantic=self.input_label.field.semantic,
                dtype=self.input_label.field.dtype,
                multi_label=self.output_label.field.multi_label,
                is_list=self.output_label.field.is_list,
            ),
        )
        input_field = self.input_label.field
        output_field = self.output_label.field

        return input_field.multi_label != output_field.multi_label or input_field.is_list != output_field.is_list

    def _convert_multi_label(
        self, df: pl.DataFrame, input_col: str, output_col: str, input_is_list: bool
    ) -> pl.DataFrame:
        """Reduce multi_label → single-label (inner dimension): keep last label."""
        log.warning(
            "Converting multi-label to single-label for field '%s': keeping the last label only. Data may be lost.",
            input_col,
        )
        if input_is_list:
            # List(List(dtype)) → List(dtype): take last element of each inner list
            return df.with_columns(pl.col(input_col).list.eval(pl.element().list.last()).alias(output_col))
        # List(dtype) → dtype: take the last element
        return df.with_columns(pl.col(input_col).list.last().alias(output_col))

    def _expand_multi_label(
        self, df: pl.DataFrame, input_col: str, output_col: str, input_is_list: bool
    ) -> pl.DataFrame:
        """Expand single-label → multi_label (inner dimension): wrap in list."""
        if input_is_list:
            # List(dtype) → List(List(dtype)): wrap each element in the list
            return df.with_columns(pl.col(input_col).list.eval(pl.concat_list(pl.element())).alias(output_col))
        # dtype → List(dtype): wrap the scalar value in a list, preserving nulls
        return df.with_columns(
            pl.when(pl.col(input_col).is_not_null())
            .then(pl.concat_list(pl.col(input_col)))
            .otherwise(pl.lit(None, dtype=pl.List(self.input_label.field.dtype)))
            .alias(output_col)
        )

    def _convert_is_list(
        self, df: pl.DataFrame, src_col: str, output_col: str, input_is_list: bool, output_multi: bool
    ) -> pl.DataFrame:
        """Handle is_list conversion (outer dimension)."""
        if input_is_list:
            log.warning(
                "Converting list to non-list for field '%s': keeping the last element only. Data may be lost.",
                src_col,
            )
            # List(X) → X: take the last element
            return df.with_columns(pl.col(src_col).list.last().alias(output_col))
        # X → List(X): wrap each sample's value in a 1-element list, preserving nulls
        if not output_multi:
            # Scalar → List(scalar): use native concat_list (fast path)
            return df.with_columns(
                pl.when(pl.col(src_col).is_not_null())
                .then(pl.concat_list(pl.col(src_col)))
                .otherwise(pl.lit(None, dtype=self.output_label.field._pl_type))
                .alias(output_col)
            )
        # List(X) → List(List(X))
        target_pl_type = self.output_label.field._pl_type
        return df.with_columns(
            pl.col(src_col)
            .map_elements(lambda x: [x] if x is not None else None, return_dtype=target_pl_type)
            .alias(output_col)
        )

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """Convert label data between different multi_label/is_list configurations."""
        input_col = self.input_label.name
        output_col = self.output_label.name

        input_multi = self.input_label.field.multi_label
        output_multi = self.output_label.field.multi_label
        input_is_list = self.input_label.field.is_list
        output_is_list = self.output_label.field.is_list

        # Special case: swapping multi_label and is_list flags.
        # When one flag goes True→False and the other False→True the underlying
        # Polars type is identical (both are List(dtype))
        if input_multi != output_multi and input_is_list != output_is_list:
            if input_multi and not output_multi and not input_is_list and output_is_list:
                # List(dtype) [multi_label] → List(dtype) [is_list]: no-op rename
                return df.with_columns(pl.col(input_col).alias(output_col))
            if not input_multi and output_multi and input_is_list and not output_is_list:
                # List(dtype) [is_list] → List(dtype) [multi_label]: ensure uniqueness
                return df.with_columns(pl.col(input_col).list.unique(maintain_order=True).alias(output_col))

        # Step 1: handle multi_label conversion (inner dimension)
        if input_multi and not output_multi:
            df = self._convert_multi_label(df, input_col, output_col, input_is_list)
        elif not input_multi and output_multi:
            df = self._expand_multi_label(df, input_col, output_col, input_is_list)

        # After step 1 the multi_label dimension matches the output.
        # The effective is_list state is still ``input_is_list``.

        # Step 2: handle is_list conversion (outer dimension)
        if input_is_list != output_is_list:
            # Determine the column to read from (may have been updated in step 1)
            step2_col = output_col if input_multi != output_multi else input_col
            df = self._convert_is_list(df, step2_col, output_col, input_is_list, output_multi)

        return df


@converter
class LabelDtypeConverter(Converter):
    """Convert Label field between different data types."""

    input_label: AttributeSpec[LabelField]
    output_label: AttributeSpec[LabelField]

    def filter_output_spec(self) -> bool:
        """Configure output label specification with target dtype."""
        self.output_label = AttributeSpec(
            name=self.output_label.name,
            field=LabelField(
                semantic=self.input_label.field.semantic,
                dtype=self.output_label.field.dtype,
                multi_label=self.input_label.field.multi_label,
                is_list=self.input_label.field.is_list,
            ),
        )
        return self.input_label.field.dtype != self.output_label.field.dtype

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """Convert label data to target dtype."""
        input_col = self.input_label.name
        output_col = self.output_label.name
        target_dtype = self.output_label.field.dtype

        if self.input_label.field.multi_label and self.input_label.field.is_list:
            # List(List(dtype)) → List(List(target_dtype)): cast inner elements
            return df.with_columns(
                pl.col(input_col).list.eval(pl.element().list.eval(pl.element().cast(target_dtype))).alias(output_col)
            )
        if self.input_label.field.multi_label or self.input_label.field.is_list:
            return df.with_columns(pl.col(input_col).list.eval(pl.element().cast(target_dtype)).alias(output_col))
        return df.with_columns(pl.col(input_col).cast(target_dtype).alias(output_col))


@converter
class PolygonDtypeConverter(Converter):
    """Convert Polygon field between different data types."""

    input_polygon: AttributeSpec[PolygonField]
    output_polygon: AttributeSpec[PolygonField]

    def filter_output_spec(self) -> bool:
        """Configure output polygon specification with target dtype."""
        self.output_polygon = AttributeSpec(
            name=self.output_polygon.name,
            field=PolygonField(
                semantic=self.input_polygon.field.semantic,
                dtype=self.output_polygon.field.dtype,
                format=self.input_polygon.field.format,
                normalize=self.input_polygon.field.normalize,
            ),
        )
        return self.input_polygon.field.dtype != self.output_polygon.field.dtype

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """Convert polygon data to target dtype."""
        input_col = self.input_polygon.name
        output_col = self.output_polygon.name
        target_dtype = self.output_polygon.field.dtype

        # Polygon structure: List[List[Array[dtype, 2]]]
        return df.with_columns(
            pl.col(input_col)
            .list.eval(pl.element().list.eval(_create_fixed_array_cast_expr(target_dtype, 2)))
            .alias(output_col)
        )


@converter
class PolygonToBBoxConverter(Converter):
    """
    Converts polygon annotations to bounding boxes.

    Extracts the bounding box coordinates that enclose each polygon.
    """

    input_polygon: AttributeSpec[PolygonField]
    output_bbox: AttributeSpec[BBoxField]

    def filter_output_spec(self) -> bool:
        """Configure output specification for bounding box format."""
        # Configure output for bbox format
        self.output_bbox = AttributeSpec(
            name=self.output_bbox.name,
            field=BBoxField(
                semantic=self.input_polygon.field.semantic,
                dtype=self.input_polygon.field.dtype,
                format=self.output_bbox.field.format,
                normalize=self.input_polygon.field.normalize,  # Inherit normalization from polygon
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Extract bounding boxes from polygon coordinates.

        Args:
            df: DataFrame with polygon coordinates

        Returns:
            DataFrame with bounding box data in output column
        """
        input_column_name = self.input_polygon.name
        output_column_name = self.output_bbox.name

        df = df.with_columns(
            pl.col(input_column_name)
            .list.eval(
                pl.concat_arr(
                    [
                        pl.element().list.eval(pl.element().arr.get(0)).list.min(),
                        pl.element().list.eval(pl.element().arr.get(1)).list.min(),
                        pl.element().list.eval(pl.element().arr.get(0)).list.max(),
                        pl.element().list.eval(pl.element().arr.get(1)).list.max(),
                    ]
                )
            )
            .alias(output_column_name)
        )

        # Format according to output bbox format
        if self.output_bbox.field.format == "x1y1x2y2":
            # Already in this format
            pass
        elif self.output_bbox.field.format == "xywh":
            df = df.with_columns(
                pl.col(output_column_name).list.eval(
                    pl.concat_arr(
                        [
                            pl.element().arr.get(0),
                            pl.element().arr.get(1),
                            pl.element().arr.get(2) - pl.element().arr.get(0),
                            pl.element().arr.get(3) - pl.element().arr.get(1),
                        ]
                    )
                )
            )
        else:
            raise NotImplementedError(
                f"This conversion is not yet implemented for the format {self.output_bbox.field.format}."
            )

        return df


@converter
class RotatedBBoxToPolygonConverter(Converter):
    """
    Converts rotated bounding boxes to polygon coordinates.

    Transforms rotated bounding box parameters (cx, cy, w, h, r) into
    polygon corner points by rotating the rectangle corners around the center.
    """

    input_rotated_bbox: AttributeSpec[RotatedBBoxField]
    output_polygon: AttributeSpec[PolygonField]

    def filter_output_spec(self) -> bool:
        """Configure output specification for polygon format."""
        # Configure output for polygon format
        self.output_polygon = AttributeSpec(
            name=self.output_polygon.name,
            field=PolygonField(
                semantic=self.input_rotated_bbox.field.semantic,
                dtype=self.input_rotated_bbox.field.dtype,
                format=self.output_polygon.field.format,
                normalize=self.input_rotated_bbox.field.normalize,  # Inherit normalization
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert rotated bounding boxes to polygon corner points.

        Args:
            df: DataFrame with rotated bounding box coordinates

        Returns:
            DataFrame with polygon data in output column
        """
        input_column_name = self.input_rotated_bbox.name
        output_column_name = self.output_polygon.name

        cx = pl.element().arr.get(0)
        cy = pl.element().arr.get(1)
        w = pl.element().arr.get(2)
        h = pl.element().arr.get(3)
        r = pl.element().arr.get(4)

        def rotate_corner(expr: pl.Expr):
            px = expr.arr.get(0)
            py = expr.arr.get(1)
            cos_theta = r.cos()
            sin_theta = r.sin()
            return pl.concat_arr(cos_theta * px - sin_theta * py + cx, sin_theta * px + cos_theta * py + cy)

        return df.with_columns(
            pl.col(input_column_name)
            .list.eval(
                pl.concat_list(
                    rotate_corner(pl.concat_arr(-w / 2, -h / 2)),
                    rotate_corner(pl.concat_arr(w / 2, -h / 2)),
                    rotate_corner(pl.concat_arr(w / 2, h / 2)),
                    rotate_corner(pl.concat_arr(-w / 2, h / 2)),
                )
            )
            .alias(output_column_name)
        )


@converter
class KeypointsDtypeConverter(Converter):
    """Convert Keypoints field between different data types."""

    input_keypoints: AttributeSpec[KeypointsField]
    output_keypoints: AttributeSpec[KeypointsField]

    def filter_output_spec(self) -> bool:
        """Configure output keypoints specification with target dtype."""
        self.output_keypoints = AttributeSpec(
            name=self.output_keypoints.name,
            field=KeypointsField(
                semantic=self.input_keypoints.field.semantic,
                dtype=self.output_keypoints.field.dtype,
                normalize=self.input_keypoints.field.normalize,
            ),
        )
        return self.input_keypoints.field.dtype != self.output_keypoints.field.dtype

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """Convert keypoints data to target dtype."""
        return _convert_fixed_array_dtype(
            df,
            self.input_keypoints.name,
            self.output_keypoints.name,
            self.output_keypoints.field.dtype,
            array_size=3,  # Keypoints have 3 elements: x, y, visibility
        )


@converter
class KeypointsCoordinateConverter(Converter):
    """
    Convert keypoints coordinates between normalized and absolute formats.

    This converter handles transformations between normalized coordinates
    (range [0,1]) and absolute pixel coordinates using image dimensions.
    Only x and y coordinates are normalized/denormalized, visibility remains unchanged.
    """

    input_keypoints: AttributeSpec[KeypointsField]
    input_image: AttributeSpec[ImageField]
    output_keypoints: AttributeSpec[KeypointsField]

    def filter_output_spec(self) -> bool:
        """
        Check if keypoints normalization conversion is needed and configure output.

        Returns:
            True if conversion is needed (normalization status differs), False otherwise
        """
        input_normalized = self.input_keypoints.field.normalize
        output_normalized = self.output_keypoints.field.normalize

        # Configure output specification with correct normalization
        self.output_keypoints = AttributeSpec(
            name=self.output_keypoints.name,
            field=KeypointsField(
                semantic=self.input_keypoints.field.semantic,
                dtype=self.input_keypoints.field.dtype,
                normalize=output_normalized,
            ),
        )

        # Apply converter only if normalization status needs to change
        return input_normalized != output_normalized

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert keypoints coordinates between normalized and absolute formats.

        Uses image dimensions to transform coordinates. Only x and y are transformed,
        visibility (third element) remains unchanged.

        Args:
            df: Input DataFrame containing keypoints and image data

        Returns:
            DataFrame with converted keypoints coordinates
        """
        input_keypoints_name = self.input_keypoints.name
        input_image_name = self.input_image.name
        output_keypoints_name = self.output_keypoints.name

        # Get the image shape column name
        image_shape_name = f"{input_image_name}_shape"

        input_normalized = self.input_keypoints.field.normalize

        def op(x: pl.Expr, y: pl.Expr) -> pl.Expr:
            """Choose operation based on conversion direction."""
            xy = x * y if input_normalized else x / y
            return xy.cast(self.output_keypoints.field.dtype)

        # Apply coordinate transformation: only x (index 0) and y (index 1) are transformed
        # visibility (index 2) remains unchanged
        return df.with_columns(
            list_eval_ref(
                input_keypoints_name,
                image_shape_name,
                lambda element, ref: pl.concat_arr(
                    op(element.arr.get(0), ref.list.get(1)),  # x * width or x / width
                    op(element.arr.get(1), ref.list.get(0)),  # y * height or y / height
                    element.arr.get(2),  # visibility unchanged
                ),
            ).alias(output_keypoints_name)
        )


@converter
class EllipseDtypeConverter(Converter):
    """Convert Ellipse field between different data types."""

    input_ellipse: AttributeSpec[EllipseField]
    output_ellipse: AttributeSpec[EllipseField]

    def filter_output_spec(self) -> bool:
        """Configure output ellipse specification with target dtype."""
        self.output_ellipse = AttributeSpec(
            name=self.output_ellipse.name,
            field=EllipseField(
                semantic=self.input_ellipse.field.semantic,
                dtype=self.output_ellipse.field.dtype,
                format=self.input_ellipse.field.format,
                normalize=self.input_ellipse.field.normalize,
            ),
        )
        return self.input_ellipse.field.dtype != self.output_ellipse.field.dtype

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """Convert ellipse data to target dtype."""
        return _convert_fixed_array_dtype(
            df,
            self.input_ellipse.name,
            self.output_ellipse.name,
            self.output_ellipse.field.dtype,
            array_size=4,  # Ellipse has 4 elements like bbox
        )


@converter
class EllipseCoordinateConverter(Converter):
    """
    Convert ellipse coordinates between normalized and absolute formats.

    This converter handles transformations between normalized coordinates
    (range [0,1]) and absolute pixel coordinates using image dimensions.
    """

    input_ellipse: AttributeSpec[EllipseField]
    input_image: AttributeSpec[ImageField]
    output_ellipse: AttributeSpec[EllipseField]

    def filter_output_spec(self) -> bool:
        """
        Check if ellipse normalization conversion is needed and configure output.

        Returns:
            True if conversion is needed (normalization status differs), False otherwise
        """
        input_normalized = self.input_ellipse.field.normalize
        output_normalized = self.output_ellipse.field.normalize

        # Configure output specification with correct normalization
        self.output_ellipse = AttributeSpec(
            name=self.output_ellipse.name,
            field=EllipseField(
                semantic=self.input_ellipse.field.semantic,
                dtype=self.input_ellipse.field.dtype,
                format=self.input_ellipse.field.format,
                normalize=output_normalized,
            ),
        )

        # Apply converter only if normalization status needs to change
        return input_normalized != output_normalized

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert ellipse coordinates between normalized and absolute formats.

        Uses image dimensions to transform coordinates. For normalized to absolute:
        multiplies by image dimensions. For absolute to normalized: divides by
        image dimensions.

        Args:
            df: Input DataFrame containing ellipse and image data

        Returns:
            DataFrame with converted ellipse coordinates
        """
        input_ellipse_name = self.input_ellipse.name
        input_image_name = self.input_image.name
        output_ellipse_name = self.output_ellipse.name

        # Get the image shape column name
        image_shape_name = f"{input_image_name}_shape"

        input_normalized = self.input_ellipse.field.normalize

        # Coordinate order for width/height mapping: [width, height, width, height] for x1y1x2y2
        coordinates_order = [1, 0, 1, 0]

        def op(x: pl.Expr, y: pl.Expr) -> pl.Expr:
            """Choose operation based on conversion direction."""
            xy = x * y if input_normalized else x / y
            return xy.cast(self.output_ellipse.field.dtype)

        # Apply coordinate transformation
        return df.with_columns(
            list_eval_ref(
                input_ellipse_name,
                image_shape_name,
                lambda element, ref: pl.concat_arr(
                    op(element.arr.get(0), ref.list.get(coordinates_order[0])),
                    op(element.arr.get(1), ref.list.get(coordinates_order[1])),
                    op(element.arr.get(2), ref.list.get(coordinates_order[2])),
                    op(element.arr.get(3), ref.list.get(coordinates_order[3])),
                ),
            ).alias(output_ellipse_name)
        )


@converter
class PolygonCoordinateConverter(Converter):
    """
    Convert polygon coordinates between normalized and absolute formats.

    This converter handles transformations between normalized coordinates
    (range [0,1]) and absolute pixel coordinates using image dimensions.
    """

    input_polygon: AttributeSpec[PolygonField]
    input_image: AttributeSpec[ImageField]
    output_polygon: AttributeSpec[PolygonField]

    def filter_output_spec(self) -> bool:
        """
        Check if polygon normalization conversion is needed and configure output.

        Returns:
            True if conversion is needed (normalization status differs), False otherwise
        """
        input_normalized = self.input_polygon.field.normalize
        output_normalized = self.output_polygon.field.normalize

        # Configure output specification with correct normalization
        self.output_polygon = AttributeSpec(
            name=self.output_polygon.name,
            field=PolygonField(
                semantic=self.input_polygon.field.semantic,
                dtype=self.input_polygon.field.dtype,
                format=self.input_polygon.field.format,
                normalize=output_normalized,
            ),
        )

        # Apply converter only if normalization status needs to change
        return input_normalized != output_normalized

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert polygon coordinates between normalized and absolute formats.

        Uses image dimensions to transform coordinates. For normalized to absolute:
        multiplies by image dimensions. For absolute to normalized: divides by
        image dimensions.

        Args:
            df: Input DataFrame containing polygon and image data

        Returns:
            DataFrame with converted polygon coordinates
        """
        input_polygon_name = self.input_polygon.name
        input_image_name = self.input_image.name
        output_polygon_name = self.output_polygon.name

        # Get the image shape column name
        image_shape_name = f"{input_image_name}_shape"

        input_normalized = self.input_polygon.field.normalize

        def op(x: pl.Expr, y: pl.Expr) -> pl.Expr:
            """Choose operation based on conversion direction."""
            xy = x * y if input_normalized else x / y
            return xy.cast(self.output_polygon.field.dtype)

        # Polygon structure: List[List[Array[dtype, 2]]]
        # For each polygon (outer list), for each point (inner list), transform [x, y]
        return df.with_columns(
            pl.struct([pl.col(input_polygon_name), pl.col(image_shape_name)])
            .map_elements(
                lambda row: (
                    [
                        [
                            [
                                (
                                    point[0] * row[image_shape_name][1]
                                    if input_normalized
                                    else point[0] / row[image_shape_name][1]
                                ),
                                (
                                    point[1] * row[image_shape_name][0]
                                    if input_normalized
                                    else point[1] / row[image_shape_name][0]
                                ),
                            ]
                            for point in polygon
                        ]
                        for polygon in row[input_polygon_name]
                    ]
                    if row[input_polygon_name] is not None
                    else None
                ),
                return_dtype=pl.List(pl.List(pl.Array(self.output_polygon.field.dtype, 2))),
            )
            .alias(output_polygon_name)
        )


@converter
class RotatedBBoxCoordinateConverter(Converter):
    """
    Convert rotated bounding box coordinates between normalized and absolute formats.

    This converter handles transformations between normalized coordinates
    (range [0,1]) and absolute pixel coordinates using image dimensions.
    The rotation angle remains unchanged during normalization.
    """

    input_rotated_bbox: AttributeSpec[RotatedBBoxField]
    input_image: AttributeSpec[ImageField]
    output_rotated_bbox: AttributeSpec[RotatedBBoxField]

    def filter_output_spec(self) -> bool:
        """
        Check if rotated bbox normalization conversion is needed and configure output.

        Returns:
            True if conversion is needed (normalization status differs), False otherwise
        """
        input_normalized = self.input_rotated_bbox.field.normalize
        output_normalized = self.output_rotated_bbox.field.normalize

        # Configure output specification with correct normalization
        self.output_rotated_bbox = AttributeSpec(
            name=self.output_rotated_bbox.name,
            field=RotatedBBoxField(
                semantic=self.input_rotated_bbox.field.semantic,
                dtype=self.input_rotated_bbox.field.dtype,
                format=self.input_rotated_bbox.field.format,
                normalize=output_normalized,
            ),
        )

        # Apply converter only if normalization status needs to change
        return input_normalized != output_normalized

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert rotated bbox coordinates between normalized and absolute formats.

        For cxcywhr format: cx, w are scaled by width; cy, h are scaled by height.
        The rotation angle r remains unchanged.

        Args:
            df: Input DataFrame containing rotated bbox and image data

        Returns:
            DataFrame with converted rotated bounding box coordinates
        """
        input_rbbox_name = self.input_rotated_bbox.name
        input_image_name = self.input_image.name
        output_rbbox_name = self.output_rotated_bbox.name

        # Get the image shape column name
        image_shape_name = f"{input_image_name}_shape"

        input_normalized = self.input_rotated_bbox.field.normalize

        def op(x: pl.Expr, y: pl.Expr) -> pl.Expr:
            """Choose operation based on conversion direction."""
            xy = x * y if input_normalized else x / y
            return xy.cast(self.output_rotated_bbox.field.dtype)

        # For cxcywhr format: [cx, cy, w, h, r]
        # cx and w are scaled by width (index 1 in shape)
        # cy and h are scaled by height (index 0 in shape)
        # r remains unchanged
        return df.with_columns(
            list_eval_ref(
                input_rbbox_name,
                image_shape_name,
                lambda element, ref: pl.concat_arr(
                    op(element.arr.get(0), ref.list.get(1)),  # cx * width or cx / width
                    op(element.arr.get(1), ref.list.get(0)),  # cy * height or cy / height
                    op(element.arr.get(2), ref.list.get(1)),  # w * width or w / width
                    op(element.arr.get(3), ref.list.get(0)),  # h * height or h / height
                    element.arr.get(4),  # r unchanged
                ),
            ).alias(output_rbbox_name)
        )


@converter
class BBoxFormatConverter(Converter):
    """
    Convert bounding box between different formats.

    Supports conversions between:
    - x1y1x2y2: top-left and bottom-right corners (x1, y1, x2, y2)
    - xywh: top-left corner and dimensions (x, y, width, height)
    - cxcywh: center and dimensions (center_x, center_y, width, height)
    """

    input_bbox: AttributeSpec[BBoxField]
    output_bbox: AttributeSpec[BBoxField]

    def filter_output_spec(self) -> bool:
        """
        Check if bbox format conversion is needed and configure output.

        Returns:
            True if conversion is needed (format differs), False otherwise
        """
        input_format = self.input_bbox.field.format
        output_format = self.output_bbox.field.format

        # Configure output specification with correct format
        self.output_bbox = AttributeSpec(
            name=self.output_bbox.name,
            field=BBoxField(
                semantic=self.input_bbox.field.semantic,
                dtype=self.input_bbox.field.dtype,
                format=output_format,
                normalize=self.input_bbox.field.normalize,
            ),
        )

        # Apply converter only if format needs to change
        return input_format != output_format

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert bbox format.

        Args:
            df: Input DataFrame containing bbox data

        Returns:
            DataFrame with converted bounding box format
        """
        input_bbox_name = self.input_bbox.name
        output_bbox_name = self.output_bbox.name
        input_format = self.input_bbox.field.format
        output_format = self.output_bbox.field.format

        # First convert to x1y1x2y2 as intermediate format
        if input_format == "x1y1x2y2":
            # Already in x1y1x2y2 format
            intermediate_expr = pl.col(input_bbox_name)
        elif input_format == "xywh":
            # Convert xywh to x1y1x2y2: [x, y, w, h] -> [x, y, x+w, y+h]
            intermediate_expr = pl.col(input_bbox_name).list.eval(
                pl.concat_arr(
                    pl.element().arr.get(0),  # x1 = x
                    pl.element().arr.get(1),  # y1 = y
                    pl.element().arr.get(0) + pl.element().arr.get(2),  # x2 = x + w
                    pl.element().arr.get(1) + pl.element().arr.get(3),  # y2 = y + h
                )
            )
        elif input_format == "cxcywh":
            # Convert cxcywh to x1y1x2y2: [cx, cy, w, h] -> [cx-w/2, cy-h/2, cx+w/2, cy+h/2]
            intermediate_expr = pl.col(input_bbox_name).list.eval(
                pl.concat_arr(
                    (pl.element().arr.get(0) - pl.element().arr.get(2) / 2).clip(lower_bound=0),  # x1 = cx - w/2
                    (pl.element().arr.get(1) - pl.element().arr.get(3) / 2).clip(lower_bound=0),  # y1 = cy - h/2
                    pl.element().arr.get(0) + pl.element().arr.get(2) / 2,  # x2 = cx + w/2
                    pl.element().arr.get(1) + pl.element().arr.get(3) / 2,  # y2 = cy + h/2
                )
            )
        else:
            raise NotImplementedError(f"Input format '{input_format}' is not supported.")

        # Then convert from x1y1x2y2 to target format
        if output_format == "x1y1x2y2":
            # Already in target format
            final_expr = intermediate_expr
        elif output_format == "xywh":
            # Convert x1y1x2y2 to xywh: [x1, y1, x2, y2] -> [x1, y1, x2-x1, y2-y1]
            df = df.with_columns(intermediate_expr.alias("_intermediate_bbox"))
            final_expr = pl.col("_intermediate_bbox").list.eval(
                pl.concat_arr(
                    pl.element().arr.get(0),  # x = x1
                    pl.element().arr.get(1),  # y = y1
                    pl.element().arr.get(2) - pl.element().arr.get(0),  # w = x2 - x1
                    pl.element().arr.get(3) - pl.element().arr.get(1),  # h = y2 - y1
                )
            )
        elif output_format == "cxcywh":
            # Convert x1y1x2y2 to cxcywh: [x1, y1, x2, y2] -> [(x1+x2)/2, (y1+y2)/2, x2-x1, y2-y1]
            df = df.with_columns(intermediate_expr.alias("_intermediate_bbox"))
            final_expr = pl.col("_intermediate_bbox").list.eval(
                pl.concat_arr(
                    (pl.element().arr.get(0) + pl.element().arr.get(2)) / 2,  # cx = (x1+x2)/2
                    (pl.element().arr.get(1) + pl.element().arr.get(3)) / 2,  # cy = (y1+y2)/2
                    pl.element().arr.get(2) - pl.element().arr.get(0),  # w = x2 - x1
                    pl.element().arr.get(3) - pl.element().arr.get(1),  # h = y2 - y1
                )
            )
        else:
            raise NotImplementedError(f"Output format '{output_format}' is not supported.")

        result_df = df.with_columns(final_expr.alias(output_bbox_name))

        # Clean up intermediate column if created
        if "_intermediate_bbox" in result_df.columns:
            result_df = result_df.drop("_intermediate_bbox")

        return result_df


@converter
class BBoxToPolygonConverter(Converter):
    """
    Converts bounding boxes to polygon coordinates.

    Transforms bounding box corners into polygon vertices (4 corner points).
    """

    input_bbox: AttributeSpec[BBoxField]
    output_polygon: AttributeSpec[PolygonField]

    def filter_output_spec(self) -> bool:
        """Configure output specification for polygon format."""
        self.output_polygon = AttributeSpec(
            name=self.output_polygon.name,
            field=PolygonField(
                semantic=self.input_bbox.field.semantic,
                dtype=self.input_bbox.field.dtype,
                format=self.output_polygon.field.format,
                normalize=self.input_bbox.field.normalize,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert bounding boxes to polygon corner points.

        For x1y1x2y2 format: creates 4 corners clockwise from top-left.

        Args:
            df: DataFrame with bounding box coordinates

        Returns:
            DataFrame with polygon data in output column
        """
        input_column_name = self.input_bbox.name
        output_column_name = self.output_polygon.name
        input_format = self.input_bbox.field.format

        if input_format == "x1y1x2y2":
            # [x1, y1, x2, y2] -> [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
            result_df = df.with_columns(
                pl.col(input_column_name)
                .list.eval(
                    pl.concat_list(
                        pl.concat_arr(pl.element().arr.get(0), pl.element().arr.get(1)),  # top-left
                        pl.concat_arr(pl.element().arr.get(2), pl.element().arr.get(1)),  # top-right
                        pl.concat_arr(pl.element().arr.get(2), pl.element().arr.get(3)),  # bottom-right
                        pl.concat_arr(pl.element().arr.get(0), pl.element().arr.get(3)),  # bottom-left
                    )
                )
                .alias(output_column_name)
            )
        elif input_format == "xywh":
            # [x, y, w, h] -> [[x,y], [x+w,y], [x+w,y+h], [x,y+h]]
            result_df = df.with_columns(
                pl.col(input_column_name)
                .list.eval(
                    pl.concat_list(
                        pl.concat_arr(pl.element().arr.get(0), pl.element().arr.get(1)),  # top-left
                        pl.concat_arr(
                            pl.element().arr.get(0) + pl.element().arr.get(2), pl.element().arr.get(1)
                        ),  # top-right
                        pl.concat_arr(
                            pl.element().arr.get(0) + pl.element().arr.get(2),
                            pl.element().arr.get(1) + pl.element().arr.get(3),
                        ),  # bottom-right
                        pl.concat_arr(
                            pl.element().arr.get(0), pl.element().arr.get(1) + pl.element().arr.get(3)
                        ),  # bottom-left
                    )
                )
                .alias(output_column_name)
            )
        else:
            raise NotImplementedError(f"Input format '{input_format}' is not supported for BBoxToPolygonConverter.")

        return result_df


@converter
class EllipseToBBoxConverter(Converter):
    """
    Converts ellipse annotations to bounding boxes.

    Since ellipses use the same x1y1x2y2 format as bboxes, this is primarily
    a field type conversion.
    """

    input_ellipse: AttributeSpec[EllipseField]
    output_bbox: AttributeSpec[BBoxField]

    def filter_output_spec(self) -> bool:
        """Configure output specification for bounding box format."""
        self.output_bbox = AttributeSpec(
            name=self.output_bbox.name,
            field=BBoxField(
                semantic=self.input_ellipse.field.semantic,
                dtype=self.input_ellipse.field.dtype,
                format=self.output_bbox.field.format,
                normalize=self.input_ellipse.field.normalize,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert ellipse to bounding box.

        Since both use the same coordinate format, this is a direct copy
        with optional format conversion.

        Args:
            df: DataFrame with ellipse coordinates

        Returns:
            DataFrame with bounding box data in output column
        """
        input_column_name = self.input_ellipse.name
        output_column_name = self.output_bbox.name
        input_format = self.input_ellipse.field.format
        output_format = self.output_bbox.field.format

        # Ellipse uses same format as bbox, so if formats match, direct copy
        if input_format == output_format:
            return df.with_columns(pl.col(input_column_name).alias(output_column_name))

        # Otherwise, need format conversion
        # First convert to x1y1x2y2 as intermediate
        if input_format == "x1y1x2y2":
            intermediate_expr = pl.col(input_column_name)
        elif input_format == "xywh":
            intermediate_expr = pl.col(input_column_name).list.eval(
                pl.concat_arr(
                    pl.element().arr.get(0),
                    pl.element().arr.get(1),
                    pl.element().arr.get(0) + pl.element().arr.get(2),
                    pl.element().arr.get(1) + pl.element().arr.get(3),
                )
            )
        else:
            raise NotImplementedError(f"Input format '{input_format}' is not supported.")

        # Then convert to target format
        if output_format == "x1y1x2y2":
            final_expr = intermediate_expr
        elif output_format == "xywh":
            df = df.with_columns(intermediate_expr.alias("_intermediate"))
            final_expr = pl.col("_intermediate").list.eval(
                pl.concat_arr(
                    pl.element().arr.get(0),
                    pl.element().arr.get(1),
                    pl.element().arr.get(2) - pl.element().arr.get(0),
                    pl.element().arr.get(3) - pl.element().arr.get(1),
                )
            )
        else:
            raise NotImplementedError(f"Output format '{output_format}' is not supported.")

        result_df = df.with_columns(final_expr.alias(output_column_name))

        if "_intermediate" in result_df.columns:
            result_df = result_df.drop("_intermediate")

        return result_df


@converter
class KeypointsToBBoxConverter(Converter):
    """
    Converts keypoints to bounding box that encloses all visible keypoints.

    Only considers keypoints with visibility > 0 when computing the bounding box.
    """

    input_keypoints: AttributeSpec[KeypointsField]
    output_bbox: AttributeSpec[BBoxField]

    def filter_output_spec(self) -> bool:
        """Configure output specification for bounding box format."""
        self.output_bbox = AttributeSpec(
            name=self.output_bbox.name,
            field=BBoxField(
                semantic=self.input_keypoints.field.semantic,
                dtype=self.input_keypoints.field.dtype,
                format=self.output_bbox.field.format,
                normalize=self.input_keypoints.field.normalize,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Compute bounding box enclosing all visible keypoints.

        Args:
            df: DataFrame with keypoints coordinates

        Returns:
            DataFrame with bounding box data in output column
        """
        input_column_name = self.input_keypoints.name
        output_column_name = self.output_bbox.name
        output_format = self.output_bbox.field.format

        # Keypoints format: List[Array[3]] where each array is [x, y, visibility]
        # We need to find min/max x,y for visible keypoints (visibility > 0)

        # Use map_elements for complex filtering logic
        def compute_bbox(keypoints_list: list | None) -> list | None:
            if keypoints_list is None or len(keypoints_list) == 0:
                return None

            # Create a single bbox for all visible keypoints
            visible_x = []
            visible_y = []

            for kp in keypoints_list:
                if kp[2] > 0:  # visibility > 0
                    visible_x.append(kp[0])
                    visible_y.append(kp[1])

            if not visible_x:
                return None

            x1, y1 = min(visible_x), min(visible_y)
            x2, y2 = max(visible_x), max(visible_y)

            if output_format == "x1y1x2y2":
                return [[x1, y1, x2, y2]]
            if output_format == "xywh":
                return [[x1, y1, x2 - x1, y2 - y1]]
            if output_format == "cxcywh":
                return [[(x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1]]
            return [[x1, y1, x2, y2]]

        return df.with_columns(
            pl.col(input_column_name)
            .map_elements(compute_bbox, return_dtype=pl.List(pl.Array(self.output_bbox.field.dtype, 4)))
            .alias(output_column_name)
        )


@converter
class RotatedBBoxToBBoxConverter(Converter):
    """
    Converts rotated bounding boxes to axis-aligned bounding boxes.

    Computes the axis-aligned bounding box that encloses the rotated bbox.
    """

    input_rotated_bbox: AttributeSpec[RotatedBBoxField]
    output_bbox: AttributeSpec[BBoxField]

    def filter_output_spec(self) -> bool:
        """Configure output specification for bounding box format."""
        self.output_bbox = AttributeSpec(
            name=self.output_bbox.name,
            field=BBoxField(
                semantic=self.input_rotated_bbox.field.semantic,
                dtype=self.input_rotated_bbox.field.dtype,
                format=self.output_bbox.field.format,
                normalize=self.input_rotated_bbox.field.normalize,
            ),
        )
        return True

    def convert(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Convert rotated bounding boxes to axis-aligned bounding boxes.

        First converts to polygon corners, then finds min/max to get AABB.

        Args:
            df: DataFrame with rotated bounding box coordinates

        Returns:
            DataFrame with bounding box data in output column
        """
        input_column_name = self.input_rotated_bbox.name
        output_column_name = self.output_bbox.name
        output_format = self.output_bbox.field.format

        # For each rotated bbox [cx, cy, w, h, r], compute the 4 corner points
        # then find the axis-aligned bounding box
        import math

        def rotated_bbox_to_aabb(rbbox_list: list | None) -> list | None:
            if rbbox_list is None or len(rbbox_list) == 0:
                return None

            result = []
            for rbbox in rbbox_list:
                cx, cy, w, h, r = rbbox[0], rbbox[1], rbbox[2], rbbox[3], rbbox[4]

                # Compute corner offsets
                cos_r = math.cos(r)
                sin_r = math.sin(r)

                # Half dimensions
                hw, hh = w / 2, h / 2

                # Four corners relative to center, then rotated
                corners = [
                    (cx + cos_r * (-hw) - sin_r * (-hh), cy + sin_r * (-hw) + cos_r * (-hh)),
                    (cx + cos_r * (hw) - sin_r * (-hh), cy + sin_r * (hw) + cos_r * (-hh)),
                    (cx + cos_r * (hw) - sin_r * (hh), cy + sin_r * (hw) + cos_r * (hh)),
                    (cx + cos_r * (-hw) - sin_r * (hh), cy + sin_r * (-hw) + cos_r * (hh)),
                ]

                xs = [c[0] for c in corners]
                ys = [c[1] for c in corners]

                x1, y1 = min(xs), min(ys)
                x2, y2 = max(xs), max(ys)

                if output_format == "x1y1x2y2":
                    result.append([x1, y1, x2, y2])
                elif output_format == "xywh":
                    result.append([x1, y1, x2 - x1, y2 - y1])
                elif output_format == "cxcywh":
                    result.append([(x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1])
                else:
                    result.append([x1, y1, x2, y2])

            return result

        return df.with_columns(
            pl.col(input_column_name)
            .map_elements(rotated_bbox_to_aabb, return_dtype=pl.List(pl.Array(self.output_bbox.field.dtype, 4)))
            .alias(output_column_name)
        )

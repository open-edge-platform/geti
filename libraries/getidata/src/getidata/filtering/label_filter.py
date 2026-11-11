# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Label filtering logic for datasets.

This module provides utilities for filtering datasets by label values,
supporting various LabelField configurations (single labels, multi-label fields,
list fields, and combinations).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import polars as pl

from getidata.categories import (
    BaseLabelCategories,
    HierarchicalLabelCategories,
    HierarchicalLabelCategory,
    LabelCategories,
    LabelGroup,
)
from getidata.fields.annotations import LabelField

if TYPE_CHECKING:
    from collections.abc import Sequence

    from getidata.schema import Schema


def resolve_label_field_name(schema: Schema, label_field_name: str | None) -> str:
    """Resolve and validate the label field name.

    When *label_field_name* is ``None`` the schema is scanned for a unique
    ``LabelField``.  If a name is given it is validated against the schema.

    Args:
        schema: The dataset schema to search in.
        label_field_name: Optional explicit label field name.

    Returns:
        The validated label field name.

    Raises:
        RuntimeError: If auto-detection finds zero or more than one LabelField.
        KeyError: If the given name is not present in the schema.
        TypeError: If the resolved attribute is not a LabelField.
    """
    if label_field_name is None:
        label_field_names = [
            name for name, attr_info in schema.attributes.items() if isinstance(attr_info.field, LabelField)
        ]
        if len(label_field_names) == 0:
            raise RuntimeError("Dataset schema does not contain any LabelField attributes.")
        if len(label_field_names) > 1:
            raise RuntimeError(
                f"Dataset schema contains multiple LabelField attributes: "
                f"{label_field_names}. Please specify 'label_field_name' explicitly."
            )
        label_field_name = label_field_names[0]

    if label_field_name not in schema.attributes:
        raise KeyError(
            f"Attribute '{label_field_name}' not found in the dataset schema. "
            f"Available attributes: {list(schema.attributes.keys())}"
        )

    attr_info = schema.attributes[label_field_name]
    if not isinstance(attr_info.field, LabelField):
        raise TypeError(f"Attribute '{label_field_name}' is a {type(attr_info.field).__name__}, not a LabelField.")

    return label_field_name


def resolve_label_indices(
    labels: Sequence[str | int],
    categories: Any,
    label_field_name: str,
) -> list[int]:
    """Map label names or indices to integer indices via *categories*.

    Args:
        labels: Label names (str) or indices (int) to resolve.
        categories: A ``LabelCategories`` or ``HierarchicalLabelCategories`` instance.
        label_field_name: Used only for error messages.

    Returns:
        List of integer indices corresponding to the given label names or indices.

    Raises:
        ValueError: If any label name is not found in *categories* or if any index is out of range.
        TypeError: If a label is neither a string nor an integer.
    """
    label_indices: list[int] = []
    for label in labels:
        if isinstance(label, int):
            if label < 0 or label >= len(categories.labels):
                raise ValueError(
                    f"Label index {label} is out of range for field '{label_field_name}'. "
                    f"Valid range is 0 to {len(categories.labels) - 1}. "
                    f"Available labels: {list(categories.labels)}"
                )
            label_indices.append(label)
        elif isinstance(label, str):
            idx, _ = categories.find(label)
            if idx is None:
                raise ValueError(
                    f"Label '{label}' not found in categories for field '{label_field_name}'. "
                    f"Available labels: {list(categories.labels)}"
                )
            label_indices.append(idx)
        else:
            raise TypeError(
                f"Label must be a string (label name) or int (label index), got {type(label).__name__}: {label}"
            )
    return label_indices


def find_associated_annotation_fields(
    schema: Schema,
    label_field_name: str,
    label_field_instance: LabelField,
) -> list[str]:
    """Find annotation fields that are associated with a label field by semantic.

    Associated annotation fields are those that:
    1. Have the same semantic value as the label field
    2. Are not the label field itself
    3. Are list-type fields (storing multiple annotations per sample)

    Args:
        schema: The dataset schema.
        label_field_name: Name of the label field.
        label_field_instance: The LabelField instance.

    Returns:
        List of field names that are associated with the label field.
    """
    associated_fields: list[str] = []
    label_semantic = label_field_instance.semantic

    for attr_name, attr_info in schema.attributes.items():
        if attr_name == label_field_name:
            continue

        field = attr_info.field
        # Check if the field has the same semantic
        if hasattr(field, "semantic") and field.semantic == label_semantic:
            # For is_list label fields, we need to filter associated list-type annotation fields
            # These are typically BBoxField, PolygonField, KeypointsField, etc.
            # which store lists of annotations as pl.List(...)
            polars_schema = field.to_polars_schema(attr_name)
            for col_dtype in polars_schema.values():
                # Check if it's a list type (annotations are stored as lists)
                if isinstance(col_dtype, pl.List):
                    associated_fields.append(attr_name)
                    break

    return associated_fields


def _filter_associated_fields(
    df: pl.DataFrame,
    keep_mask_expr: pl.Expr,
    associated_fields: list[str],
) -> list[pl.Expr]:
    """Build column expressions to filter associated annotation fields using a mask.

    Args:
        df: The DataFrame being filtered.
        keep_mask_expr: Boolean mask expression indicating which elements to keep.
        associated_fields: List of field names to filter.

    Returns:
        List of Polars expressions to update the associated fields.
    """
    columns_to_update: list[pl.Expr] = []
    for field_name in associated_fields:
        if field_name in df.columns:

            def filter_by_mask(s: dict[str, Any], fname: str = field_name) -> list[Any] | None:
                if s[fname] is None or s["__mask__"] is None:
                    return None
                return [v for v, m in zip(s[fname], s["__mask__"]) if m]

            columns_to_update.append(
                pl.struct([pl.col(field_name), keep_mask_expr.alias("__mask__")])
                .map_elements(
                    filter_by_mask,
                    return_dtype=df.schema[field_name],
                )
                .alias(field_name)
            )
    return columns_to_update


def _filter_list_and_multi_label(
    df: pl.DataFrame,
    label_field_name: str,
    label_indices: list[int],
    schema: Schema | None,
    label_field_instance: LabelField,
    keep_empty_samples: bool,
) -> pl.DataFrame:
    """Filter DataFrame with List(List(UInt)) label structure."""
    label_col = pl.col(label_field_name)

    # Compute a boolean mask for which outer elements to keep
    keep_mask_expr = label_col.list.eval(pl.element().list.eval(pl.element().is_in(label_indices)).list.any())

    # Filter the label column: keep matching elements in inner lists, drop empty inner lists
    filtered_label_expr = (
        label_col.list.eval(
            pl.element().list.eval(pl.when(pl.element().is_in(label_indices)).then(pl.element())).list.drop_nulls()
        )
        .list.eval(pl.when(pl.element().list.len() > 0).then(pl.element()))
        .list.drop_nulls()
    )

    columns_to_update: list[pl.Expr] = [filtered_label_expr.alias(label_field_name)]

    if schema is not None:
        associated_fields = find_associated_annotation_fields(schema, label_field_name, label_field_instance)
        columns_to_update.extend(_filter_associated_fields(df, keep_mask_expr, associated_fields))

    result = df.with_columns(columns_to_update)
    if not keep_empty_samples:
        result = result.filter(label_col.is_not_null() & (label_col.list.len() > 0))
    return result


def _filter_list_label(
    df: pl.DataFrame,
    label_field_name: str,
    label_indices: list[int],
    schema: Schema | None,
    label_field_instance: LabelField,
    keep_empty_samples: bool,
) -> pl.DataFrame:
    """Filter DataFrame with List(UInt) label structure (one label per annotation)."""
    label_col = pl.col(label_field_name)

    # Compute a boolean mask for which elements to keep
    keep_mask_expr = label_col.list.eval(pl.element().is_in(label_indices))

    # Filter the label column
    filtered_label_expr = label_col.list.eval(
        pl.when(pl.element().is_in(label_indices)).then(pl.element())
    ).list.drop_nulls()

    columns_to_update: list[pl.Expr] = [filtered_label_expr.alias(label_field_name)]

    if schema is not None:
        associated_fields = find_associated_annotation_fields(schema, label_field_name, label_field_instance)
        columns_to_update.extend(_filter_associated_fields(df, keep_mask_expr, associated_fields))

    result = df.with_columns(columns_to_update)
    if not keep_empty_samples:
        result = result.filter(label_col.is_not_null() & (label_col.list.len() > 0))
    return result


def _filter_multi_label(
    df: pl.DataFrame,
    label_field_name: str,
    label_indices: list[int],
    keep_empty_samples: bool,
) -> pl.DataFrame:
    """Filter DataFrame with multi-label structure (multiple labels per sample, not per annotation)."""
    label_col = pl.col(label_field_name)

    result = df.with_columns(
        label_col.list.eval(pl.when(pl.element().is_in(label_indices)).then(pl.element())).list.drop_nulls()
    )
    if not keep_empty_samples:
        result = result.filter(label_col.is_not_null() & (label_col.list.len() > 0))
    return result


def _filter_scalar_label(
    df: pl.DataFrame,
    label_field_name: str,
    label_indices: list[int],
    keep_empty_samples: bool,
) -> pl.DataFrame:
    """Filter DataFrame with scalar label structure."""
    label_col = pl.col(label_field_name)

    if keep_empty_samples:
        # Set non-matching labels to null instead of filtering
        return df.with_columns(
            pl.when(label_col.is_in(label_indices)).then(label_col).otherwise(pl.lit(None)).alias(label_field_name)
        )
    return df.filter(label_col.is_in(label_indices))


def filter_df_by_label_indices(
    df: pl.DataFrame,
    label_field_name: str,
    label_field_instance: LabelField,
    label_indices: list[int],
    schema: Schema | None = None,
    keep_empty_samples: bool = False,
) -> pl.DataFrame:
    """Return a filtered DataFrame keeping rows that match any of *label_indices*.

    This function both filters rows (keeping only those with at least one matching label)
    AND removes non-matching labels from within each sample's label field.

    When the label field is a list type (is_list=True), this function also filters
    associated annotation fields (e.g., bboxes, polygons) that share the same semantic,
    keeping only the annotations at the same indices as the kept labels.

    The filtering strategy is chosen based on the ``is_list`` and
    ``multi_label`` flags of *label_field_instance*.

    Args:
        df: The DataFrame to filter.
        label_field_name: Name of the label column.
        label_field_instance: The LabelField instance.
        label_indices: List of label indices to keep.
        schema: Optional schema to find associated annotation fields to filter.
        keep_empty_samples: If True, keep all rows even if they have no matching labels
            (labels and annotations will be empty). If False (default), rows without
            matching labels are removed.

    Returns:
        Filtered DataFrame.
    """
    if label_field_instance.is_list and label_field_instance.multi_label:
        return _filter_list_and_multi_label(
            df, label_field_name, label_indices, schema, label_field_instance, keep_empty_samples
        )

    if label_field_instance.is_list:
        return _filter_list_label(df, label_field_name, label_indices, schema, label_field_instance, keep_empty_samples)

    if label_field_instance.multi_label:
        return _filter_multi_label(df, label_field_name, label_indices, keep_empty_samples)

    return _filter_scalar_label(df, label_field_name, label_indices, keep_empty_samples)


def remap_label_indices(
    df: pl.DataFrame,
    label_field_name: str,
    label_field_instance: LabelField,
    old_to_new_index_map: dict[int, int],
) -> pl.DataFrame:
    """Remap label indices in the DataFrame according to the provided mapping.

    Args:
        df: The DataFrame to modify.
        label_field_name: Name of the label column.
        label_field_instance: The LabelField instance.
        old_to_new_index_map: Mapping from old indices to new indices.

    Returns:
        DataFrame with remapped label indices.
    """
    col = pl.col(label_field_name)

    if label_field_instance.is_list and label_field_instance.multi_label:
        # List(List(UInt)) - remap each element in the inner lists
        return df.with_columns(
            col.list.eval(pl.element().list.eval(pl.element().replace_strict(old_to_new_index_map, default=None)))
        )

    if label_field_instance.is_list or label_field_instance.multi_label:
        # List(UInt) - remap each element in the list
        return df.with_columns(col.list.eval(pl.element().replace_strict(old_to_new_index_map, default=None)))

    # Scalar UInt - remap the single value
    return df.with_columns(col.replace_strict(old_to_new_index_map, default=None))


def expand_indices_with_ancestors(
    categories: HierarchicalLabelCategories,
    label_indices: list[int],
) -> list[int]:
    """Expand label indices to include all ancestor labels in the hierarchy.

    For each label index, traverse up the parent chain and add all ancestor
    indices to the result set.

    Args:
        categories: The hierarchical label categories.
        label_indices: Initial list of label indices to expand.

    Returns:
        List of label indices including all ancestors.
    """
    # Build a name-to-index map for quick lookup
    name_to_idx = {item.name: idx for idx, item in enumerate(categories.items)}

    expanded_indices = set(label_indices)

    for idx in label_indices:
        # Traverse up the parent chain
        current_item = categories.items[idx]
        while current_item.parent:
            parent_idx = name_to_idx.get(current_item.parent)
            if parent_idx is None:
                break
            expanded_indices.add(parent_idx)
            current_item = categories.items[parent_idx]

    return list(expanded_indices)


def create_filtered_categories(
    categories: LabelCategories | HierarchicalLabelCategories,
    sorted_indices: list[int],
) -> LabelCategories | HierarchicalLabelCategories:
    """Create new categories containing only the filtered labels.

    Args:
        categories: The original categories (LabelCategories or HierarchicalLabelCategories).
        sorted_indices: Sorted list of indices to keep.

    Returns:
        New categories instance with only the filtered labels.
    """
    filtered_labels = tuple(categories.labels[idx] for idx in sorted_indices)

    if isinstance(categories, HierarchicalLabelCategories):
        # For hierarchical categories, recreate HierarchicalLabelCategories
        # keeping only the items that match the filtered labels
        filtered_items: list[HierarchicalLabelCategory] = []
        for idx in sorted_indices:
            original_item = categories.items[idx]
            # Clear the parent if it's not in the filtered labels
            # (parent would be invalid since it's not being kept)
            new_parent = original_item.parent if original_item.parent in filtered_labels else ""
            filtered_items.append(
                HierarchicalLabelCategory(
                    name=original_item.name,
                    parent=new_parent,
                    label_semantics=original_item.label_semantics,
                )
            )

        # Filter label_groups to only include groups whose labels are in filtered_labels
        filtered_groups: list[LabelGroup] = []
        for group in categories.label_groups:
            # Keep only the labels that are in the filtered set
            kept_labels = tuple(lbl for lbl in group.labels if lbl in filtered_labels)
            if kept_labels:
                filtered_groups.append(
                    LabelGroup(
                        name=group.name,
                        labels=kept_labels,
                        group_type=group.group_type,
                    )
                )

        # Preserve label_semantics for labels that are kept
        filtered_semantics = {}
        for semantic, label_name in categories.label_semantics.items():
            if label_name in filtered_labels:
                filtered_semantics[semantic] = label_name

        return HierarchicalLabelCategories(
            items=tuple(filtered_items),
            label_groups=tuple(filtered_groups),
            label_semantics=filtered_semantics,
        )

    # For LabelCategories, create a new LabelCategories instance
    # Preserve label_semantics for labels that are kept
    filtered_semantics = {}
    if hasattr(categories, "label_semantics"):
        for semantic, label_name in categories.label_semantics.items():
            if label_name in filtered_labels:
                filtered_semantics[semantic] = label_name

    return LabelCategories(
        labels=filtered_labels,
        group_type=categories.group_type,
        label_semantics=filtered_semantics,
    )


def validate_label_categories(
    categories: Any,
    label_field_name: str,
) -> LabelCategories | HierarchicalLabelCategories:
    """Validate that the categories are appropriate for label filtering.

    Args:
        categories: The categories to validate.
        label_field_name: The name of the label field (for error messages).

    Returns:
        The validated categories.

    Raises:
        TypeError: If categories are a BaseLabelCategories subclass that is not supported.
        ValueError: If categories are not label categories.
    """
    if isinstance(categories, (LabelCategories, HierarchicalLabelCategories)):
        return categories

    if isinstance(categories, BaseLabelCategories):
        raise TypeError(
            f"Attribute '{label_field_name}' has unsupported categories type "
            f"'{type(categories).__name__}'. Expected LabelCategories or "
            f"HierarchicalLabelCategories."
        )

    raise ValueError(
        f"Attribute '{label_field_name}' does not have LabelCategories attached to the schema. "
        f"LabelCategories are required to resolve label names to indices. "
        f"Found categories: {categories}"
    )

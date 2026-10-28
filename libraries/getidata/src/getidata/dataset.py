# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import collections.abc
import types
import typing
from collections.abc import Sequence
from functools import cache
from typing import TYPE_CHECKING, Annotated, Any, Generic, TypeGuard, Union, cast, get_args, get_origin, get_type_hints

import polars as pl
from typing_extensions import TypeVar, dataclass_transform

from getidata.arrow_utils import build_series_bulk
from getidata.categories import BaseLabelCategories, HierarchicalLabelCategories
from getidata.converters.registry import ConverterTransform, find_conversion_path
from getidata.fields.annotations import LabelField
from getidata.fields.datasets import Subset, SubsetField
from getidata.filtering.label_filter import (
    create_filtered_categories,
    expand_indices_with_ancestors,
    filter_df_by_label_indices,
    remap_label_indices,
    resolve_label_field_name,
    resolve_label_indices,
    validate_label_categories,
)
from getidata.polars_utils import prepare_dataframe_for_pickle, restore_dataframe_from_pickle
from getidata.schema import AttributeInfo, Field, Schema
from getidata.transform import IdentityTransform, Transform
from getidata.type_registry import is_type_optional

if TYPE_CHECKING:
    from collections.abc import Callable

    from getidata.categories import Categories


@dataclass_transform()
class Sample:
    """
    Base class for all samples in a dataset.

    This class provides a foundation for creating sample objects with
    schema inference capabilities and flexible attribute assignment.
    """

    def __init__(self, **kwargs: Any):
        """Initialize sample with provided attributes."""
        # Get the schema to allow field coercion
        schema = self.__class__.infer_schema()

        for key, value in kwargs.items():
            # Check if the field has a coerce method to convert the value
            if key in schema.attributes:
                attr_info = schema.attributes[key]
                if hasattr(attr_info.field, "coerce"):
                    value = attr_info.field.coerce(value, attr_info.type)  # noqa: PLW2901
            setattr(self, key, value)
        self.__post_init__()
        self.validate()

    def __post_init__(self) -> None:
        pass

    def __repr__(self):
        """Return a string representation of the sample."""
        fields = ", ".join(f"{key}={getattr(self, key)}" for key in self.__dict__ if not key.startswith("_"))
        return f"{self.__class__.__name__}({fields})"

    def validate(self) -> None:
        """
        Validate the sample's attributes against the inferred schema.

        Raises:
            ValueError: If required attributes are missing
            TypeError: If attribute types do not match the schema
        """
        schema = self.__class__.infer_schema()  # Cached per class
        for name, attr_info in schema.attributes.items():
            if name not in self.__dict__:
                continue
            value = getattr(self, name)
            expected_type = attr_info.type
            field = attr_info.field

            if not self._validate_attribute_type(expected_type, value):
                raise TypeError(f"Attribute `{name}` must be of type `{expected_type}` but is type `{type(value)}`.")

            # Custom field validation (if any)
            if hasattr(field, "validate"):
                field.validate(value)

    def _validate_attribute_type(self, expected_type: Any, value: Any) -> bool:
        """
        Recursively validate attribute type, handling Union and Callable types.
        """
        # Union and Callable types have to be handled separately,
        # because isinstance() does not work with Callable types.
        origin = get_origin(expected_type)
        if origin in {Union, types.UnionType}:
            # Check each type in the Union
            result = any(self._validate_attribute_type(typ, value) for typ in get_args(expected_type))
        elif origin in {typing.Callable, collections.abc.Callable} or expected_type in {
            typing.Callable,
            collections.abc.Callable,
        }:
            result = callable(value)
        else:
            try:
                result = isinstance(value, expected_type)
            except TypeError:
                # Some complex types cannot be validated, for example, sometimes when a numpy dtype is turned
                # into a list using Polars List, the resulting complex dtype will contain a generic Any.
                result = isinstance(value, origin)
        return result

    @classmethod
    @cache
    def infer_schema(cls) -> Schema:
        """
        Infer schema from this Sample class definition.

        Returns:
            Schema: The inferred schema containing attribute information

        Raises:
            TypeError: If attributes don't have proper Field annotations
        """

        attributes: dict[str, AttributeInfo] = {}

        try:
            # Pass include_extras=True to preserve Annotated metadata
            resolved_annotations = get_type_hints(cls, include_extras=True)
        except Exception as e:
            raise TypeError(f"Failed to resolve type annotations for class '{cls.__name__}': {e}")

        # Iterate over the resolved type annotations
        for name, annotation in resolved_annotations.items():
            origin = get_origin(annotation)

            if origin is Annotated:
                # Handle Annotated[Type, Field] approach
                annotation, *annotations = get_args(annotation)  # noqa: PLW2901
                field_annotation = annotations[0] if annotations else None
            else:
                # Handle Type = field(...) approach
                field_annotation = getattr(cls, name, None)

            if not isinstance(field_annotation, Field):
                raise TypeError(f"Attribute '{name}' must have a Field annotation.")

            # Extract base class from generic types like MyClass[A, B, C] -> MyClass
            type_origin = get_origin(annotation)

            # For Union types, keep the original annotation (the Union instance)
            if isinstance(annotation, types.UnionType) or type_origin is Union:
                final_type = annotation
            else:
                final_type = type_origin if type_origin is not None else annotation

            attributes[name] = AttributeInfo(type=final_type, field=field_annotation)
        return Schema(attributes=attributes)

    def evaluate_lazy_field(self, name: str) -> Any:
        row_df = self._transforms.apply([name])

        # Now extract the value from the converted dataframe
        attr_info = self._transforms.schema.attributes[name]
        return attr_info.field.from_polars(name, 0, row_df, attr_info.type)


class LazyDescriptor:
    def __init__(self, attr_name: str, transforms: Transform) -> None:
        self._attr_name = attr_name
        self._transforms = transforms

    def __get__(self, instance: Any, _: Any) -> Any:
        """
        Create a lazy property that applies converters on demand.

        Args:
            attr_name: Name of the attribute
            attr_info: AttributeInfo for the attribute

        Returns:
            The computed value for the attribute
        """

        row_df = self._transforms.apply([self._attr_name])

        # Now extract the value from the converted dataframe
        attr_info = self._transforms.schema.attributes[self._attr_name]
        value = attr_info.field.from_polars(self._attr_name, 0, row_df, attr_info.type)

        # Cache the value and set it as a real attribute
        setattr(instance, self._attr_name, value)

        return value


DType = TypeVar("DType", bound=Sample)
DTargetType = TypeVar("DTargetType", bound=Sample)


class Dataset(Generic[DType]):
    """
    Represents a typed dataset with schema validation and conversion capabilities.

    This class provides a strongly-typed container for tabular data with support
    for complex field types, schema inference, and automatic conversions between
    different schema representations.

    Args:
        DType: The sample type this dataset contains
    """

    def __init__(
        self,
        dtype_or_schema: Schema | type[DType],
        categories: dict[str, Categories] | None = None,
        schema: Schema | None = None,
    ):
        """
        Initialize dataset with either a schema or sample type.

        Args:
            dtype_or_schema: Either a Schema instance or a Sample class type
            categories: Optional dictionary mapping attribute names to categories
            schema: Optional schema if a dtype is provided
        """
        if isinstance(dtype_or_schema, Schema):
            self._schema = dtype_or_schema
            self._dtype = cast("type[DType]", Sample)
        else:
            self._schema = dtype_or_schema.infer_schema() if schema is None else schema
            self._dtype = dtype_or_schema

        # Apply categories if provided
        if categories is not None:
            self._schema = self._schema.with_categories(categories)

        self.df = pl.DataFrame(schema=self._generate_polars_schema())
        self._transforms: Transform | None = None

    def __getstate__(self) -> dict[str, Any]:
        """
        Prepare the dataset for pickling.

        Polars DataFrames with Object columns cannot be serialized using Polars' default
        serialization. This method extracts Object columns as Python lists before pickling.
        """
        state = self.__dict__.copy()

        return prepare_dataframe_for_pickle(self.df, "df", state)

    def __setstate__(self, state: dict[str, Any]) -> None:
        """
        Restore the dataset after unpickling.

        Reconstructs Object columns from the Python lists stored during pickling.
        """
        state["df"] = restore_dataframe_from_pickle(state, "df")

        self.__dict__.update(state)

    @classmethod
    def from_dataframe(
        cls,
        df: pl.DataFrame,
        dtype_or_schema: Schema | type[DTargetType],
        transforms: Transform | None = None,
        categories: dict[str, Categories] | None = None,
        schema: Schema | None = None,
    ) -> Dataset[DTargetType]:
        """
        Create a Dataset from an existing DataFrame and lazy converters.

        Args:
            df: The Polars DataFrame containing the data
            dtype_or_schema: Either a Schema instance or a Sample class type
            transforms: Optional Transform instance to apply during sample access
            categories: Optional dictionary mapping attribute names to categories

        Returns:
            A new Dataset instance with the provided DataFrame and converters
        """
        dataset = Dataset(dtype_or_schema, categories, schema)
        dataset.df = df
        dataset._transforms = transforms
        return dataset

    @property
    def schema(self) -> Schema:
        """Get the schema of this dataset."""
        return self._schema

    @property
    def dtype(self) -> type[DType]:
        """Get the sample type of this dataset."""
        return self._dtype

    @property
    def label_categories(self) -> BaseLabelCategories | None:
        """Get the label categories from the dataset schema, if any.

        Searches the schema attributes for the first field whose categories
        are an instance of :class:`BaseLabelCategories` (which covers both
        :class:`LabelCategories` and :class:`HierarchicalLabelCategories`).

        Returns:
            The :class:`BaseLabelCategories` instance, or ``None`` if no
            label categories are defined in the schema.
        """
        for attr_name, attr_info in self._schema.attributes.items():
            categories = self._schema.get_categories_for_field(attr_name)
            if isinstance(categories, BaseLabelCategories):
                return categories
        return None

    def _generate_polars_schema(self) -> pl.Schema:
        """Generate a Polars schema from the dataset's field definitions."""
        schema: dict[str, pl.DataType] = {}
        for key, attr_info in self._schema.attributes.items():
            schema.update(attr_info.field.to_polars_schema(key))
        return pl.Schema(schema)

    def _expand_df_with_auxiliary_columns(self, new_df: pl.DataFrame) -> None:
        """Expand the main DataFrame with auxiliary columns from new_df that are not in the schema.

        Some fields (e.g., BBoxField) produce auxiliary columns (like canvas_size)
        that are not part of the required schema but are needed for full reconstruction.
        This method adds those columns to the main DataFrame (backfilled with nulls)
        so that vstack/extend can succeed.
        """
        for col_name in new_df.columns:
            if col_name not in self.df.columns:
                # Add a null-filled column with the same dtype to the main DataFrame
                self.df = self.df.with_columns(
                    pl.lit(None).cast(new_df[col_name].dtype).alias(col_name),
                )

    def append(self, sample: DType) -> None:
        """
        Add a new sample to the dataset.

        Args:
            sample: The sample instance to add to the dataset
        """
        if self._transforms is not None:
            raise RuntimeError("Transformed dataset is immutable.")

        series_data: dict[str, pl.Series] = {}
        for key, attr_info in self._schema.attributes.items():
            value = getattr(sample, key)
            series_data.update(attr_info.field.to_polars(key, value))

        new_row = pl.DataFrame(series_data)

        # Add any auxiliary columns from new_row that are missing in the main DataFrame
        self._expand_df_with_auxiliary_columns(new_row)

        new_row = new_row.select(self.df.columns).cast(dict(self.df.schema))  # type: ignore

        # Validate fields with categories have integers that refer to existing categories
        self._validate_fields_with_categories(df=new_row)

        # Use vstack instead of extend for object columns since extend doesn't support them
        if any(dtype == pl.Object for dtype in self.df.schema.values()):
            self.df = self.df.vstack(new_row)
        else:
            self.df.extend(new_row)

    def _collect_batch_column_values(
        self, samples: Sequence[DType]
    ) -> tuple[dict[str, list[Any]], dict[str, pl.DataType]]:
        """Collect raw Python values and dtypes per column for a batch of samples.

        Uses :meth:`Field.to_python_scalars` for fast extraction, avoiding
        per-sample ``pl.Series`` construction. Auxiliary columns that are not
        part of the required schema get their dtype inferred from a one-off
        call to :meth:`Field.to_polars` on their first occurrence.
        """
        column_raw_values: dict[str, list[Any]] = {}
        column_dtypes: dict[str, pl.DataType] = {}

        # Pre-compute schema dtypes for all known columns
        for key, attr_info in self._schema.attributes.items():
            for col_name, col_dtype in attr_info.field.to_polars_schema(key).items():
                column_dtypes[col_name] = col_dtype

        for sample in samples:
            for key, attr_info in self._schema.attributes.items():
                value = getattr(sample, key)
                scalars_map = attr_info.field.to_python_scalars(key, value)
                for col_name, scalar_val in scalars_map.items():
                    if col_name not in column_raw_values:
                        column_raw_values[col_name] = []
                        if col_name not in column_dtypes:
                            # Auxiliary column (e.g. "<bbox>_canvas_size"); infer dtype
                            # from to_polars on the first encounter.
                            series_map = attr_info.field.to_polars(key, value)
                            if col_name in series_map:
                                column_dtypes[col_name] = series_map[col_name].dtype
                    column_raw_values[col_name].append(scalar_val)

        return column_raw_values, column_dtypes

    def append_batch(self, samples: Sequence[DType]) -> None:
        """
        Add multiple samples to the dataset at once.

        Args:
            samples: A sequence of sample instances to add to the dataset

        Raises:
            RuntimeError: If the dataset has transforms applied (immutable)
            ValueError: If any sample has category values out of range

        Example:
            >>> samples = [MySample(image=img1, label=0), MySample(image=img2, label=1)]
            >>> dataset.append_batch(samples)
        """
        if not samples:
            return

        if self._transforms is not None:
            raise RuntimeError("Transformed dataset is immutable.")

        # Collect raw Python values per column, then build Series in bulk.
        # This avoids creating N single-element Series and concatenating them,
        # which is extremely slow for deeply nested types (e.g., polygons).
        column_raw_values, column_dtypes = self._collect_batch_column_values(samples)

        # Build Series in bulk, using PyArrow for nested types (much faster)
        combined_series: dict[str, pl.Series] = {
            col_name: build_series_bulk(col_name, values, column_dtypes[col_name])
            for col_name, values in column_raw_values.items()
        }

        new_rows = pl.DataFrame(combined_series)

        # Add any auxiliary columns from new_rows that are missing in the main DataFrame
        self._expand_df_with_auxiliary_columns(new_rows)

        new_rows = new_rows.select(self.df.columns).cast(dict(self.df.schema))  # type: ignore

        # Validate fields with categories have integers that refer to existing categories
        self._validate_fields_with_categories(df=new_rows)

        # Append to dataset
        if any(dtype == pl.Object for dtype in self.df.schema.values()):
            self.df = self.df.vstack(new_rows)
        else:
            self.df.extend(new_rows)

    def slice(self, offset: int, length: int | None = None) -> Dataset[DType]:
        """
        Create a new dataset that is a slice of this dataset.

        Args:
            offset: The starting index of the slice
            length: The number of samples to include in the slice
        """
        if self._transforms is None:
            slice_df = self.df.slice(offset, length)
            transforms = None
        else:
            transforms = self._transforms.slice(offset, length)
            slice_df = pl.DataFrame()

        dataset = Dataset.from_dataframe(
            slice_df,
            self._dtype,
            transforms,
        )
        dataset._dtype = self._dtype

        return dataset

    def validate_fields_with_categories(self) -> None:
        """
        Validates that each integer value in field columns with categories refers to existing categories

        Each field that requires categories should have an unsigned integer dtype, therefore checking the maximum value
        of each column is lower or equal than the number of associated categories is enough.
        """
        self._validate_fields_with_categories(df=self.df)

    def _validate_fields_with_categories(self, df: pl.DataFrame) -> None:
        fields_with_categories = self._schema.get_fields_with_required_categories()

        for field_name, categories in fields_with_categories.items():
            if df[field_name].dtype.is_object():
                continue

            # Label fields can be lists or lists of lists (in the case of multi-labels), so explode column twice.
            field_max = df.select(pl.col(field_name).explode().explode().max()).item()
            # Optional fields can be None, so we can skip the check
            if field_max is not None and len(categories) <= field_max:
                raise ValueError(
                    f"For field '{field_name}' there are '{len(categories)}' categories defined. However, the "
                    f"dataset or sample has values that exceed this number: the maximum value is {field_max}. "
                    f"Therefore some samples of this dataset do not have meaning for field '{field_name}'."
                )

    def __getitem__(self, row_idx: int) -> DType:
        """
        Retrieve a sample from the dataset by index.

        Args:
            row_idx: The index of the sample to retrieve

        Returns:
            The sample instance at the specified index
        """
        # Extract the row as a single-row DataFrame
        if self._transforms is None:
            row_df = self.df.slice(row_idx, 1)
            lazy_attributes = set()
            transforms = None
        else:
            transforms = self._transforms.slice(row_idx, 1)
            row_df = transforms.apply(transforms.get_batch_attributes())
            lazy_attributes = transforms.get_lazy_attributes()

        # Separate attributes into those available directly and those requiring lazy conversion
        direct_attributes = {}

        # Compute available columns once before the loop
        available_columns = set(row_df.columns)

        for key, attr_info in self._schema.attributes.items():
            if key not in lazy_attributes:
                # Get required columns from cache (avoids repeated to_polars_schema calls)
                required_columns = self._schema.get_required_columns(key)

                if not required_columns.issubset(available_columns):
                    # Columns are missing - check if the field is optional
                    if is_type_optional(attr_info.type):
                        # Optional field with missing columns - set to None
                        direct_attributes[key] = None
                        continue
                    # Required field with missing columns - this is an error
                    missing = required_columns - available_columns
                    raise KeyError(f"Required columns {missing} for field '{key}' not found in DataFrame")

                # This attribute is directly available
                direct_attributes[key] = attr_info.field.from_polars(key, 0, row_df, attr_info.type)

        # If there are lazy converters, create a dynamic class with descriptors
        dtype = self._dtype

        if lazy_attributes:
            direct_attributes["_transforms"] = transforms
            # attrs = {}
            # for lazy_attr in lazy_attributes:
            #    attrs[lazy_attr] = LazyDescriptor(lazy_attr, transforms)

            ## Create a new dynamic class inheriting from dtype
            # dtype = type(dtype.__name__, (dtype,), attrs)
            # dtype.__annotations__ = self._dtype.__annotations__

        return dtype(
            **direct_attributes,
        )

    def __len__(self) -> int:
        """
        Return the number of samples in the dataset.

        Returns:
            The number of samples (rows) in the dataset
        """
        return len(self.df) if self._transforms is None else len(self._transforms)

    def __iter__(self):
        """
        Return an iterator over the samples in the dataset.

        Yields:
            Sample instances from the dataset in order
        """
        for i in range(len(self)):
            yield self[i]

    def __delitem__(self, row_idx: int):
        """
        Delete a sample from the dataset at the specified index.

        Args:
            row_idx: The index of the sample to delete

        Raises:
            IndexError: If the row index is out of bounds
        """
        if self._transforms is not None:
            raise RuntimeError("Transformed dataset is immutable.")

        if row_idx < 0 or row_idx >= len(self.df):
            raise IndexError("Row index out of bounds.")

        # Create a filter to exclude the row at the specified index
        self.df = self.df.with_row_index().filter(pl.col("index") != row_idx).drop("index")

    def __setitem__(self, row_idx: int, sample: DType):
        """
        Update the dataset at the specified index with the given sample.

        Args:
            row_idx: The index to update
            sample: The sample instance to set at the specified index

        Raises:
            IndexError: If the row index is out of bounds
        """
        if self._transforms is not None:
            raise RuntimeError("Transformed dataset is immutable.")

        if row_idx < 0 or row_idx >= len(self.df):
            raise IndexError("Row index out of bounds.")

        series_data: dict[str, pl.Series] = {}
        for key, attr_info in self._schema.attributes.items():
            series_data.update(attr_info.field.to_polars(key, getattr(sample, key)))

        updated_row = pl.DataFrame(series_data).cast(dict(self.df.schema))  # type: ignore

        # Update the dataframe by replacing the row at the specified index
        self.df = self.df.with_row_index().select(
            pl.when(pl.col("index") == row_idx).then(updated_row[c]).otherwise(pl.col(c)).alias(c)
            for c in self.df.columns
        )

    def transform(
        self,
        transform_factory: Callable[[Transform], Transform],
        dtype: type[DTargetType] | None = None,
    ) -> Dataset[DTargetType]:
        transforms = self._transforms
        if transforms is None:
            transforms = IdentityTransform(self.df, self.schema)

        transforms = transform_factory(transforms)

        if dtype is None:
            return Dataset.from_dataframe(
                self.df,
                transforms.schema,
                transforms,
            )
        return Dataset.from_dataframe(
            self.df,
            dtype,
            transforms,
            schema=transforms.schema,
        )

    def convert_to_schema(
        self,
        target_dtype_or_schema: Schema | type[DTargetType],
        target_categories: dict[str, Categories] | None = None,
        direct_only: bool = False,
    ) -> Dataset[DTargetType]:
        """
        Convert this dataset to a new schema using registered converters.

        Args:
            target_dtype_or_schema: The target schema or sample type to convert to
            target_categories: Optional dictionary mapping attribute names to categories
            direct_only: If True, only apply converters where all output field types
                match (are a subset of) the input field types. Cross-field-type
                converters (e.g., BBoxField→PolygonField) are skipped. Converters
                that operate within the same field type (e.g., BBoxField→BBoxField
                for format or dtype changes) are still allowed.
                :class:`~getidata.converters.base.MediaBridgeConverter`
                subclasses (e.g., MediaPathField→ImagePathField) are always
                allowed regardless of this flag.

        Returns:
            A new Dataset instance with the converted schema
        """
        # Determine target schema
        if isinstance(target_dtype_or_schema, Schema):
            target_schema = target_dtype_or_schema
        else:
            target_schema = target_dtype_or_schema.infer_schema()

        if target_categories is not None:
            target_schema = target_schema.with_categories(target_categories)

        # Early return if schemas are already compatible
        if has_schema(self, target_dtype_or_schema):
            # Same schema but mismatching dtype.
            return Dataset.from_dataframe(
                self.df,
                target_dtype_or_schema,
            )

        # Find the optimal conversion path using A* search
        conversion_paths, inferred_categories = find_conversion_path(
            self._schema, target_schema, direct_only=direct_only
        )

        # Create a converter transform
        transforms = self._transforms
        if transforms is None:
            transforms = IdentityTransform(self.df, self.schema)

        transforms = ConverterTransform(transforms, target_schema, conversion_paths)

        remaining_transforms: Transform | None = transforms if transforms.get_lazy_attributes() else None

        # Create new dataset with converted data and inferred categories
        return Dataset.from_dataframe(
            transforms._df,
            target_dtype_or_schema,
            remaining_transforms,
            categories=inferred_categories,
        )

    def filter_by_subset(self, subset: Subset | Sequence[Subset]) -> Dataset[DType]:
        """
        Return new dataset with items from given subset(s).

        Args:
            subset: a single subset or a list/tuple of subsets to filter on

        Returns:
            A new Dataset with items of the given subset(s).
        """
        for subset_column_name, attribute_info in self.schema.attributes.items():
            if isinstance(attribute_info.field, SubsetField):
                break
        else:
            raise RuntimeError(f"Dataset does not have an attribute for 'SubsetField': schema: {self.df.schema}")

        if isinstance(subset, Sequence):
            subset_names = [s.name for s in subset]
            filtered_df = self.df.filter(self.df[subset_column_name].is_in(subset_names))
        else:
            filtered_df = self.df.filter(self.df[subset_column_name] == subset.name)

        return Dataset.from_dataframe(
            df=filtered_df,
            dtype_or_schema=self.dtype,
            schema=self.schema,
        )

    def filter_by_labels(
        self,
        labels: str | int | Sequence[str | int],
        label_field_name: str | None = None,
        update_categories: bool = False,
        keep_empty_samples: bool = False,
    ) -> Dataset[DType]:
        """
        Return a new dataset containing only items that have at least one of the given labels.

        This method accepts either label names (as strings) or label indices (as integers)
        and resolves them to their integer indices using the LabelCategories associated with
        the specified label field. It supports all LabelField configurations: single labels,
        multi-label fields, list fields, and combinations thereof.

        When ``label_field_name`` is not provided, the method automatically
        detects the LabelField in the schema. If the schema contains multiple
        LabelFields, ``label_field_name`` must be specified explicitly.

        Args:
            labels: A single label name (str), label index (int), or a sequence of label names
                and/or indices to filter by. Label indices must be within the valid range
                [0, num_categories).
            label_field_name: The name of the attribute on the Sample that uses a
                LabelField. If ``None``, it is inferred automatically when the
                schema contains exactly one LabelField.
            update_categories: If ``True``, the returned dataset's LabelCategories will
                contain only the filtered labels (with indices remapped to 0, 1, 2, ...).
                If ``False`` (default), the original LabelCategories are preserved and
                label indices remain unchanged.
            keep_empty_samples: If ``True``, all samples are kept in the dataset even if
                they have no matching labels. Non-matching labels and their corresponding
                annotations are removed, but the sample's media data (e.g., images) is
                preserved. If ``False`` (default), samples without any matching labels
                are removed from the dataset entirely.

        Returns:
            A new Dataset containing items filtered by the specified labels.
            If ``keep_empty_samples=False``, only items with at least one matching label
            are included. If ``keep_empty_samples=True``, all items are included but with
            non-matching labels and annotations stripped away.

        Raises:
            KeyError: If ``label_field_name`` is not found in the schema.
            TypeError: If the specified field is not a LabelField, or if a label is
                neither a string nor an integer.
            RuntimeError: If ``label_field_name`` is ``None`` and the schema
                contains zero or more than one LabelField.
            ValueError: If the field does not have LabelCategories attached, if any
                of the provided label names are not found in the categories, or if
                any label index is out of range.

        Example:
            ```python
            # Auto-detect (schema has exactly one LabelField)
            filtered = dataset.filter_by_labels(["cat", "dog"])

            # Using label indices
            filtered = dataset.filter_by_labels([0, 1])

            # Explicit field name (required when multiple LabelFields exist)
            filtered = dataset.filter_by_labels(["cat", "dog"], label_field_name="labels")

            # Update categories to only contain filtered labels (indices remapped)
            filtered = dataset.filter_by_labels(["cat", "dog"], update_categories=True)

            # Keep all samples but strip non-matching labels and annotations
            filtered = dataset.filter_by_labels(["cat"], keep_empty_samples=True)
            ```
        """

        label_field_name = resolve_label_field_name(self.schema, label_field_name)
        attr_info = self.schema.attributes[label_field_name]
        label_field_instance: LabelField = attr_info.field  # type: ignore[assignment]

        # Validate LabelCategories
        categories = validate_label_categories(attr_info.categories, label_field_name)

        if isinstance(labels, (str, int)):
            labels = [labels]

        if len(labels) == 0:
            raise ValueError("No labels provided to filter by. Please provide at least one label name or index.")

        label_indices = resolve_label_indices(labels, categories, label_field_name)
        filtered_df = filter_df_by_label_indices(
            self.df,
            label_field_name,
            label_field_instance,
            label_indices,
            schema=self.schema,
            keep_empty_samples=keep_empty_samples,
        )

        if update_categories:
            # For hierarchical categories, automatically include all ancestor labels
            if isinstance(categories, HierarchicalLabelCategories):
                label_indices = expand_indices_with_ancestors(categories, label_indices)

            # Sort indices to maintain a consistent order in the new categories
            sorted_indices = sorted(set(label_indices))

            # Create mapping from old indices to new indices (0, 1, 2, ...)
            old_to_new_index_map = {old_idx: new_idx for new_idx, old_idx in enumerate(sorted_indices)}

            # Remap label indices in the DataFrame
            filtered_df = remap_label_indices(filtered_df, label_field_name, label_field_instance, old_to_new_index_map)

            # Create new categories based on the original category type
            new_categories = create_filtered_categories(categories, sorted_indices)

            # Create a new schema with the updated categories
            new_schema = self.schema.with_categories({label_field_name: new_categories})

            return Dataset.from_dataframe(
                df=filtered_df,
                dtype_or_schema=self.dtype,
                schema=new_schema,
            )

        return Dataset.from_dataframe(
            df=filtered_df,
            dtype_or_schema=self.dtype,
            schema=self.schema,
        )

    def append_dataset(self, dataset: Dataset, direct_only: bool = False) -> None:
        """
        Append another dataset to this dataset in place.

        Args:
            dataset: The dataset to append
            direct_only: If True, only apply converters where all output field types
                match (are a subset of) the input field types. Cross-field-type
                converters (e.g., BBoxField→PolygonField) are skipped.
                :class:`~getidata.converters.base.MediaBridgeConverter`
                subclasses are always allowed regardless of this flag.
        """
        converted_dataset = dataset.convert_to_schema(target_dtype_or_schema=self.schema, direct_only=direct_only)
        self.df = self.df.vstack(converted_dataset.df)


def convert_sample_to_schema(
    sample: Sample,
    source_schema: Schema,
    target_dtype_or_schema: Schema | type[DTargetType],
    direct_only: bool = False,
) -> DTargetType:
    """
    Convert a sample to a new schema using registered converters.

    This function creates a temporary dataset, converts it, and returns the
    converted sample. It's useful for one-off conversions without creating
    a full dataset.

    Args:
        sample: The sample instance to convert
        source_schema: The source schema of the sample
        target_dtype_or_schema: The target schema to convert to
        direct_only: If True, only apply converters where all output field types
            match (are a subset of) the input field types.
            :class:`~getidata.converters.base.MediaBridgeConverter`
            subclasses are always allowed regardless of this flag.

    Returns:
        A new Sample instance with the converted schema
    """
    # Create temporary dataset with single sample
    temp_dataset = Dataset(source_schema)
    temp_dataset.append(sample)

    # Convert the dataset
    converted_dataset = temp_dataset.convert_to_schema(target_dtype_or_schema, direct_only=direct_only)

    # Return the converted sample
    return converted_dataset[0]


def has_schema(
    dataset: Dataset[Any], target_dtype_or_schema: Schema | type[DTargetType]
) -> TypeGuard[Dataset[DTargetType]]:
    """
    Check if a dataset has the specified schema.

    This function performs schema compatibility checking and serves as a
    type guard for type narrowing.

    Args:
        dataset: The dataset to check
        target_dtype_or_schema: The target schema or sample type to check against

    Returns:
        True if the dataset has the specified schema, False otherwise
    """
    if isinstance(target_dtype_or_schema, Schema):
        target_schema = target_dtype_or_schema
    else:
        # For sample type input, infer the schema
        target_schema = target_dtype_or_schema.infer_schema()

    return dataset.schema == target_schema

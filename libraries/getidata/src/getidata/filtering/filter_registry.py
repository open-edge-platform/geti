"""
Registry system for filtering operations on datasets.

This module provides the foundation for filtering operations, including filter
registration and configuration management.
"""

import copy
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, NamedTuple

import polars as pl

from getidata.schema import AttributeSpec, Field, Schema
from getidata.transform import Transform


class Filter(ABC):
    """Base class for all filters.

    All filter implementations should inherit from this class and implement
    the filter method. Each filter is responsible for determining which rows
    should be kept in the dataset based on specific criteria.
    """

    def __init__(self, field_spec: AttributeSpec[Any]):
        self.field_spec = field_spec

    @abstractmethod
    def filter(self, df: pl.DataFrame) -> pl.Expr:
        """Filter the dataframe and return a boolean mask of rows to keep.

        Args:
            df: Input dataframe to filter

        Returns:
            Boolean expression indicating which rows to keep (True) or remove (False)
        """


class FilterRegistry:
    """Registry for filter implementations.

    This class provides a central registry for all filter implementations, mapping
    field types to their corresponding filters. It uses a decorator pattern for
    registration, making it easy to add new filters for different field types.

    Example:
        ```python
        @FilterRegistry.register(BBoxField)
        class EmptyBBoxFilter(Filter):
            def filter(self, df):
                # Implementation for filtering empty bboxes
                ...

        # Later, get filter for field type
        filter_cls = FilterRegistry.get_filter(BBoxField)
        ```
    """

    _filters: dict[type[Field], type[Filter]] = {}

    @classmethod
    def register(cls, field_type: type[Field]):
        """Decorator to register a filter implementation for a field type.

        Args:
            field_type: The field type this filter handles

        Returns:
            Decorator function that registers the filter class
        """

        def decorator(filter_cls: type[Filter]) -> type[Filter]:
            cls._filters[field_type] = filter_cls
            return filter_cls

        return decorator

    @classmethod
    def get_filter(cls, field_type: type[Field]) -> type[Filter] | None:
        """Get the filter implementation for a field type.

        Args:
            field_type: The field type to get the filter for

        Returns:
            The filter class for the field type, or None if no filter is registered
        """
        return cls._filters.get(field_type)


class FilterEntry(NamedTuple):
    """Entry for a filter instance and its associated field.

    Attributes:
        field_name: Name of the field this filter operates on
        filter: The filter instance
    """

    field_name: str
    filter: Filter


@dataclass
class FilteringPlan:
    """Stores the complete plan for executing filtering operations.

    This class organizes all the components needed for filtering a dataset:
    - List of filters to apply
    - List of attributes used by the filters

    The plan is created by create_filtering_plan() and used by the filtering transform
    to execute the filtering operation.

    Attributes:
        filters: List of filter entries to apply to the dataset
    """

    filters: list[FilterEntry]
    attributes: list[str]


def create_filtering_plan(schema: Schema) -> FilteringPlan:
    """Create a plan for filtering operations on a dataset.

    This function analyzes the schema, identifies relevant fields, and creates
    a structured plan for how to filter the dataset.

    Args:
        schema: The input dataset's schema, defining all fields.

    Returns:
        A FilteringPlan containing all information needed for the filtering operation.

    Example:
        ```python
        schema = Schema(...)  # Your dataset schema
        plan = create_filtering_plan(schema)
        ```
    """
    # Create filters for each field type
    filters: list[FilterEntry] = []
    attributes: list[str] = []

    for field_name, field_info in schema.attributes.items():
        filter_cls = FilterRegistry.get_filter(type(field_info.field))
        if filter_cls is not None:
            filter_instance = filter_cls(AttributeSpec(field_name, field_info.field))
            filters.append(FilterEntry(field_name, filter_instance))
            attributes.append(field_name)

    return FilteringPlan(
        filters=filters,
        attributes=attributes,
    )


def _compute_filter_mask(
    df: pl.DataFrame,
    plan: FilteringPlan,
) -> pl.Expr:
    """Compute the boolean mask for filtering operations based on the filtering plan.

    This function computes which rows should be kept in the dataset by applying all
    filters in sequence and combining their results.

    Args:
        df: Source DataFrame containing the data to filter
        plan: The FilteringPlan containing all filtering specifications

    Returns:
        Boolean expression indicating which rows to keep (True) or remove (False)
    """
    keep_mask = None

    # Apply filters in sequence
    for filter_entry in plan.filters:
        # Combine with AND operation - rows must pass all filters
        entry_filter = filter_entry.filter.filter(df)
        if keep_mask is None:
            keep_mask = entry_filter
        else:
            keep_mask = keep_mask & entry_filter

    if keep_mask is None:
        keep_mask = pl.Series([True] * len(df))

    return keep_mask


class FilteringTransform(Transform):
    """Transform that implements filtering operations on a dataset.

    The transform maintains state about which fields have been processed and
    caches intermediate results to avoid redundant computation.

    Example:
        ```python
        # Create filtering transform
        transform = create_filtering_transform()

        # Apply to dataset
        filtered_dataset = dataset.transform(transform)
        ```
    """

    def __init__(self, parent: Transform, filtering_plan: FilteringPlan):
        """Initialize filtering transform.

        Args:
            parent: The parent transform providing input data
            filtering_plan: The plan specifying how to filter the data
        """
        super().__init__(parent.schema)
        self._lazy_outputs = parent.get_lazy_attributes().copy()
        self._lazy_outputs -= set(filtering_plan.attributes)

        self._parent = parent
        self._filtering_plan = filtering_plan
        self._keep_mask = None

        # The length will be initialized during the first apply
        self._length = 0

        self.apply(filtering_plan.attributes)

    def apply(self, fields: Sequence[str]) -> pl.DataFrame:
        """Apply filtering to specified fields.

        Args:
            fields: List of field names to process

        Returns:
            DataFrame with filtered data
        """
        if len(self._filtering_plan.filters) == 0:
            # No filters to apply, just pass through
            output_df = self._parent.apply(list(fields))
            self._length = len(output_df)
            return output_df

        fields_set = set(fields)
        fields_set.update(self._filtering_plan.attributes)

        input_df = self._parent.apply(list(fields_set))

        if self._keep_mask is None:
            # First time applying filters
            self._keep_mask = input_df.select(_compute_filter_mask(input_df, self._filtering_plan).alias("mask"))[
                "mask"
            ]

        output_df = input_df.filter(self._keep_mask)
        self._length = len(output_df)

        return output_df

    def get_lazy_attributes(self) -> set[str]:
        """Get the set of attributes that can be evaluated lazily.

        Returns:
            Set of field names that support lazy evaluation
        """
        return self._lazy_outputs

    def slice(self, offset: int, length: int | None = None) -> "Transform":
        """Create a new transform representing a slice of this one.

        Args:
            offset: Start index of the slice
            length: Optional length of the slice. If None, includes all remaining items.

        Returns:
            A new FilteringTransform instance representing the slice
        """
        if len(self._filtering_plan.filters) == 0:
            parent_offset = offset
            parent_length = length
        else:
            # Find parent offset and length
            parent_indexes = pl.DataFrame({"keep": self._keep_mask}).with_row_index().filter(pl.col("keep"))
            parent_offset = parent_indexes[offset, "index"]
            parent_length = (
                parent_indexes[offset + length - 1, "index"] - parent_offset + 1 if length is not None else None
            )

        instance = copy.copy(self)
        instance._parent = self._parent.slice(parent_offset, parent_length)
        instance._keep_mask = (
            self._keep_mask.slice(parent_offset, parent_length) if self._keep_mask is not None else None
        )
        return instance

    def __len__(self):
        """Get the length of the filtered dataset.

        Returns:
            Number of items in the filtered dataset
        """
        return self._length


class _FilteringTransformFactory:
    """Module-level callable that builds a :class:`FilteringTransform` from a parent transform.

    Defined at module scope (instead of a local ``factory`` closure) so instances
    pickle by reference. This allows the returned transform to be safely passed
    across process boundaries (e.g. multiprocessing, ``cloudpickle``-free paths).
    """

    __slots__ = ()

    def __call__(self, parent: Transform) -> "FilteringTransform":
        plan = create_filtering_plan(parent.schema)
        return FilteringTransform(parent, plan)


def create_filtering_transform() -> Callable[[Transform], FilteringTransform]:
    """Create a transform factory for filtering operations.

    This is the main entry point for creating a filtering transform. It returns
    a picklable callable that will create FilteringTransform instances when needed.
    This pattern allows the transform to be used in dataset pipelines.

    Returns:
        A picklable callable that creates FilteringTransform instances.

    Example:
        ```python
        # Create the transform factory
        filtering_transform = create_filtering_transform()

        # Use in a dataset pipeline
        dataset = dataset.transform(filtering_transform)
        ```
    """
    return _FilteringTransformFactory()

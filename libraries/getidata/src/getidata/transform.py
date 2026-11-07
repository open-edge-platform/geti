# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
from abc import abstractmethod
from collections.abc import Sequence

import polars as pl

from .polars_utils import prepare_dataframe_for_pickle, restore_dataframe_from_pickle
from .schema import Schema


class Transform:
    """Base class for all dataframe transformations.

    A Transform represents an operation that can be applied to a dataframe,
    potentially modifying its structure and content.

    This class is not meant to be used directly. It is typically used behind the scene
    by the Dataset class.

    Transforms may support lazy evaluation of certain fields. The list of readily
    available fields is available through get_batch_attributes() while the list of lazy
    fields is available through get_lazy_attributes(). From a behavioral perspective,
    there is no difference between the two types of attributes, but it is recommended
    to avoid fetching lazy attributes until needed as they often require expensive
    operations (such as image loading)

    Transforms can be chained through by passing the parent transform to the
    constructor of the child transform. The only transform which no parent is the
    IdentityTransform which acts as the root of the transform pipeline.


    Attributes:
        schema: The schema describing the structure of the transformed data
    """

    def __init__(self, schema: Schema):
        """Initialize the transform with its output schema.

        Args:
            schema: Schema describing the structure of the transformed data
        """
        self._schema = schema

    @abstractmethod
    def apply(self, fields: Sequence[str]) -> pl.DataFrame:
        """Apply the transform to selected fields.

        This method performs the actual transformation on the requested fields.
        It supports lazy evaluation by only processing the fields that are
        actually needed.

        Note that the returned dataframe may contain columns for any available fields
        specified in the schema even if not explicitly requested.

        Args:
            fields: Names of the fields to process in this operation

        Returns:
            DataFrame containing the transformed data for the requested fields

        Example:
            ```python
            # Process just image and annotation fields
            result = transform.apply(['image', 'annotations'])
            ```
        """
        raise NotImplementedError

    @property
    def schema(self) -> Schema:
        """Get the schema describing the transformed data structure.

        Returns:
            Schema object describing all fields in the transformed data
        """
        return self._schema

    def get_batch_attributes(self) -> set[str]:
        """Get the set of attributes that should be processed in batch.

        This method identifies which attributes are processed immediately upon the creation
        of the transform and are readily available without additional computation.

        Returns:
            Set of attribute names that are readily available

        Example:
            ```python
            # Check which attributes are readily available
            batch_attrs = transform.get_batch_attributes()

            # Retrieve them
            df = transform.apply(list(batch_attrs))
            ```
        """
        attributes = set(self.schema.attributes.keys())
        attributes -= self.get_lazy_attributes()
        return attributes

    @abstractmethod
    def get_lazy_attributes(self) -> set[str]:
        """Get the set of attributes that can be processed lazily.

        Lazy attributes are require additional computation
        and can be evaluated on-demand. This helps optimize memory usage and
        processing time.

        Returns:
            Set of attribute names that can be processed lazily

        Example:
            ```python
            # Check which attributes are lazy
            lazy_attrs = transform.get_lazy_attributes()

            # Process them individually as needed
            for attr in lazy_attrs:
                data = transform.apply([attr])
            ```
        """
        raise NotImplementedError

    @abstractmethod
    def slice(self, offset: int, length: int | None = None) -> "Transform":
        """Create a new transform representing a slice of this one.

        This method enables working with subsets of the data while preserving
        the transformation logic. It's useful for retrieving lazy attributes
        for a given slice (or even a single item) without processing the entire dataset.

        Args:
            offset: Starting index for the slice
            length: Number of items to include in the slice, or None for
                all remaining items

        Returns:
            A new Transform instance representing the requested slice

        Example:
            ```python
            # Create transform for first 100 items
            batch = transform.slice(0, 100)

            # Process the batch
            result = batch.apply(['image', 'bbox'])
            ```
        """
        raise NotImplementedError

    @abstractmethod
    def __len__(self):
        """Get the number of items in this transform.

        Returns:
            The total number of items that this transform will produce
        """
        raise NotImplementedError


class IdentityTransform(Transform):
    """A transform that returns its input unchanged.

    This transform simply passes through its input data without modification.
    It's useful as:
    - A base case for transform pipelines
    - A wrapper to adapt raw DataFrames to the Transform interface
    - A testing/debugging tool

    Example:
        ```python
        # Create identity transform from DataFrame
        transform = IdentityTransform(df, schema)

        # Use like any other transform
        result = transform.apply(['field1', 'field2'])
        ```
    """

    def __init__(self, df: pl.DataFrame, schema: Schema):
        """Initialize identity transform.

        Args:
            df: The input DataFrame to wrap
            schema: Schema describing the DataFrame structure
        """
        super().__init__(schema)
        self._df = df

    def __getstate__(self) -> dict:
        """Prepare the transform for pickling.

        Polars DataFrames with Object columns cannot be serialized using Polars' default
        serialization. This method extracts Object columns as Python lists before pickling.
        """
        state = self.__dict__.copy()
        return prepare_dataframe_for_pickle(self._df, "_df", state)

    def __setstate__(self, state: dict) -> None:
        """Restore the transform after unpickling.

        Reconstructs Object columns from the Python lists stored during pickling.
        """
        state["_df"] = restore_dataframe_from_pickle(state, "_df")
        self.__dict__.update(state)

    def apply(self, _: Sequence[str]) -> pl.DataFrame:
        """Return the wrapped DataFrame unchanged.

        Args:
            _: Ignored field list - all fields are always returned

        Returns:
            The complete wrapped DataFrame
        """
        return self._df

    def get_lazy_attributes(self) -> set[str]:
        """Get lazy attributes - none for identity transform.

        The identity transform has no lazy attributes because it simply
        returns its input DataFrame directly.

        Returns:
            Empty set, indicating no lazy attributes
        """
        return set()

    def slice(self, offset: int, length: int | None = None) -> "Transform":
        """Create a sliced view of this transform.

        Args:
            offset: Starting index for the slice
            length: Number of items to include, or None for all remaining

        Returns:
            New IdentityTransform wrapping the sliced DataFrame
        """
        return IdentityTransform(self._df.slice(offset, length), self.schema)

    def __len__(self):
        """Get number of rows in the wrapped DataFrame.

        Returns:
            Length of the wrapped DataFrame
        """
        return len(self._df)

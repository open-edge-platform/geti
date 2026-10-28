# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import polars as pl

from getidata.fields.datasets import Subset, subset_field


class SubsetFieldFromPolarsTest:
    """Tests for SubsetField.from_polars with valid and unknown subset values."""

    def _make_df(self, value):
        """Create a single-row DataFrame with a categorical 'subset' column."""
        return pl.DataFrame({"subset": [value]}).cast({"subset": pl.Categorical})

    def test_valid_subset_value(self):
        field = subset_field()
        df = self._make_df("TRAINING")
        result = field.from_polars("subset", 0, df, Subset)
        assert result == Subset.TRAINING

    def test_valid_subset_value_validation(self):
        field = subset_field()
        df = self._make_df("VALIDATION")
        result = field.from_polars("subset", 0, df, Subset)
        assert result == Subset.VALIDATION

    def test_unknown_subset_falls_back_to_unassigned(self):
        field = subset_field()
        df = self._make_df("default")
        result = field.from_polars("subset", 0, df, Subset)
        assert result == Subset.UNASSIGNED

    def test_unknown_subset_arbitrary_string_falls_back_to_unassigned(self):
        field = subset_field()
        df = self._make_df("some_unknown_subset")
        result = field.from_polars("subset", 0, df, Subset)
        assert result == Subset.UNASSIGNED

    def test_none_subset_returns_none(self):
        field = subset_field()
        df = pl.DataFrame({"subset": [None]}).cast({"subset": pl.Categorical})
        result = field.from_polars("subset", 0, df, Subset)
        assert result is None

    def test_optional_subset_unknown_falls_back_to_unassigned(self):
        field = subset_field()
        df = self._make_df("default")
        result = field.from_polars("subset", 0, df, Subset | None)
        assert result == Subset.UNASSIGNED

    def test_optional_subset_valid_value(self):
        field = subset_field()
        df = self._make_df("TESTING")
        result = field.from_polars("subset", 0, df, Subset | None)
        assert result == Subset.TESTING

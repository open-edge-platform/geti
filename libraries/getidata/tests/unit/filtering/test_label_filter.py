# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import polars as pl

from getidata.filtering.label_filter import _filter_associated_fields


def test_filter_associated_fields_null_mask_does_not_raise():
    """_filter_associated_fields must not crash when the mask is null.

    Regression test: when the labels column is null for a row, the boolean
    mask expression derived from it also evaluates to null.  Before the fix
    the inner ``filter_by_mask`` only guarded against a null *field* value
    but not a null *mask*, causing
    ``TypeError: 'NoneType' object is not iterable``.
    """
    df = pl.DataFrame(
        {
            # Row 0: two annotations, labels [0, 1]
            # Row 1: non-null bboxes but null labels  →  mask will be null
            # Row 2: one annotation, label [1]
            "labels": [[0, 1], None, [1]],
            "bboxes": [
                [[1.0, 2.0, 3.0, 4.0], [5.0, 6.0, 7.0, 8.0]],
                [[9.0, 10.0, 11.0, 12.0]],
                [[13.0, 14.0, 15.0, 16.0]],
            ],
        },
        schema={
            "labels": pl.List(pl.UInt32()),
            "bboxes": pl.List(pl.Array(pl.Float32(), 4)),
        },
    )

    # Mask: per-element boolean derived from labels — null when labels is null
    keep_mask_expr = pl.col("labels").list.eval(pl.element().cast(pl.Int64).is_in([0]))

    exprs = _filter_associated_fields(df, keep_mask_expr, associated_fields=["bboxes"])
    assert len(exprs) == 1

    # This .with_columns() call is where the original TypeError was raised
    result = df.with_columns(exprs)

    # Row 0: only label-index 0 matches → keep first bbox only
    assert result["bboxes"][0].to_list() == [[1.0, 2.0, 3.0, 4.0]]
    # Row 1: mask is null → returns None
    assert result["bboxes"][1] is None
    # Row 2: label-index 1 does not match [0] → empty list
    assert result["bboxes"][2].to_list() == []

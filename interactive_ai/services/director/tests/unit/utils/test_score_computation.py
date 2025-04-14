# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import numpy as np
import pytest

from active_learning.utils import reduce_dict_values


@pytest.fixture
def fxt_sample_dict(fxt_media_identifier_factory):
    yield {
        fxt_media_identifier_factory(1): [0.1, 0.5, 0.9],
        fxt_media_identifier_factory(2): [0.4, 0.8],
        fxt_media_identifier_factory(3): [0.3],
        fxt_media_identifier_factory(4): [],
    }


@pytest.fixture
def fxt_sample_dict_reduced_min(fxt_sample_dict):
    yield {key: min(values, default=1.0) for key, values in fxt_sample_dict.items()}


@pytest.fixture
def fxt_sample_dict_reduced_max(fxt_sample_dict):
    yield {key: max(values, default=1.0) for key, values in fxt_sample_dict.items()}


@pytest.fixture
def fxt_sample_dict_reduced_avg(fxt_sample_dict):
    yield {key: sum(values) / len(values) if values else 1.0 for key, values in fxt_sample_dict.items()}


class TestScoreComputationUtils:
    @pytest.mark.parametrize(
        "reduce_fn, lazyfxt_expected_out_dict",
        [
            (np.nanmin, "fxt_sample_dict_reduced_min"),
            (np.nanmax, "fxt_sample_dict_reduced_max"),
            (np.nanmean, "fxt_sample_dict_reduced_avg"),
        ],
        ids=["min", "max", "avg"],
    )
    def test_reduce_dict_values(self, request, fxt_sample_dict, reduce_fn, lazyfxt_expected_out_dict) -> None:
        expected_out_dict = request.getfixturevalue(lazyfxt_expected_out_dict)

        reduced_dict = reduce_dict_values(
            input_dict=fxt_sample_dict,
            reduce_fn=reduce_fn,
        )

        assert reduced_dict == expected_out_dict

# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

import pytest

from communication.exceptions import InvalidFilterException
from usecases.dataset_filter import DatasetFilter, MediaScoreFilterField


class TestDatasetFilter:
    def test_media_dataset_filter(
        self,
        fxt_dataset_filter_dict,
        fxt_dataset_filter_match_dict,
    ) -> None:
        """
        Tests successfully creating a dataset filter object from a correct dictionary,
        tests it produces the correct amount of unique fields and tests the generated
        matching query.
        """
        dataset_filter = DatasetFilter.from_dict(query=fxt_dataset_filter_dict, limit=100)
        assert len(dataset_filter.unique_fields()) == 2
        assert dataset_filter.generate_match_query() == fxt_dataset_filter_match_dict

    def test_media_score_dataset_filter(
        self,
        fxt_valid_media_score_query,
        fxt_media_score_match_query,
    ) -> None:
        """
        Tests successfully creating a dataset filter object from a correct dictionary,
        tests it produces the correct amount of unique fields and tests the generated
        matching query.
        """
        dataset_filter = DatasetFilter.from_dict(
            query=fxt_valid_media_score_query,
            sort_by=MediaScoreFilterField.SCORE,
            limit=100,
        )
        assert len(dataset_filter.unique_fields()) == 2
        assert dataset_filter.generate_match_query() == fxt_media_score_match_query

    def test_broken_dataset_filter(self, fxt_broken_dataset_filter) -> None:
        """
        Tests that a broken dataset filter raises an exception
        """
        with pytest.raises(InvalidFilterException):
            DatasetFilter.from_dict(query=fxt_broken_dataset_filter, limit=100)

    def test_in_operator_without_sequence_value(self, fxt_broken_dataset_filter_in_no_sequence):
        """
        Tests that a broken dataset filter raises an exception
        """
        with pytest.raises(InvalidFilterException) as error:
            DatasetFilter.from_dict(query=fxt_broken_dataset_filter_in_no_sequence, limit=100)

        assert (
            error.value.message
            == "Expected a sequence for operator '$in', but got a single value instead: 'ANNOTATED'."
        )

    def test_broken_media_score_query(self, fxt_invalid_media_score_query) -> None:
        """
        Tests that a broken media score query raises an exception
        """
        with pytest.raises(InvalidFilterException):
            DatasetFilter.from_dict(
                query=fxt_invalid_media_score_query,
                sort_by=MediaScoreFilterField.SCORE,
                limit=100,
            )

    def test_too_large_int_dataset_filter(self, fxt_too_large_int_dataset_filter) -> None:
        """
        Tests that a filter with an integer value larger than 64 bits raises an exception
        """
        with pytest.raises(InvalidFilterException):
            DatasetFilter.from_dict(query=fxt_too_large_int_dataset_filter, limit=100)

    def test_contains_filter(self, fxt_contains_filter, fxt_contains_query) -> None:
        """
        Tests that a filter with a regex is generated correctly.
        """
        regex_filter = DatasetFilter.from_dict(query=fxt_contains_filter, limit=100)
        assert fxt_contains_query == regex_filter.generate_match_query()

    def test_0_1_value_float(self) -> None:
        """
        Verifies that a float filter with value 0 or 1 doesn't throw an error. This
        is checked because it is seen as an integer value but should not give an error.
        """
        float_filter = {
            "condition": "and",
            "rules": [
                {
                    "field": "SHAPE_AREA_PERCENTAGE",
                    "operator": "greater",
                    "value": 0,
                },
            ],
        }

        DatasetFilter.from_dict(query=float_filter, limit=100)
        float_filter["rules"][0]["value"] = 1  # type: ignore
        DatasetFilter.from_dict(query=float_filter, limit=100)

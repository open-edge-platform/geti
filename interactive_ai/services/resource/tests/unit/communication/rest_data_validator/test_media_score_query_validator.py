# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import pytest

from communication.exceptions import InvalidFilterException
from communication.rest_data_validator import MediaScoreQueryValidator


class TestMediaScoreQueryRestValidator:
    @pytest.mark.parametrize(
        "valid_media_score_query",
        [
            "fxt_valid_media_score_query",
            "fxt_valid_single_media_score_query",
        ],
        ids=[
            "2 valid rules",
            "1 valid rule",
        ],
    )
    def test_validate_valid_query(self, request, valid_media_score_query):
        query = request.getfixturevalue(valid_media_score_query)
        validator = MediaScoreQueryValidator()
        validator.validate_media_score_query(query)

    @pytest.mark.parametrize(
        "invalid_media_score_query",
        [
            "fxt_too_many_rules_media_score_query",
            "fxt_unsupported_fields_media_score_query",
            "fxt_nested_media_score_query",
        ],
        ids=[
            "More than 2 rules",
            "Unsupported fields",
            "Nested query",
        ],
    )
    def test_validate_invalid_query(self, request, invalid_media_score_query):
        query = request.getfixturevalue(invalid_media_score_query)
        with pytest.raises(InvalidFilterException):
            MediaScoreQueryValidator().validate_media_score_query(query)

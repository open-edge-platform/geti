# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from utils.enums import CreditSystemTimeBoundaries
from utils.validation import is_whitespace_or_empty_string, validate_timestamp


@pytest.mark.parametrize(
    "timestamp, name",
    [
        (CreditSystemTimeBoundaries.START.value - 1, "test_timestamp"),
        (CreditSystemTimeBoundaries.END.value + 1, "test_timestamp"),
        (None, "test_timestamp"),
    ],
)
def test_validate_timestamp_raises_value_error(timestamp, name):
    with pytest.raises(ValueError) as exc_info:
        validate_timestamp(timestamp, name)
    assert "must represent a date" in str(exc_info.value) or "has to be integer" in str(exc_info.value)


@pytest.mark.parametrize(
    "timestamp, name",
    [
        ((CreditSystemTimeBoundaries.START.value + CreditSystemTimeBoundaries.END.value) // 2, "test_timestamp"),
    ],
)
def test_validate_timestamp_passes(timestamp, name):
    try:
        validate_timestamp(timestamp, name)
    except ValueError:
        pytest.fail(f"validate_timestamp raised ValueError unexpectedly for timestamp {timestamp}")


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("", True),
        (" ", True),
        ("\t\n\r", True),
        ("  text  ", False),
        ("text", False),
        ("123", False),
    ],
)
def test_is_whitespace_or_empty_string(input_str, expected):
    assert is_whitespace_or_empty_string(input_str) == expected

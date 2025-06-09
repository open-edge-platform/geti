# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import pytest

from service.utils import delete_none_from_dict, merge_deep_dict


class TestUtils:
    @pytest.mark.parametrize(
        "d, expected",
        [
            # Empty dict
            ({}, {}),
            # Dict with no None values
            ({"a": 1, "b": "test"}, {"a": 1, "b": "test"}),
            # Dict with None values
            ({"a": 1, "b": None, "c": "test"}, {"a": 1, "c": "test"}),
            # Dict with nested dict containing None values
            ({"a": 1, "b": {"x": None, "y": 2}}, {"a": 1, "b": {"y": 2}}),
            # Dict with list containing dicts with None values
            ({"a": 1, "b": [{"x": None, "y": 2}, {"z": 3}]}, {"a": 1, "b": [{"y": 2}, {"z": 3}]}),
            # Complex nested scenario
            (
                {"a": 1, "b": None, "c": {"d": None, "e": {"f": None, "g": 2}, "h": [{"i": None, "j": 3}]}},
                {"a": 1, "c": {"e": {"g": 2}, "h": [{"j": 3}]}},
            ),
        ],
    )
    def test_delete_none_from_dict(self, d, expected) -> None:
        result = delete_none_from_dict(d)
        assert result == expected
        # Ensure the function modifies the dict in-place
        assert result is d

    @pytest.mark.parametrize(
        "a, b, expected",
        [
            # Empty dicts
            ({}, {}, {}),
            # Empty target dict
            ({}, {"x": 1}, {"x": 1}),
            # Empty source dict
            ({"x": 1}, {}, {"x": 1}),
            # Non-overlapping keys
            ({"x": 1}, {"y": 2}, {"x": 1, "y": 2}),
            # Overlapping keys (non-dict values)
            ({"x": 1}, {"x": 2}, {"x": 2}),
            # Simple nested dict
            ({"x": 1, "y": {"a": 2}}, {"y": {"b": 3}, "z": 4}, {"x": 1, "y": {"a": 2, "b": 3}, "z": 4}),
            # Complex nested scenario
            (
                {"a": 1, "b": {"c": 2, "d": {"e": 3}}},
                {"b": {"d": {"f": 4}, "g": 5}},
                {"a": 1, "b": {"c": 2, "d": {"e": 3, "f": 4}, "g": 5}},
            ),
            # Overwrite dict with non-dict
            ({"a": {"b": 1}}, {"a": 2}, {"a": 2}),
            # Overwrite non-dict with dict
            ({"a": 1}, {"a": {"b": 2}}, {"a": {"b": 2}}),
        ],
    )
    def test_merge_deep_dict(self, a, b, expected) -> None:
        result = merge_deep_dict(a, b)
        assert result == expected
        # Ensure the function modifies the first dict in-place
        assert result is a

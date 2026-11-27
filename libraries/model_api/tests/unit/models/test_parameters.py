# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock

import pytest
from model_api.models.parameters import ParameterDescriptor, ParameterRegistry, ParameterView


def test_merge_empty():
    result = ParameterRegistry.merge()
    assert result == {}


def test_merge_single():
    result = ParameterRegistry.merge(ParameterRegistry.CONFIDENCE_THRESHOLD)
    assert "confidence_threshold" in result


def test_merge_multiple():
    result = ParameterRegistry.merge(
        ParameterRegistry.CONFIDENCE_THRESHOLD,
        ParameterRegistry.LABELS,
    )
    assert "confidence_threshold" in result
    assert "labels" in result
    assert "path_to_labels" in result


def test_merge_override():
    g1 = {"key": "value1"}
    g2 = {"key": "value2"}
    result = ParameterRegistry.merge(g1, g2)
    assert result["key"] == "value2"


def test_parameter_groups_defined():
    assert len(ParameterRegistry.CONFIDENCE_THRESHOLD) > 0
    assert len(ParameterRegistry.LABELS) > 0
    assert len(ParameterRegistry.IMAGE_PREPROCESSING) > 0
    assert len(ParameterRegistry.NMS) > 0
    assert len(ParameterRegistry.ANOMALY) > 0


def test_descriptor_get_none_obj():
    desc = ParameterDescriptor()
    # Accessing from class (obj=None) should return the descriptor itself
    result = desc.__get__(None, type)
    assert result is desc


def test_descriptor_get_with_obj():
    desc = ParameterDescriptor()
    mock_model = MagicMock()
    result = desc.__get__(mock_model, type(mock_model))
    assert isinstance(result, ParameterView)


def test_parameter_view_getattr_raises():
    mock_model = MagicMock()
    mock_model.get_param.side_effect = KeyError("not found")
    view = ParameterView(mock_model)
    with pytest.raises(AttributeError, match="not found"):
        _ = view.nonexistent_param


def test_parameter_view_dir():
    mock_model = MagicMock()
    mock_model.get_cached_parameters.return_value = {"param_a": 1, "param_b": 2}
    view = ParameterView(mock_model)
    result = dir(view)
    assert "param_a" in result
    assert "param_b" in result


def test_parameter_view_dir_error():
    mock_model = MagicMock()
    mock_model.get_cached_parameters.side_effect = AttributeError
    view = ParameterView(mock_model)
    result = dir(view)
    assert result == []

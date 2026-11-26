# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest
from model_api.adapters.ovms_adapter import OVMSAdapter


def test_is_ovms_model_valid():
    assert OVMSAdapter.is_ovms_model("localhost:9000/v2/models/my_model") is True
    assert OVMSAdapter.is_ovms_model("localhost:9000/v2/models/my_model/versions/1") is True
    assert OVMSAdapter.is_ovms_model("http://server:8080/v2/models/detection") is True


def test_is_ovms_model_invalid():
    assert OVMSAdapter.is_ovms_model("path/to/model.xml") is False
    assert OVMSAdapter.is_ovms_model("") is False
    assert OVMSAdapter.is_ovms_model(123) is False


def test_parse_model_arg_valid():
    url, name, version = OVMSAdapter.parse_model_arg("localhost:9000/v2/models/my_model")
    assert url == "localhost:9000"
    assert name == "my_model"
    assert version == ""


def test_parse_model_arg_with_version():
    _url, name, version = OVMSAdapter.parse_model_arg("localhost:9000/v2/models/my_model/versions/2")
    assert name == "my_model"
    assert version == "2"


def test_parse_model_arg_invalid():
    with pytest.raises(ValueError, match="invalid"):
        OVMSAdapter.parse_model_arg("not-a-valid-url")


def test_parse_model_arg_not_string():
    with pytest.raises(TypeError, match="must be str"):
        OVMSAdapter.parse_model_arg(123)

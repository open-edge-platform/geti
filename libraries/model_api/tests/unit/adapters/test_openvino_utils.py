# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


from model_api.adapters.inference_adapter import Metadata
from model_api.adapters.openvino_adapter import (
    get_user_config,
    parse_devices,
    parse_value_per_device,
)

# --- Metadata ---


def test_metadata_defaults():
    m = Metadata()
    assert m.names == set()
    assert m.shape == []
    assert m.layout == ""
    assert m.precision == ""
    assert m.type == ""
    assert m.meta == {}


def test_metadata_with_values():
    m = Metadata(
        names={"input"},
        shape=[1, 3, 224, 224],
        layout="NCHW",
        precision="FP32",
    )
    assert "input" in m.names
    assert m.shape == [1, 3, 224, 224]


# --- parse_devices ---


def test_parse_devices_single():
    assert parse_devices("CPU") == ["CPU"]
    assert parse_devices("GPU") == ["GPU"]


def test_parse_devices_hetero():
    result = parse_devices("HETERO:CPU,GPU")
    assert "CPU" in result
    assert "GPU" in result


def test_parse_devices_multi():
    result = parse_devices("MULTI:CPU,GPU")
    assert "CPU" in result
    assert "GPU" in result


# --- parse_value_per_device ---


def test_parse_value_per_device_single():
    result = parse_value_per_device({"CPU", "GPU"}, "4")
    assert result["CPU"] == 4
    assert result["GPU"] == 4


def test_parse_value_per_device_per_device():
    result = parse_value_per_device({"CPU", "GPU"}, "CPU:2,GPU:4")
    assert result["CPU"] == 2
    assert result["GPU"] == 4


def test_parse_value_per_device_empty():
    result = parse_value_per_device({"CPU"}, "")
    assert result == {}


# --- get_user_config ---


def test_get_user_config_cpu():
    config = get_user_config("CPU", "1")
    assert "NUM_STREAMS" in config


def test_get_user_config_cpu_with_threads():
    config = get_user_config("CPU", "1", flags_nthreads=4)
    assert config["INFERENCE_NUM_THREADS"] == "4"


def test_get_user_config_gpu():
    config = get_user_config("GPU", "1")
    assert "NUM_STREAMS" in config


def test_get_user_config_auto():
    config = get_user_config("CPU", "")
    assert config["NUM_STREAMS"] == "NUM_STREAMS_AUTO"

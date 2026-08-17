# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pytest

from app.models import DeviceSpec
from app.models.system import DeviceInfo, DeviceType


class TestDeviceSpec:
    """Test cases for DeviceSpec"""

    @pytest.mark.parametrize(
        "device_str, expected_type, expected_index",
        [
            ("auto", DeviceType.AUTO, 0),
            ("cpu", DeviceType.CPU, 0),
            ("xpu", DeviceType.XPU, 0),
            ("cuda", DeviceType.CUDA, 0),
            ("xpu-0", DeviceType.XPU, 0),
            ("xpu-2", DeviceType.XPU, 2),
            ("cuda-1", DeviceType.CUDA, 1),
            ("XPU-1", DeviceType.XPU, 1),  # case-insensitive
        ],
    )
    def test_parse_valid(self, device_str, expected_type, expected_index):
        """Test parsing valid device strings"""
        spec = DeviceSpec.parse(device_str)

        assert spec.type == expected_type
        if spec.is_auto() or spec.is_cpu():
            assert str(spec) == f"{expected_type.value}"
        else:
            assert str(spec) == f"{expected_type.value}-{expected_index}"

    @pytest.mark.parametrize(
        "device_str",
        [
            "auto-0",  # auto must not have an index
            "cpu-0",  # cpu must not have an index
            "cpu-cpu",
            "cpu--1",
            "cpu-",
            "cpu-0.9",
            "1",
            "-1",
            "gpu",
            "tpu",
            "invalid",
            "",
        ],
    )
    def test_parse_invalid(self, device_str):
        """Test parsing invalid device strings raises ValueError"""
        with pytest.raises(ValueError):
            DeviceSpec.parse(device_str)

    def test_is_cpu(self):
        assert DeviceSpec.parse("cpu").is_cpu() is True
        assert DeviceSpec.parse("xpu").is_cpu() is False

    def test_is_auto(self):
        assert DeviceSpec.parse("auto").is_auto() is True
        assert DeviceSpec.parse("cpu").is_auto() is False

    def test_is_cuda(self):
        assert DeviceSpec.parse("cuda").is_cuda() is True
        assert DeviceSpec.parse("cuda-1").is_cuda() is True
        assert DeviceSpec.parse("xpu").is_cuda() is False

    def test_fixed_device_cpu(self):
        assert DeviceSpec.parse("cpu").fixed_device() == DeviceInfo.cpu()

    def test_fixed_device_auto(self):
        assert DeviceSpec.parse("auto").fixed_device() == DeviceInfo.auto()

    @pytest.mark.parametrize("device_str", ["xpu", "xpu-1", "cuda", "cuda-2"])
    def test_fixed_device_none_for_catalog_devices(self, device_str):
        """XPU/CUDA specs cannot be resolved without consulting a catalog"""
        assert DeviceSpec.parse(device_str).fixed_device() is None

    @pytest.mark.parametrize(
        "device_str, device, expected",
        [
            ("xpu-0", DeviceInfo(type=DeviceType.XPU, name="Intel GPU", memory=1024, index=0), True),
            ("xpu-1", DeviceInfo(type=DeviceType.XPU, name="Intel GPU", memory=1024, index=0), False),
            ("xpu", DeviceInfo(type=DeviceType.XPU, name="Intel GPU", memory=1024, index=0), True),  # default index 0
            ("cuda-0", DeviceInfo(type=DeviceType.XPU, name="Intel GPU", memory=1024, index=0), False),  # type mismatch
            ("cpu", DeviceInfo(type=DeviceType.CPU, name="CPU", memory=None, index=None), True),
        ],
    )
    def test_matches(self, device_str, device, expected):
        assert DeviceSpec.parse(device_str).matches(device) is expected

    def test_str(self):
        assert str(DeviceSpec.parse("xpu-2")) == "xpu-2"
        assert str(DeviceSpec.parse("cpu")) == "cpu"
        assert str(DeviceSpec.parse("auto")) == "auto"

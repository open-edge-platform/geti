# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import MagicMock, patch

import pytest

from app.models.system import DeviceInfo, DeviceType
from app.services.system_service import DeviceSpec, SystemService


class FakeDeviceCatalog:
    """Test double for `DeviceCatalog` — no torch/openvino involved."""

    def __init__(self, devices: list[DeviceInfo]) -> None:
        self._devices = devices

    def devices(self) -> list[DeviceInfo]:
        return self._devices

    def find(self, spec: DeviceSpec) -> DeviceInfo | None:
        if spec.is_cpu():
            return DeviceInfo.cpu()
        if spec.is_auto():
            return DeviceInfo.auto()
        return next((device for device in self._devices if spec.matches(device)), None)


class TestSystemService:
    """Test cases for SystemService"""

    @pytest.fixture
    def fxt_system_service(self) -> SystemService:
        return SystemService()

    def test_get_memory_usage(self, fxt_system_service: SystemService):
        """Test getting memory usage"""
        used, total = fxt_system_service.get_memory_usage()

        assert used > 0
        assert total > 0
        assert used <= total

    def test_get_cpu_usage(self, fxt_system_service: SystemService):
        """Test getting CPU usage"""
        cpu_usage = fxt_system_service.get_cpu_usage()

        assert cpu_usage >= 0.0

    def test_training_devices_cpu_only(self):
        """Test getting devices when only CPU is available"""
        service = SystemService(training_catalog=FakeDeviceCatalog([DeviceInfo.cpu()]))

        devices = service.training_devices()

        assert len(devices) == 1
        assert devices[0].name == "CPU"
        assert devices[0].memory is None
        assert devices[0].index is None

    def test_training_devices_with_xpu(self, fxt_system_service: SystemService):
        """Test getting devices when Intel XPU is available"""
        xpu_device = DeviceInfo(type=DeviceType.XPU, name="Intel(R) Graphics [0x7d41]", memory=36022263808, index=0)
        service = SystemService(training_catalog=FakeDeviceCatalog([DeviceInfo.cpu(), xpu_device]))

        devices = service.training_devices()

        assert len(devices) == 2
        assert devices[1].name == "Intel(R) Graphics [0x7d41]"
        assert devices[1].memory == 36022263808
        assert devices[1].index == 0

    def test_training_devices_with_cuda(self, fxt_system_service: SystemService):
        """Test getting devices when NVIDIA CUDA is available"""
        cuda_device = DeviceInfo(type=DeviceType.CUDA, name="NVIDIA GeForce RTX 4090", memory=25769803776, index=0)
        service = SystemService(training_catalog=FakeDeviceCatalog([DeviceInfo.cpu(), cuda_device]))

        devices = service.training_devices()

        assert len(devices) == 2
        assert devices[1].name == "NVIDIA GeForce RTX 4090"
        assert devices[1].memory == 25769803776
        assert devices[1].index == 0

    def test_training_devices_with_multiple_devices(self, fxt_system_service: SystemService):
        """Test getting devices when multiple GPUs are available"""
        xpu_device = DeviceInfo(type=DeviceType.XPU, name="Intel(R) Graphics [0x7d41]", memory=36022263808, index=0)
        cuda_device = DeviceInfo(type=DeviceType.CUDA, name="NVIDIA GeForce RTX 4090", memory=25769803776, index=0)
        service = SystemService(training_catalog=FakeDeviceCatalog([DeviceInfo.cpu(), xpu_device, cuda_device]))

        devices = service.training_devices()

        assert len(devices) == 3

    def test_is_valid_inference_device_auto_always_valid(self, fxt_system_service: SystemService):
        """Test that AUTO device is always valid"""
        assert fxt_system_service.is_valid_inference_device("auto") is True

    def test_is_valid_inference_device_cpu_always_valid(self, fxt_system_service: SystemService):
        """Test that CPU device is always valid"""
        assert fxt_system_service.is_valid_inference_device("cpu") is True

    def test_is_valid_inference_device_xpu_available(self, fxt_system_service: SystemService):
        """Test validating XPU device when available"""
        xpu_devices = [
            DeviceInfo(type=DeviceType.XPU, name="Intel XPU", memory=36022263808, index=0),
            DeviceInfo(type=DeviceType.XPU, name="Intel XPU", memory=36022263808, index=1),
        ]
        service = SystemService(inference_catalog=FakeDeviceCatalog(xpu_devices))

        assert service.is_valid_inference_device("xpu") is True
        assert service.is_valid_inference_device("xpu-0") is True
        assert service.is_valid_inference_device("xpu-1") is True
        assert service.is_valid_inference_device("xpu-2") is False

    def test_is_valid_inference_device_xpu_not_available(self, fxt_system_service: SystemService):
        """Test validating XPU device when not available"""
        service = SystemService(inference_catalog=FakeDeviceCatalog([]))

        assert service.is_valid_inference_device("xpu") is False
        assert service.is_valid_inference_device("xpu-0") is False

    def test_is_valid_training_device_cuda_available(self, fxt_system_service: SystemService):
        """Test validating CUDA device when available"""
        cuda_devices = [
            DeviceInfo(type=DeviceType.CUDA, name="NVIDIA GPU", memory=25769803776, index=index) for index in range(3)
        ]
        service = SystemService(training_catalog=FakeDeviceCatalog(cuda_devices))

        assert service.is_valid_training_device("cuda") is True
        assert service.is_valid_training_device("cuda-0") is True
        assert service.is_valid_training_device("cuda-1") is True
        assert service.is_valid_training_device("cuda-2") is True
        assert service.is_valid_training_device("cuda-3") is False

    def test_is_valid_training_device_cuda_not_available(self, fxt_system_service: SystemService):
        """Test validating CUDA device when not available"""
        service = SystemService(training_catalog=FakeDeviceCatalog([]))

        assert service.is_valid_training_device("cuda") is False
        assert service.is_valid_training_device("cuda-0") is False

    def test_inference_devices_with_multiple_devices(self, fxt_system_service: SystemService):
        """Test getting inference devices via OpenVINO: CPU, integrated GPUs, and Intel discrete GPUs are returned"""

        def fake_get_property(device: str, prop: str):
            if prop == "FULL_DEVICE_NAME":
                return {
                    "GPU.0": "Intel(R) Graphics [0x7d41]",
                    "GPU.1": "Intel(R) Arc(TM) A770",
                    "GPU.2": "NVIDIA GeForce RTX 4090",
                }[device]
            if prop == "GPU_DEVICE_TOTAL_MEM_SIZE":
                return {"GPU.0": 36022263808, "GPU.1": 17179869184, "GPU.2": 25769803776}[device]
            if prop == "DEVICE_TYPE":
                # GPU.0 is an integrated GPU (iGPU), GPU.1 and GPU.2 are discrete GPUs (dGPU)
                return {
                    "GPU.0": "Type.INTEGRATED",
                    "GPU.1": "Type.DISCRETE",
                    "GPU.2": "Type.DISCRETE",
                }[device]
            raise KeyError(prop)

        mock_core = MagicMock()
        mock_core.available_devices = ["CPU", "GPU.0", "GPU.1", "GPU.2"]
        mock_core.get_property.side_effect = fake_get_property

        with patch("openvino.Core", return_value=mock_core):
            inference_devices = SystemService().inference_devices()

        # The non-Intel discrete GPU (GPU.2) must be filtered out, leaving CPU, the integrated GPU,
        # and the Intel discrete GPU.
        assert len(inference_devices) == 3
        assert not any(device.type == "cuda" for device in inference_devices)
        assert inference_devices[0].type == "cpu"
        assert inference_devices[0].name == "CPU"
        assert inference_devices[0].memory is None
        assert inference_devices[0].index is None
        assert inference_devices[1].type == "xpu"
        assert inference_devices[1].name == "Intel(R) Graphics [0x7d41]"
        assert inference_devices[1].memory == 36022263808
        assert inference_devices[1].index == 0
        assert inference_devices[2].type == "xpu"
        assert inference_devices[2].name == "Intel(R) Arc(TM) A770"
        assert inference_devices[2].memory == 17179869184
        assert inference_devices[2].index == 1

    def test_inference_devices_cpu_only(self, fxt_system_service: SystemService):
        """Test getting inference devices when only CPU is available via OpenVINO"""
        mock_core = MagicMock()
        mock_core.available_devices = ["CPU"]

        with patch("openvino.Core", return_value=mock_core):
            inference_devices = fxt_system_service.inference_devices()

        assert len(inference_devices) == 1
        assert inference_devices[0].type == "cpu"

    def test_inference_devices_fallback_on_error(self, fxt_system_service: SystemService):
        """Test fallback to CPU-only when OpenVINO query fails"""
        with patch("openvino.Core", side_effect=RuntimeError("boom")):
            inference_devices = fxt_system_service.inference_devices()

        assert len(inference_devices) == 1
        assert inference_devices[0].type == "cpu"

    def test_is_valid_inference_device_invalid_type(self, fxt_system_service: SystemService):
        """Test validating invalid device types"""
        assert fxt_system_service.is_valid_inference_device("cpu-cpu") is False
        assert fxt_system_service.is_valid_inference_device("cpu--1") is False
        assert fxt_system_service.is_valid_inference_device("cpu-") is False
        assert fxt_system_service.is_valid_inference_device("cpu-0.9") is False
        assert fxt_system_service.is_valid_inference_device("1") is False
        assert fxt_system_service.is_valid_inference_device("-1") is False
        assert fxt_system_service.is_valid_inference_device("gpu") is False
        assert fxt_system_service.is_valid_inference_device("tpu") is False
        assert fxt_system_service.is_valid_inference_device("invalid") is False

    def test_training_device_info(self, fxt_system_service: SystemService):
        """Test getting training device info"""
        xpu_device = DeviceInfo(type=DeviceType.XPU, name="Intel(R) Graphics [0x7d41]", memory=36022263808, index=0)
        service = SystemService(training_catalog=FakeDeviceCatalog([DeviceInfo.cpu(), xpu_device]))

        device_info = service.training_device("cpu")

        assert device_info.type == "cpu"
        assert device_info.name == "CPU"
        assert device_info.memory is None
        assert device_info.index is None

        device_info = service.training_device("xpu-0")

        assert device_info.type == "xpu"
        assert device_info.name == "Intel(R) Graphics [0x7d41]"
        assert device_info.memory == 36022263808
        assert device_info.index == 0

    def test_training_device_info_invalid(self, fxt_system_service: SystemService):
        """Test getting device info for invalid device"""
        service = SystemService(training_catalog=FakeDeviceCatalog([]))

        with pytest.raises(ValueError):
            service.training_device("xpu-999")

    @pytest.mark.parametrize(
        "raw_device_name, expected_ov_device_name",
        [
            ("auto", "AUTO"),
            ("cpu", "CPU"),
            ("xpu", "GPU.0"),  # default to GPU.0 if index is not specified
            ("xpu-0", "GPU.0"),
            ("xpu-1", "GPU.1"),
        ],
    )
    def test_get_inference_device_name(
        self, fxt_system_service: SystemService, raw_device_name, expected_ov_device_name
    ) -> None:
        """Test conversion of raw device names to OpenVINO device names."""
        xpu_devices = [
            DeviceInfo(type=DeviceType.XPU, name="Intel(R) Graphics [0x7d41]", memory=36022263808, index=index)
            for index in range(2)
        ]
        service = SystemService(inference_catalog=FakeDeviceCatalog(xpu_devices))

        geti_device = service.inference_device(raw_device_name)

        assert geti_device.as_openvino == expected_ov_device_name

    def test_get_ov_device_name_invalid(self, fxt_system_service: SystemService) -> None:
        """Test conversion of raw device names to OpenVINO device names."""
        with pytest.raises(ValueError):
            _ = fxt_system_service.inference_device("gpu")

    def test_inference_device_fallback_to_cpu(self, fxt_system_service: SystemService) -> None:
        """Malformed, CUDA, and unavailable inference devices fall back to CPU when fallback_to_cpu=True."""
        assert fxt_system_service.inference_device("not-a-device!!", fallback_to_cpu=True) == DeviceInfo.cpu()
        assert fxt_system_service.inference_device("cuda", fallback_to_cpu=True) == DeviceInfo.cpu()
        assert fxt_system_service.inference_device("xpu-2", fallback_to_cpu=True) == DeviceInfo.cpu()

    def test_list_cameras(self, fxt_system_service: SystemService):
        """Test listing camera devices"""
        with patch("app.services.system_service.enumerate_cameras") as mock_enumerate_cameras:
            # Mock camera device
            mock_camera = MagicMock()
            mock_camera.name = "Integrated Camera"
            mock_camera.index = 1400

            mock_enumerate_cameras.return_value = [mock_camera]

            camera_devices = fxt_system_service.list_cameras()

            assert len(camera_devices) == 1
            assert camera_devices[0].name == "Integrated Camera [1400]"
            assert camera_devices[0].index == 1400

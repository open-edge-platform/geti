# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import platform
import re
from typing import Any, Protocol

import cv2
import psutil
from cv2_enumerate_cameras import enumerate_cameras
from loguru import logger

from app.models.system import CameraInfo, DeviceInfo, DeviceType

DEFAULT_DEVICE = "cpu"
CV2_BACKENDS = {
    "Windows": cv2.CAP_MSMF,
    "Linux": cv2.CAP_V4L2,
    "Darwin": cv2.CAP_AVFOUNDATION,
}


class DeviceSpec:
    """A parsed device request, e.g. 'xpu-1', that knows how to match a `DeviceInfo`."""

    _PATTERN = re.compile(r"^(auto|cpu|xpu|cuda)(-(\d+))?$")

    def __init__(self, device_type: DeviceType, index: int) -> None:
        self._type = device_type
        self._index = index

    @classmethod
    def parse(cls, device_str: str) -> "DeviceSpec":
        """
        Parse a device string into a `DeviceSpec`.

        Args:
            device_str: Device string in format '<target>[-<index>]'
                (e.g., 'auto', 'cpu', 'xpu', 'cuda', 'xpu-2', 'cuda-1').

        Returns:
            DeviceSpec: The parsed device specification.

        Raises:
            ValueError: If `device_str` does not match the expected format.
        """
        match = cls._PATTERN.match(device_str.lower())
        if not match:
            raise ValueError(f"Invalid device string: {device_str}")
        kind, _, index = match.groups()
        return cls(DeviceType(kind), int(index) if index is not None else 0)

    @property
    def type(self) -> DeviceType:
        """The requested device type."""
        return self._type

    def is_cpu(self) -> bool:
        """Whether this spec refers to the CPU."""
        return self._type == DeviceType.CPU

    def is_auto(self) -> bool:
        """Whether this spec refers to automatic device selection."""
        return self._type == DeviceType.AUTO

    def is_cuda(self) -> bool:
        """Whether this spec refers to a CUDA device."""
        return self._type == DeviceType.CUDA

    def matches(self, device: DeviceInfo) -> bool:
        """
        Check whether a `DeviceInfo` satisfies this spec.

        Args:
            device: The candidate device.

        Returns:
            bool: True if `device` has the same type and index as this spec.
        """
        return self._type == device.type and self._index == (device.index or 0)

    def __str__(self) -> str:
        return f"{self._type.value}-{self._index}"

    def fixed_device(self) -> DeviceInfo | None:
        """Resolve this spec to a fixed `DeviceInfo` without consulting a device catalog.

        `AUTO` and `CPU` are always available and never need to be looked up among the
        devices a catalog actually discovers (e.g. via PyTorch or OpenVINO)."""
        if self.is_cpu():
            return DeviceInfo.cpu()
        if self.is_auto():
            return DeviceInfo.auto()
        return None


class DeviceCatalog(Protocol):
    """Can list and resolve devices."""

    def devices(self) -> list[DeviceInfo]: ...
    def find(self, spec: DeviceSpec) -> DeviceInfo | None: ...


class TrainingDeviceCatalog:
    """Devices available for training, sourced from PyTorch (CPU, XPU, CUDA)."""

    def __init__(self) -> None:
        self._torch: Any = None

    def _get_torch(self) -> Any:
        if self._torch is None:
            import torch

            self._torch = torch
        return self._torch

    def devices(self) -> list[DeviceInfo]:
        """
        Get available compute devices for training.

        Returns:
            list[DeviceInfo]: CPU plus any detected XPU/CUDA devices.
        """
        torch = self._get_torch()
        devices: list[DeviceInfo] = [DeviceInfo.cpu()]
        devices.extend(self._xpu_devices(torch))
        devices.extend(self._cuda_devices(torch))
        return devices

    def find(self, spec: DeviceSpec) -> DeviceInfo | None:
        """
        Resolve a `DeviceSpec` against training devices.

        Args:
            spec: The requested device specification.

        Returns:
            DeviceInfo | None: The matching device, or None if unavailable.
        """
        if (device := spec.fixed_device()) is not None:
            return device
        return next((device for device in self.devices() if spec.matches(device)), None)

    @staticmethod
    def _xpu_devices(torch: Any) -> list[DeviceInfo]:
        if not torch.xpu.is_available():
            return []
        devices = []
        for index in range(torch.xpu.device_count()):
            props = torch.xpu.get_device_properties(index)
            devices.append(DeviceInfo(type=DeviceType.XPU, name=props.name, memory=props.total_memory, index=index))
        return devices

    @staticmethod
    def _cuda_devices(torch: Any) -> list[DeviceInfo]:
        if not torch.cuda.is_available():
            return []
        devices = []
        for index in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(index)
            devices.append(DeviceInfo(type=DeviceType.CUDA, name=props.name, memory=props.total_memory, index=index))
        return devices


class OpenVinoInferenceDeviceCatalog:
    """
    Devices available for OpenVINO inference (CPU, integrated GPUs, and Intel discrete GPUs).

    OpenVINO returns device names such as 'CPU', 'GPU', 'GPU.0', 'GPU.1', ... Per the OpenVINO
    documentation, when an integrated GPU is present it always takes id 0, and 'GPU' is an alias
    for 'GPU.0'. A GPU is included when it is either integrated (iGPU) or an Intel-branded
    discrete GPU (dGPU), since only Intel GPUs can perform OpenVINO inference.
    """

    def __init__(self) -> None:
        self._core = self._try_create_core()

    @staticmethod
    def _try_create_core() -> Any | None:
        try:
            import openvino as ov

            return ov.Core()
        except Exception:
            logger.exception("Failed to query OpenVINO inference devices; falling back to CPU only.")
            return None

    def devices(self) -> list[DeviceInfo]:
        """
        Get available compute devices for inference.

        Returns:
            list[DeviceInfo]: CPU plus any detected integrated/Intel discrete GPUs.
        """
        if self._core is None:
            return [DeviceInfo.cpu()]

        found = [d for name in self._core.available_devices if (d := self._device_info(name)) is not None]
        if not any(device.type == DeviceType.CPU for device in found):
            found.insert(0, DeviceInfo.cpu())
        return found

    def find(self, spec: DeviceSpec) -> DeviceInfo | None:
        """
        Resolve a `DeviceSpec` against inference devices.

        Args:
            spec: The requested device specification.

        Returns:
            DeviceInfo | None: The matching device, or None if unavailable.
        """
        if (device := spec.fixed_device()) is not None:
            return device
        return next((device for device in self.devices() if spec.matches(device)), None)

    def _device_info(self, ov_device: str) -> DeviceInfo | None:
        if ov_device == "CPU":
            return DeviceInfo.cpu()
        if ov_device.startswith("GPU"):
            return self._gpu_device_info(ov_device)
        logger.debug("Skipping unsupported OpenVINO inference device: {}", ov_device)
        return None

    def _gpu_device_info(self, ov_device: str) -> DeviceInfo | None:
        try:
            device_type = self._core.get_property(ov_device, "DEVICE_TYPE")  # pyrefly: ignore[missing-attribute]
            name = str(self._core.get_property(ov_device, "FULL_DEVICE_NAME"))  # pyrefly: ignore[missing-attribute]
        except Exception:
            logger.exception("Failed to query required OpenVINO GPU properties for '{}'; skipping.", ov_device)
            return None

        if not self._is_supported_gpu(device_type=device_type, name=name):
            logger.debug("Skipping non-Intel discrete OpenVINO GPU device: {} ({})", ov_device, name)
            return None

        return DeviceInfo(
            type=DeviceType.XPU, name=name, memory=self._gpu_memory(ov_device), index=self._gpu_index(ov_device)
        )

    @staticmethod
    def _is_supported_gpu(device_type: Any, name: str) -> bool:
        is_integrated = "integrated" in str(device_type).lower()
        is_intel = "intel" in name.lower()
        return is_integrated or is_intel

    @staticmethod
    def _gpu_index(ov_device: str) -> int:
        if ov_device == "GPU":
            return 0
        return int(ov_device.split(".", maxsplit=1)[1])

    def _gpu_memory(self, ov_device: str) -> int | None:
        try:
            return int(
                self._core.get_property(ov_device, "GPU_DEVICE_TOTAL_MEM_SIZE")  # pyrefly: ignore[missing-attribute]
            )
        except Exception:
            return None


class SystemService:
    """Reports host system information and resolves compute devices for training and inference.

    Exposes process-level CPU/memory usage, available camera devices, and device lookup backed by
    pluggable `DeviceCatalog` implementations (defaults to PyTorch for training and OpenVINO for
    inference).
    """

    def __init__(
        self, training_catalog: DeviceCatalog | None = None, inference_catalog: DeviceCatalog | None = None
    ) -> None:
        self.process = psutil.Process()
        self._training = training_catalog or TrainingDeviceCatalog()
        self._inference = inference_catalog or OpenVinoInferenceDeviceCatalog()

    def get_memory_usage(self) -> tuple[float, float]:
        """
        Get the memory usage of the process

        Returns:
            tuple[float, float]: Used memory in MB and total available memory in MB
        """
        memory_info = psutil.virtual_memory()
        return self.process.memory_info().rss / (1024 * 1024), memory_info.total / (1024 * 1024)

    def get_cpu_usage(self) -> float:
        """
        Get the CPU usage of the process

        Returns:
            float: CPU usage in percentage
        """
        return self.process.cpu_percent(interval=None)

    def training_devices(self) -> list[DeviceInfo]:
        """
        Get available compute devices for training (CPU, XPU, CUDA).

        Returns:
            list[DeviceInfo]: List of available training devices.
        """
        return self._training.devices()

    def inference_devices(self) -> list[DeviceInfo]:
        """
        Get available compute devices for inference (CPU and Intel GPUs, via OpenVINO).

        Returns:
            list[DeviceInfo]: List of available inference devices.
        """
        return self._inference.devices()

    def training_device(self, device_str: str) -> DeviceInfo:
        """
        Resolve a device string to a `DeviceInfo` for training.

        Args:
            device_str: Device string in format '<target>[-<index>]'
                (e.g., 'auto', 'cpu', 'xpu', 'cuda', 'xpu-2', 'cuda-1').

        Returns:
            DeviceInfo: Information about the specified training device.

        Raises:
            ValueError: If `device_str` is invalid or not available for training.
        """
        spec = self._parse(device_str)
        device = self._training.find(spec)
        if device is None:
            raise ValueError(f"Device '{device_str}' is not available for training.")
        return device

    def inference_device(self, device_str: str) -> DeviceInfo:
        """
        Resolve a device string to a `DeviceInfo` for inference.

        Args:
            device_str: Device string in format '<target>[-<index>]'
                (e.g., 'auto', 'cpu', 'xpu', 'xpu-2').

        Returns:
            DeviceInfo: Information about the specified inference device.

        Raises:
            ValueError: If `device_str` is invalid, is a CUDA device, or is not available
                for inference.
        """
        spec = self._parse(device_str)
        if spec.is_cuda():
            raise ValueError(f"Device '{device_str}' is not valid for inference (CUDA devices are not supported).")
        device = self._inference.find(spec)
        if device is None:
            raise ValueError(f"Device '{device_str}' is not available for inference.")
        return device

    def is_valid_training_device(self, device_str: str) -> bool:
        """
        Check whether a device string is available for training.

        Args:
            device_str: Device string to validate.

        Returns:
            bool: True if the device is available for training.
        """
        return self._is_valid(device_str, self._training)

    def is_valid_inference_device(self, device_str: str) -> bool:
        """
        Check whether a device string is available for inference.

        Args:
            device_str: Device string to validate.

        Returns:
            bool: True if the device is available for inference.
        """
        try:
            spec = self._parse(device_str)
        except ValueError:
            return False
        if spec.is_cuda():
            return False
        return self._inference.find(spec) is not None

    @staticmethod
    def _is_valid(device_str: str, catalog: DeviceCatalog) -> bool:
        try:
            spec = DeviceSpec.parse(device_str)
        except ValueError:
            logger.debug("Cannot parse invalid device string: {}", device_str)
            return False
        return catalog.find(spec) is not None

    @staticmethod
    def _parse(device_str: str) -> DeviceSpec:
        try:
            return DeviceSpec.parse(device_str)
        except ValueError as ex:
            raise ValueError(f"Invalid device string: {device_str}") from ex

    def supports_int8(self, device: DeviceInfo) -> bool:
        """
        Check if the given device supports INT8 inference using OpenVINO.

        For CPU devices, INT8 is always supported. For GPU devices, the check is done via
        OpenVINO's `OPTIMIZATION_CAPABILITIES` property.

        Args:
            device: The device to check.

        Returns:
            bool: True if the device supports INT8 inference, False otherwise.
        """
        if device.type == DeviceType.CPU:
            return True
        if device.type == DeviceType.CUDA:
            return False
        try:
            from model_api.adapters import create_core

            core = create_core()
            capabilities = core.get_property(device_name=device.as_openvino, property="OPTIMIZATION_CAPABILITIES")
            return "INT8" in capabilities
        except Exception:
            logger.exception(
                "Failed to query INT8 support for device '{}' (OpenVINO device '{}'). Assuming not supported.",
                device,
                device.as_openvino,
            )
            return False

    @staticmethod
    def list_cameras() -> list[CameraInfo]:
        """
        List available camera devices.
        Camera names are formatted as "<camera_name> [<index>]".

        Returns:
            list[CameraInfo]: List of available camera devices
        """
        if (backend := CV2_BACKENDS.get(platform.system())) is None:
            raise RuntimeError(f"Unsupported platform: {platform.system()}")

        return [CameraInfo(index=cam.index, name=f"{cam.name} [{cam.index}]") for cam in enumerate_cameras(backend)]

# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import re

from app.models.system import DeviceInfo, DeviceType


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
        if kind in {"auto", "cpu"} and index is not None:
            raise ValueError(f"Invalid device string: {device_str}")
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
        if self.is_auto() or self.is_cpu():
            return self._type.value
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

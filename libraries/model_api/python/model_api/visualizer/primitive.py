"""Base class for primitives."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import PIL


class Primitive(ABC):
    """Primitive class."""

    @abstractmethod
    def compute(self, image: PIL.Image, **kwargs) -> PIL.Image:
        pass

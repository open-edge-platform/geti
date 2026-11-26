"""Base class for primitives."""

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import PIL


class Primitive(ABC):
    """Base class for primitives."""

    @abstractmethod
    def compute(self, image: PIL.Image) -> PIL.Image:
        """Compute the primitive."""

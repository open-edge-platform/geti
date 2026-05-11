"""Visualization Layout."""

# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Type

if TYPE_CHECKING:
    import PIL

    from model_api.visualizer.primitive import Primitive

    from .scene import Scene


class Layout(ABC):
    """Base class for layouts."""

    @abstractmethod
    def _compute_on_primitive(self, primitive: Type[Primitive], image: PIL.Image, scene: Scene) -> PIL.Image | None:
        pass

    @abstractmethod
    def __call__(self, scene: Scene) -> PIL.Image:
        """Compute the layout."""

"""Visualization Layout"""

# Copyright (C) 2024 Intel Corporation
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

    def _compute_on_primitive(self, primitive: Type[Primitive], image: PIL.Image, scene: Scene) -> PIL.Image | None:
        if scene.has_primitives(primitive):
            primitives = scene.get_primitives(primitive)
            for _primitive in primitives:
                image = _primitive.compute(image)
            return image
        return None

    @abstractmethod
    def __call__(self, scene: Scene) -> PIL.Image:
        """Compute the layout."""


class Flatten(Layout):
    """Put all primitives on top of each other.

    Args:
        *args (Type[Primitive]): Primitives to be applied.
    """

    def __init__(self, *args: Type[Primitive]) -> None:
        self.children = args

    def __call__(self, scene: Scene) -> PIL.Image:
        _image: PIL.Image = scene.base.copy()
        for child in self.children:
            output = self._compute_on_primitive(child, _image, scene)
            if output is not None:
                _image = output
        return _image

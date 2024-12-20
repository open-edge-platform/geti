"""Visualization Layout"""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import PIL

    from model_api.visualizer.primitive import Primitive

    from .scene import Scene


class Layout(ABC):
    """Base class for layouts."""

    def _compute_on_primitive(self, primitive: Primitive, image: PIL.Image, scene: Scene) -> PIL.Image | None:
        if scene.has_primitives(type(primitive)):
            primitives = scene.get_primitives(type(primitive))
            for primitive in primitives:
                image = primitive.compute(image)
            return image
        return None

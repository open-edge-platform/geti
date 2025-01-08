"""Flatten Layout."""

# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, Type, Union

from .layout import Layout

if TYPE_CHECKING:
    import PIL

    from model_api.visualizer.primitive import Primitive
    from model_api.visualizer.scene import Scene


class Flatten(Layout):
    """Put all primitives on top of each other.

    Args:
        *args (Union[Type[Primitive], Layout]): Primitives or layouts to be applied.
    """

    def __init__(self, *args: Union[Type[Primitive], Layout]) -> None:
        self.children = args

    def _compute_on_primitive(self, primitive: Type[Primitive], image: PIL.Image, scene: Scene) -> PIL.Image | None:
        if scene.has_primitives(primitive):
            primitives = scene.get_primitives(primitive)
            for _primitive in primitives:
                image = _primitive.compute(image)
            return image
        return None

    def __call__(self, scene: Scene) -> PIL.Image:
        _image: PIL.Image = scene.base.copy()
        for child in self.children:
            _image = child(scene) if isinstance(child, Layout) else self._compute_on_primitive(child, _image, scene)
        return _image

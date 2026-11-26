"""Flatten Layout."""

# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, Type, Union, cast

from model_api.visualizer.primitive import Label

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
            if primitive == Label:  # Labels need to be rendered next to each other
                # cast is needed as mypy does not know that the primitives are of type Label.
                primitives_ = cast("list[Label]", primitives)
                image = Label.overlay_labels(image, primitives_)
            else:
                # Other primitives are rendered on top of each other
                for _primitive in primitives:
                    image = _primitive.compute(image)
            return image
        return None

    def __call__(self, scene: Scene) -> PIL.Image:
        image: PIL.Image = scene.base.copy()
        for child in self.children:
            image_ = child(scene) if isinstance(child, Layout) else self._compute_on_primitive(child, image, scene)
            if image_ is not None:
                image = image_
        return image

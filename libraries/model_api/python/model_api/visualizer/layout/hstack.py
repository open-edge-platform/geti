"""Horizontal Stack Layout."""

# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, Type, Union

import PIL

from .layout import Layout

if TYPE_CHECKING:
    from model_api.visualizer.primitive import Primitive
    from model_api.visualizer.scene import Scene


class HStack(Layout):
    """Horizontal Stack Layout.

    Args:
        *args (Union[Type[Primitive], Layout]): Primitives or layouts to be applied.
    """

    def __init__(self, *args: Union[Type[Primitive], Layout]) -> None:
        self.children = args

    def _compute_on_primitive(self, primitive: Type[Primitive], image: PIL.Image, scene: Scene) -> PIL.Image | None:
        if scene.has_primitives(primitive):
            images = []
            for _primitive in scene.get_primitives(primitive):
                _image = _primitive.compute(image.copy())
                images.append(_image)
            return self._stitch(*images)
        return None

    @staticmethod
    def _stitch(*images: PIL.Image) -> PIL.Image:
        """Stitch images horizontally.

        Args:
            images (PIL.Image): Images to be stitched.

        Returns:
            PIL.Image: Stitched image.
        """
        new_image = PIL.Image.new(
            "RGB",
            (
                sum(image.width for image in images),
                max(image.height for image in images),
            ),
        )
        x_offset = 0
        for image in images:
            new_image.paste(image, (x_offset, 0))
            x_offset += image.width
        return new_image

    def __call__(self, scene: Scene) -> PIL.Image:
        """Stitch images horizontally.

        Args:
            scene (Scene): Scene to be stitched.

        Returns:
            PIL.Image: Stitched image.
        """
        images: list[PIL.Image] = []
        for child in self.children:
            if isinstance(child, Layout):
                _image = child(scene)
            else:
                _image = self._compute_on_primitive(child, scene.base.copy(), scene)
            if _image is not None:
                images.append(_image)
        return self._stitch(*images)

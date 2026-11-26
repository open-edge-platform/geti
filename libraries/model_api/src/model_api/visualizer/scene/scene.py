"""Scene object."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np
from PIL import Image

from model_api.visualizer.primitive import BoundingBox, Keypoint, Label, Overlay, Polygon, Primitive

if TYPE_CHECKING:
    from pathlib import Path

    from model_api.visualizer.layout import Layout


class Scene:
    """Scene object.

    Used by the visualizer to render.
    """

    def __init__(
        self,
        base: Image,
        bounding_box: BoundingBox | list[BoundingBox] | None = None,
        label: Label | list[Label] | None = None,
        overlay: Overlay | list[Overlay] | np.ndarray | None = None,
        polygon: Polygon | list[Polygon] | None = None,
        keypoints: Keypoint | list[Keypoint] | np.ndarray | None = None,
        layout: Layout | None = None,
    ) -> None:
        self.base = base
        self.overlay = self._to_overlay(overlay)
        self.bounding_box = self._to_bounding_box(bounding_box)
        self.label = self._to_label(label)
        self.polygon = self._to_polygon(polygon)
        self.keypoints = self._to_keypoints(keypoints)
        self.layout = layout

    def show(self) -> None:
        self.render().show()

    def save(self, path: Path) -> None:
        self.render().save(path)

    def render(self) -> Image:
        if self.layout is None:
            return self.default_layout(self)
        return self.layout(self)

    def has_primitives(self, primitive: type[Primitive]) -> bool:
        if primitive == Overlay:
            return bool(self.overlay)
        if primitive == BoundingBox:
            return bool(self.bounding_box)
        if primitive == Label:
            return bool(self.label)
        if primitive == Polygon:
            return bool(self.polygon)
        if primitive == Keypoint:
            return bool(self.keypoints)
        return False

    def get_primitives(self, primitive: type[Primitive]) -> list[Primitive]:
        """Get primitives of the given type.

        Args:
            primitive (type[Primitive]): The type of primitive to get.

        Example:
            >>> scene = Scene(base=Image.new("RGB", (100, 100)), overlay=[Overlay(Image.new("RGB", (100, 100)))])
            >>> scene.get_primitives(Overlay)
            [Overlay(image=Image.new("RGB", (100, 100)))]

        Returns:
            list[Primitive]: The primitives of the given type or an empty list if no primitives are found.
        """
        primitives: list[Primitive] | None = None
        # cast is needed as mypy does not know that the primitives are a subclass of Primitive.
        if primitive == Overlay:
            primitives = cast("list[Primitive]", self.overlay)
        elif primitive == BoundingBox:
            primitives = cast("list[Primitive]", self.bounding_box)
        elif primitive == Label:
            primitives = cast("list[Primitive]", self.label)
        elif primitive == Polygon:
            primitives = cast("list[Primitive]", self.polygon)
        elif primitive == Keypoint:
            primitives = cast("list[Primitive]", self.keypoints)
        else:
            msg = f"Primitive {primitive} not found"
            raise ValueError(msg)
        return primitives or []

    @property
    def default_layout(self) -> Layout:
        """Default layout for the media."""
        msg = "Default layout not implemented"
        raise NotImplementedError(msg)

    def _to_overlay(self, overlay: Overlay | list[Overlay] | np.ndarray | None) -> list[Overlay] | None:
        if isinstance(overlay, np.ndarray):
            image = Image.fromarray(overlay)
            return [Overlay(image)]
        if isinstance(overlay, Overlay):
            return [overlay]
        return overlay

    def _to_bounding_box(self, bounding_box: BoundingBox | list[BoundingBox] | None) -> list[BoundingBox] | None:
        if isinstance(bounding_box, BoundingBox):
            return [bounding_box]
        return bounding_box

    def _to_label(self, label: Label | list[Label] | None) -> list[Label] | None:
        if isinstance(label, Label):
            return [label]
        return label

    def _to_polygon(self, polygon: Polygon | list[Polygon] | None) -> list[Polygon] | None:
        if isinstance(polygon, Polygon):
            return [polygon]
        return polygon

    def _to_keypoints(self, keypoints: Keypoint | list[Keypoint] | np.ndarray | None) -> list[Keypoint] | None:
        if isinstance(keypoints, Keypoint):
            return [keypoints]
        if isinstance(keypoints, np.ndarray):
            return [Keypoint(keypoints)]
        return keypoints

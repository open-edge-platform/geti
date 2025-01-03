"""Scene object."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from PIL import Image

from model_api.visualizer.primitive import Overlay, Primitive

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
        overlay: Overlay | list[Overlay] | np.ndarray | None = None,
        layout: Layout | None = None,
    ) -> None:
        self.base = base
        self.overlay = self._to_overlay(overlay)
        self.layout = layout

    def show(self) -> Image: ...

    def save(self, path: Path) -> None: ...

    def render(self) -> Image:
        if self.layout is None:
            return self.default_layout(self)
        return self.layout(self)

    def has_primitives(self, primitive: type[Primitive]) -> bool:
        if primitive == Overlay:
            return bool(self.overlay)
        return False

    def get_primitives(self, primitive: type[Primitive]) -> list[Primitive]:
        primitives: list[Primitive] | None = None
        if primitive == Overlay:
            primitives = self.overlay  # type: ignore[assignment]  # TODO(ashwinvaidya17): Address this in the next PR
        if primitives is None:
            msg = f"Primitive {primitive} not found"
            raise ValueError(msg)
        return primitives

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

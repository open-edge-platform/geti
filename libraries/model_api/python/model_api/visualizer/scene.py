"""Scene object."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
from typing import Type, Union

import PIL

from .layout import Layout
from .primitive import Primitive


class Scene:
    """Scene object.

    Used by the visualizer to render.
    """

    def __init__(
        self,
        base: PIL.Image,
        layout: Union[Layout, list[Layout], None] = None,
    ) -> None: ...

    def show(self) -> PIL.Image: ...

    def save(self, path: str) -> None: ...

    def has_primitives(self, primitive: Type[Primitive]) -> bool:
        return False

    def get_primitives(self, primitive: Type[Primitive]) -> list[Primitive]:
        return []

    @property
    @abstractmethod
    def default_layout(self) -> Layout:
        """Default layout for the media."""

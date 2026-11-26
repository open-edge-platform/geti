"""Visual Prompting Scene."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from model_api.models.result import VisualPromptingResult

from .scene import Scene


class VisualPromptingScene(Scene):
    """Visual Prompting Scene."""

    def __init__(self, result: VisualPromptingResult) -> None:
        self.result = result

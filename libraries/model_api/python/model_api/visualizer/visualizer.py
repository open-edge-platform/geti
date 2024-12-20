"""Visualizer for modelAPI."""

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import PIL

from model_api.models.result import Result


class Visualizer:
    def show(self, image: PIL.Image, result: Result) -> PIL.Image: ...

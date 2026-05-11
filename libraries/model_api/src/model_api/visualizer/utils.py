"""Visualizer utilities."""

from __future__ import annotations

from functools import lru_cache
from typing import Union

from PIL import Image, ImageDraw, ImageFont

# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

COLOR_PALETTE = [
    "#FF6B6B",  # Red
    "#4ECDC4",  # Teal
    "#45B7D1",  # Blue
    "#FFA07A",  # Light Salmon
    "#98D8C8",  # Mint
    "#F7DC6F",  # Yellow
    "#BB8FCE",  # Purple
    "#85C1E2",  # Sky Blue
    "#F8B739",  # Orange
    "#52BE80",  # Green
    "#EC7063",  # Coral
    "#5DADE2",  # Light Blue
    "#F39C12",  # Dark Orange
    "#8E44AD",  # Dark Purple
    "#16A085",  # Dark Teal
    "#E74C3C",  # Dark Red
    "#3498DB",  # Dodger Blue
    "#2ECC71",  # Emerald
    "#F1C40F",  # Sun Yellow
    "#E67E22",  # Carrot Orange
]


def get_label_color_mapping(labels: list[str]) -> dict[str, str]:
    """Generate a consistent color mapping for a list of labels.

    Args:
        labels: List of label names.

    Returns:
        Dictionary mapping each label to a hex color string.
    """
    unique_labels = sorted(set(labels))
    return {label: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, label in enumerate(unique_labels)}


@lru_cache(maxsize=5)
def default_font(size: int = 10):
    """Get the default font with the specified size using cache to store the object.

    Args:
        size: Font size.

    Returns:
        A PIL ImageFont instance with the default font and specified size.
    """
    return ImageFont.load_default(size=size)


@lru_cache(maxsize=5)
def truetype_font(font_path: str, size: int = 10):
    """Get a TrueType font from the specified path and size using cache to store the object.

    Args:
        font_path: Path to the .ttf font file.
        size: Font size.
    """

    return ImageFont.truetype(font_path, size)


def make_label_image(
    text: str,
    font: ImageFont.ImageFont,
    fg_color: Union[str, tuple[int, int, int]] = "black",
    bg_color: Union[str, tuple[int, int, int]] = "yellow",
) -> Image.Image:
    """Create a label image with uniform height based on font metrics.

    The height is derived from the font's ascent + descent so that all labels
    produced with the same font share the same background height regardless of
    the specific characters in *text*.  Text is drawn at a fixed baseline
    position so that adjacent labels align consistently.

    Args:
        text: The label string to render.
        font: PIL font instance.
        fg_color: Text colour.
        bg_color: Background colour.

    Returns:
        PIL Image containing the rendered label.
    """
    dummy = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy)
    ascent, descent = font.getmetrics()
    font_height = ascent + descent
    textbox = draw.textbbox((0, 0), text, font=font)
    label_w = textbox[2] - textbox[0]
    label_image = Image.new("RGB", (label_w, font_height), bg_color)
    draw = ImageDraw.Draw(label_image)
    draw.text((-textbox[0], 0), text, font=font, fill=fg_color)
    return label_image

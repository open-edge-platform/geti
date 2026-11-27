"""Visualizer utilities."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Union

from PIL import Image, ImageColor, ImageDraw, ImageFont

if TYPE_CHECKING:
    from collections.abc import Mapping

# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

Color = Union[str, tuple[int, int, int]]

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


def _is_valid_rgb_tuple(color: tuple) -> bool:
    """Check that a tuple is a valid ``(R, G, B)`` triplet.

    Args:
        color: Tuple to check.

    Returns:
        True when the tuple holds exactly three integers in the 0-255 range.
    """
    return len(color) == 3 and all(isinstance(channel, int) and 0 <= channel <= 255 for channel in color)


def to_rgb(color: Color) -> tuple[int, int, int]:
    """Normalize a colour to an ``(R, G, B)`` tuple.

    ``PIL.ImageColor.getrgb`` only accepts strings, so tuples are returned unchanged.

    Args:
        color: Colour string accepted by PIL (e.g. ``"#RRGGBB"`` or ``"red"``) or an
            ``(R, G, B)`` tuple of integers in the 0-255 range.

    Returns:
        The colour as an ``(R, G, B)`` tuple.
    """
    if isinstance(color, str):
        return ImageColor.getrgb(color)
    return color


def validate_label_colors(label_colors: Union[Mapping[str, Color], None]) -> dict[str, Color]:
    """Validate a mapping of label name to colour.

    Args:
        label_colors: Mapping of label name to a colour. Colours are either a string
            accepted by PIL (e.g. ``"#RRGGBB"`` or ``"red"``) or an ``(R, G, B)`` tuple
            of integers in the 0-255 range. ``None`` is treated as an empty mapping.

    Returns:
        A copy of the mapping as a plain dictionary. Empty when *label_colors* is None.

    Raises:
        ValueError: If any colour is not a valid colour string or RGB tuple.
    """
    if label_colors is None:
        return {}

    validated: dict[str, Color] = {}
    for label, color in label_colors.items():
        if isinstance(color, str):
            try:
                to_rgb(color)
            except ValueError as error:
                msg = f"Invalid color {color!r} for label {label!r}."
                raise ValueError(msg) from error
        elif not (isinstance(color, tuple) and _is_valid_rgb_tuple(color)):
            msg = (
                f"Invalid color {color!r} for label {label!r}. Expected a color string or "
                "a tuple of three integers in the 0-255 range."
            )
            raise ValueError(msg)
        validated[label] = color
    return validated


def get_label_color_mapping(
    labels: list[str],
    overrides: Union[Mapping[str, Color], None] = None,
) -> dict[str, Color]:
    """Generate a consistent color mapping for a list of labels.

    Args:
        labels: List of label names.
        overrides: Optional mapping of label name to colour. Entries whose label appears
            in *labels* replace the automatically assigned palette colour; other entries
            are ignored.

    Returns:
        Dictionary mapping each label to a colour.
    """
    unique_labels = sorted(set(labels))
    mapping: dict[str, Color] = {label: COLOR_PALETTE[i % len(COLOR_PALETTE)] for i, label in enumerate(unique_labels)}
    if overrides:
        mapping.update({label: color for label, color in overrides.items() if label in mapping})
    return mapping


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

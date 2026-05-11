"""Default visualization constants."""

# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Font sizes
DEFAULT_FONT_SIZE: int = 16
"""Default font size used for all text (labels, bounding boxes, overlays, keypoints)."""

# Line / outline widths
DEFAULT_OUTLINE_WIDTH: int = 2
"""Default outline width for bounding boxes and polygon contours."""

# Opacity
DEFAULT_OPACITY: float = 0.4
"""Default blend opacity for overlays and polygon fills."""

# Keypoint drawing
DEFAULT_KEYPOINT_SIZE: int = 3
"""Default radius (in pixels) for keypoint dots."""

# Scale baseline
SCALE_BASELINE: int = 1280
"""Longer-edge pixel count of 720p (landscape). Used as the denominator when
computing the auto-scale factor."""

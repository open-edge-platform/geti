# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from dataclasses import dataclass


@dataclass
class VideoPredictionProperties:
    """
    Stores the video prediction properties for the rest view
    """

    total_count: int
    total_requested_count: int
    start_frame: int | None = None
    end_frame: int | None = None
    requested_start_frame: int | None = None
    requested_end_frame: int | None = None

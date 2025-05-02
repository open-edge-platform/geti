# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the VideoAnnotationStatistics entity"""

from dataclasses import dataclass


@dataclass
class VideoAnnotationStatistics:
    """
    VideoAnnotationStatistics stores the number of annotated, partially annotated and unannotated frames of a video
    """

    annotated: int
    unannotated: int
    partially_annotated: int

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the Media entity"""

from sc_sdk.entities.image import Image
from sc_sdk.entities.video import VideoFrame

Media2D = Image | VideoFrame

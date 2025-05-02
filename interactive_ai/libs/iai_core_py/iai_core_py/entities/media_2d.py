# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the Media entity"""

from iai_core_py.entities.image import Image
from iai_core_py.entities.video import VideoFrame

Media2D = Image | VideoFrame

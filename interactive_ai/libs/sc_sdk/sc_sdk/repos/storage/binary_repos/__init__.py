# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

"""
This module implements the binary repositories
"""

from .code_deployment_binary_repo import CodeDeploymentBinaryRepo
from .image_binary_repo import ImageBinaryRepo
from .model_binary_repo import ModelBinaryRepo
from .tensor_binary_repo import TensorBinaryRepo
from .thumbnail_binary_repo import ThumbnailBinaryRepo
from .video_binary_repo import VideoBinaryRepo

__all__ = [
    "CodeDeploymentBinaryRepo",
    "ImageBinaryRepo",
    "ModelBinaryRepo",
    "TensorBinaryRepo",
    "ThumbnailBinaryRepo",
    "VideoBinaryRepo",
]

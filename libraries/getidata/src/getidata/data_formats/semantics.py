# Copyright (C) 2022-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
This module defines semantic tags for fields used in getidata's supported data formats. The semantics can be used to
ensure generic fields such as NumericField, BoolField, and StringField are kept when converting to specific data format
Sample schemas.
"""

# Dataset organization semantics
IMAGE_ID = "image_id"  # NumericField | stores the image id

# COCO semantics
AREAS = "areas"  # NumericField | stores the area of an annotation
ISCROWD = "iscrowd"  # BoolField | stores whether an annotation is a crowd
CAPTION_GROUP_IDS = "caption_group_ids"  # NumericField | stores group ids for captions to link multiple captions

# VOC semantics
DIFFICULT = "difficult"  # BoolField | stores whether an annotation is difficult to detect
TRUNCATED = "truncated"  # BoolField | stores whether an object is truncated (partially visible)
OCCLUDED = "occluded"  # BoolField | stores whether an object is occluded by another object
POSE = "pose"  # StringField | stores the pose of an object (e.g., "Left", "Right", "Frontal", "Rear")

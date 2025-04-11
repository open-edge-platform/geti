# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

from datetime import datetime, timezone

from sc_sdk.entities.annotation import AnnotationSceneKind


class DummyValues:
    MEDIA_HEIGHT = 480
    MEDIA_WIDTH = 640
    LABEL_NAMES = ["rectangle", "ellipse", "triangle"]
    CREATOR_NAME = "SC SDK Fixtures"
    CREATION_DATE = datetime.strptime("01/01/1970 00:00:01", "%d/%m/%Y %H:%M:%S").astimezone(timezone.utc)
    ANNOTATION_SCENE_KIND = AnnotationSceneKind.ANNOTATION
    ANNOTATION_EDITOR_NAME = "editor"
    MODIFICATION_DATE = datetime(2021, 7, 15, tzinfo=timezone.utc)
    X = 0.375
    Y = 0.25
    WIDTH = 0.25
    HEIGHT = 0.125
    UUID = "92497df6-f45a-11eb-9a03-0242ac130003"
    LABEL_PROBABILITY = 1.0
    LABEL_NAME = "dog"
    LABEL_HOTKEY = "ctrl+V"
    FRAME_INDEX = 0


class DefaultImageValues:
    IMAGE_WIDTH = 480
    IMAGE_HEIGTH = 640
    MIN_SHAPE_SIZE = 50
    MAX_SHAPE_SIZE = 250
    INTENSITY_RANGE = [(100, 200)]
    MAX_NUMBER_OF_SHAPES = 10
    ALLOWED_SHAPE_NAMES = ["rectangle", "ellipse", "triangle"]


class IDOffsets:
    WORKSPACE = 0
    DATASET_STORAGE = 1
    EMPTY_PROJECT = 2
    SINGLE_TASK_PROJECT = 3
    TASK_CHAIN_PROJECT = 4
    DATASET = 5
    HYPER_PARAMETERS = 6
    DATASET_TASK = 13
    CROP_TASK = 14
    CLASSIFICATION_TASK = 15
    DETECTION_TASK = 16
    SEGMENTATION_TASK = 17
    ANOMALY_CLASSIFICATION_TASK = 18
    EMTPY_LABEL_SCHEMA = 40
    CLASSIFICATION_LABEL_SCHEMA = 41
    DETECTION_LABEL_SCHEMA = 42
    SEGMENTATION_LABEL_SCHEMA = 43
    ROTATED_DETACTION_LABEL_SCHEMA = 44
    MODEL_TEST_JOB = 45
    CLASSIFICATION_LABELS = 50
    DETECTION_LABELS = 60
    SEGMENTATION_LABELS = 70
    ROTATED_DETECTION_LABELS = 80
    EMPTY_IMAGE = 100
    EMPTY_VIDEO = 120
    MODEL_TEST_RESULT = 140
    MEDIA_SCORE = 160
    ANOMALY_CLASSIFICATION_LABEL_SCHEMA = 200
    ANOMALY_SEGMENTATION_LABEL_SCHEMA = 201
    ANOMALY_DETECTION_LABEL_SCHEMA = 202
    KEYPOINT_DETECTION_LABEL_SCHEMA = 300

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import datetime

import numpy as np
import pytest

from geti_types import ID
from iai_core_py.entities.annotation import AnnotationSceneKind
from iai_core_py.entities.color import Color
from iai_core_py.entities.label import Domain


class DummyValues:
    X = 0.375
    Y = 0.25
    WIDTH = 0.25
    HEIGHT = 0.125
    UUID = "92497df6-f45a-11eb-9a03-0242ac130003"
    UUID_2 = "92497df6-f45a-11eb-9a03-0242ac130004"
    UUID_3 = "92497df6-f45a-11eb-9a03-0242ac130005"
    UUID_4 = "92497df6-f45a-11eb-9a03-0242ac130006"
    FRAME_INDEX = 42
    TOTAL_FRAMES = 5
    FRAME_SKIP = 2
    MODIFICATION_DATE_1 = datetime.datetime(2021, 7, 15)
    MODIFICATION_DATE_2 = datetime.datetime(2020, 9, 1)
    ANNOTATION_SCENE_KIND = AnnotationSceneKind.ANNOTATION
    ANNOTATION_EDITOR_NAME = "editor"
    LABEL_NAME = "dog"
    LABEL_PROBABILITY = 0.97
    DETECTION_DOMAIN = Domain.DETECTION
    CLASSIFICATION_DOMAIN = Domain.CLASSIFICATION
    SEGMENTATION_DOMAIN = Domain.SEGMENTATION
    ANOMALY_CLASSIFICATION_DOMAIN = Domain.ANOMALY_CLASSIFICATION
    LABEL_HOTKEY = "ctrl+V"
    LABEL_COLOR = Color.from_hex_str("#ff0000")
    DURATION_METRIC_AS_SECONDS = 1 * 3600 + 2 * 60 + 3
    DURATION_METRIC_AS_STRING = "1:02:03"
    DATE_METRIC_NAME = "test_date_metric"
    DATE_METRIC_AS_DATETIME = datetime.datetime(2020, 1, 1)
    DATE_METRIC_AS_STRING = "2020-01-01T00:00:00"
    CREATION_DATE = datetime.datetime(2021, 7, 15)
    CURVE_METRIC_NAME = "test_curve"
    CURVE_METRIC_X_VALUES = [0, 1, 2]
    CURVE_METRIC_Y_VALUES = [1, 5, 8]
    CURVE_METRIC_Y_VALUES_WITH_NAN = [float("nan"), 5, 8]
    CURVE_METRIC_Y_VALUES_AFTER_NAN = [0, 5, 8]
    MATRIX_METRIC_NAME = "test_matrix"
    MATRIX_METRIC_ROWS = ["row1", "row2", "row3"]
    MATRIX_METRIC_COLS = ["col1", "col2", "col3"]
    MATRIX_METRIC_VALUES = np.array([[4, 0, 1], [0, 3, 2], [1, 2, 2]])
    SCORE_METRIC_NAME = "test_score_metric"
    SCORE_METRIC_VALUE = 1.0
    COUNT_METRIC_NAME = "test_count_metric"
    COUNT_METRIC_VALUE = 3
    STRING_METRIC_NAME = "test_string_metric"
    STRING_METRIC_VALUE = "test_string_metric_value"
    METRICS_GROUP_NAME = "test_metrics_group"
    MEDIA_HEIGHT = 480
    MEDIA_WIDTH = 640
    OBJECT_SIZE_DISTRIBUTION = [(160, 60), (160, 60), (240, 300), (80, 30)]
    CLUSTER_CENTER = [160, 112]
    CLUSTER_WIDTH_HEIGHT = [113, 218]
    ASPECT_RATIO_THRESHOLD_TALL = 7.0
    ASPECT_RATIO_THRESHOLD_WIDE = 0.07
    DISTRIBUTION_TALL = 0
    DISTRIBUTION_BALANCED = 4
    DISTRIBUTION_WIDE = 0
    N_ALL_IMAGES = 5
    N_ALL_VIDEOS = 1
    N_ANNOTATED_IMAGES = 5
    N_ANNOTATED_FRAMES = 5
    N_ANNOTATED_VIDEOS = 1
    CREATOR_NAME = "Geti"


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


@pytest.fixture
def fxt_mongo_id():
    """
    Create a realistic MongoDB ID string for testing purposes.

    If you need multiple ones, call this fixture repeatedly with different arguments.
    """
    base_id: int = 0x60D31793D5F1FB7E6E3C1A4F

    def _build_id(offset: int = 0) -> str:
        return ID(str(hex(base_id + offset))[2:])

    yield _build_id

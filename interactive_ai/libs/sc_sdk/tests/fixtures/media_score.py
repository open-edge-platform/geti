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
import pytest

from sc_sdk.entities.media_score import MediaScore
from sc_sdk.entities.metrics import ScoreMetric

from .values import IDOffsets


@pytest.fixture
def fxt_media_score(fxt_ote_id, fxt_image_identifier):
    scores = {
        ScoreMetric(
            name="F-Measure",
            label_id=fxt_ote_id(IDOffsets.DETECTION_LABELS),
            value=0.6,
        ),
        ScoreMetric(
            name="F-Measure",
            label_id=None,
            value=0.6,
        ),
    }
    yield MediaScore(
        id_=fxt_ote_id(IDOffsets.MEDIA_SCORE),
        model_test_result_id=fxt_ote_id(IDOffsets.MODEL_TEST_RESULT),
        media_identifier=fxt_image_identifier,
        scores=scores,
    )


@pytest.fixture
def fxt_media_score_2(fxt_ote_id, fxt_image_identifier):
    scores = {
        ScoreMetric(
            name="F-Measure",
            label_id=fxt_ote_id(IDOffsets.DETECTION_LABELS),
            value=0.6,
        ),
        ScoreMetric(
            name="Dice",
            label_id=fxt_ote_id(IDOffsets.SEGMENTATION_LABELS),
            value=0.6,
        ),
    }
    yield MediaScore(
        id_=fxt_ote_id(IDOffsets.MEDIA_SCORE),
        model_test_result_id=fxt_ote_id(IDOffsets.MODEL_TEST_RESULT),
        media_identifier=fxt_image_identifier,
        scores=scores,
    )

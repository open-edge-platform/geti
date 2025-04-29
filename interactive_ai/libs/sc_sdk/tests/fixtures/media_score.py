# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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

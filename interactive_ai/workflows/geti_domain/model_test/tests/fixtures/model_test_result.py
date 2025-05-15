# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from iai_core.entities.metrics import MultiScorePerformance, ScoreMetric
from iai_core.entities.model_test_result import ModelTestResult, TestState

from tests.fixtures.values import IDOffsets


@pytest.fixture
def fxt_model_test_result(fxt_ote_id, fxt_mongo_id, fxt_empty_project, fxt_model, fxt_dataset_storage):
    performance = MultiScorePerformance(
        additional_scores=[
            ScoreMetric(name="F-Measure", value=0.7),
            ScoreMetric(name="Precision", value=0.6),
            ScoreMetric(name="Recall", value=0.8),
            ScoreMetric(name="F-Measure", value=0.9, label_id=fxt_ote_id(1000)),
            ScoreMetric(name="F-Measure", value=0.5, label_id=fxt_ote_id(1001)),
        ]
    )
    yield ModelTestResult(
        id_=fxt_ote_id(IDOffsets.MODEL_TEST_RESULT),
        name="test",
        project_identifier=fxt_empty_project.identifier,
        model_storage_id=fxt_model.model_storage.id_,
        model_id=fxt_model.id_,
        dataset_storage_ids=[fxt_dataset_storage.id_],
        job_id=fxt_ote_id(1),
        ground_truth_dataset=fxt_mongo_id(2),
        prediction_dataset=fxt_mongo_id(3),
        state=TestState.DONE,
        performance=performance,
    )

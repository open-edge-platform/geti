# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from iai_core_py.entities.evaluation_result import EvaluationResult
from iai_core_py.entities.metrics import Performance, ScoreMetric


@pytest.fixture
def fxt_performance():
    yield Performance(score=ScoreMetric(name="score", value=1))


@pytest.fixture
def fxt_evaluation_result(fxt_mongo_id, fxt_performance, fxt_project_identifier):
    yield EvaluationResult(
        id_=fxt_mongo_id(0),
        project_identifier=fxt_project_identifier,
        model_storage_id=fxt_mongo_id(2),
        model_id=fxt_mongo_id(3),
        dataset_storage_id=fxt_mongo_id(4),
        ground_truth_dataset=fxt_mongo_id(5),
        prediction_dataset=fxt_mongo_id(6),
        performance=fxt_performance,
    )

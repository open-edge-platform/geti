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
import copy

import pytest

from tests.fixtures.values import DummyValues, IDOffsets

from sc_sdk.entities.dataset_storage import NullDatasetStorage
from sc_sdk.entities.metrics import MultiScorePerformance, ScoreMetric
from sc_sdk.entities.model_test_result import ModelTestResult, TestState


@pytest.fixture
def fxt_model_test_result(fxt_mongo_id, fxt_project_identifier, fxt_model, fxt_dataset_storage):
    performance = MultiScorePerformance(
        additional_scores=[
            ScoreMetric(name="F-Measure", value=0.5, label_id=None),
            ScoreMetric(name="F-Measure", value=0.5, label_id=fxt_mongo_id(4)),
        ]
    )
    yield ModelTestResult(
        id_=fxt_mongo_id(IDOffsets.MODEL_TEST_RESULT),
        name="test",
        project_identifier=fxt_project_identifier,
        model_storage_id=fxt_model.model_storage.id_,
        model_id=fxt_model.id_,
        dataset_storage_ids=[fxt_dataset_storage.id_],
        job_id=fxt_mongo_id(1),
        ground_truth_dataset=fxt_mongo_id(2),
        prediction_dataset=fxt_mongo_id(3),
        state=TestState.DONE,
        performance=performance,
        creation_date=DummyValues.CREATION_DATE,
    )


@pytest.fixture
def fxt_model_test_result_with_accuracy_metric(fxt_mongo_id, fxt_project_identifier, fxt_model, fxt_dataset_storage):
    performance = MultiScorePerformance(
        additional_scores=[
            ScoreMetric(name="Accuracy", value=0.5, label_id=None),
            ScoreMetric(name="Accuracy", value=0.5, label_id=fxt_mongo_id(4)),
        ]
    )
    yield ModelTestResult(
        id_=fxt_mongo_id(IDOffsets.MODEL_TEST_RESULT),
        name="test",
        project_identifier=fxt_project_identifier,
        model_storage_id=fxt_model.model_storage.id_,
        model_id=fxt_model.id_,
        dataset_storage_ids=[fxt_dataset_storage.id_],
        job_id=fxt_mongo_id(1),
        ground_truth_dataset=fxt_mongo_id(2),
        prediction_dataset=fxt_mongo_id(3),
        state=TestState.DONE,
        performance=performance,
        creation_date=DummyValues.CREATION_DATE,
    )


@pytest.fixture
def fxt_model_test_result_deleted_ds(fxt_mongo_id, fxt_project_identifier, fxt_model):
    performance = MultiScorePerformance(
        additional_scores=[
            ScoreMetric(name="F-Measure", value=0.5, label_id=None),
            ScoreMetric(name="F-Measure", value=0.5, label_id=fxt_mongo_id(4)),
        ]
    )
    yield ModelTestResult(
        id_=fxt_mongo_id(IDOffsets.MODEL_TEST_RESULT),
        name="test",
        project_identifier=fxt_project_identifier,
        model_storage_id=fxt_model.model_storage.id_,
        model_id=fxt_model.id_,
        dataset_storage_ids=[NullDatasetStorage().id_],
        job_id=fxt_mongo_id(1),
        ground_truth_dataset=fxt_mongo_id(2),
        prediction_dataset=fxt_mongo_id(3),
        state=TestState.DONE,
        performance=performance,
        creation_date=DummyValues.CREATION_DATE,
    )


@pytest.fixture
def fxt_broken_model_test_result(fxt_model_test_result):
    broken_model_test_result = copy.deepcopy(fxt_model_test_result)
    broken_model_test_result.ground_truth_dataset_id = None
    broken_model_test_result.prediction_dataset_id = None
    yield broken_model_test_result


@pytest.fixture
def fxt_model_test_result_rest(fxt_model_test_result, fxt_mongo_id):
    return {
        "id": str(fxt_model_test_result.id_),
        "name": fxt_model_test_result.name,
        "creation_time": fxt_model_test_result.creation_date.isoformat(),
        "job_info": {"id": fxt_model_test_result.job_id, "status": "DONE"},
        "model_info": {
            "group_id": fxt_model_test_result.model_id,
            "id": fxt_model_test_result.model_id,
            "template_id": "test_template_dataset",
            "optimization_type": "NONE",
            "task_id": "60d31793d5f1fb7e6e3c1a59",
            "task_type": "DATASET",
            "n_labels": 1,
            "precision": ["FP32"],
            "version": 1,
        },
        "datasets_info": [
            {
                "id": "60d31793d5f1fb7e6e3c1a52",
                "is_deleted": False,
                "name": "dummy_dataset_storage",
                "n_images": 10,
                "n_frames": 5,
                "n_samples": 15,
            }
        ],
        "scores": [
            {"name": "F-measure", "value": 0.5, "label_id": fxt_mongo_id(4)},
            {"name": "F-measure", "value": 0.5, "label_id": None},
        ],
    }


@pytest.fixture
def fxt_model_test_result_with_accuracy_metric_rest(fxt_model_test_result, fxt_mongo_id):
    return {
        "id": str(fxt_model_test_result.id_),
        "name": fxt_model_test_result.name,
        "creation_time": fxt_model_test_result.creation_date.isoformat(),
        "job_info": {"id": fxt_model_test_result.job_id, "status": "DONE"},
        "model_info": {
            "group_id": fxt_model_test_result.model_id,
            "id": fxt_model_test_result.model_id,
            "template_id": "test_template_dataset",
            "optimization_type": "NONE",
            "task_id": "60d31793d5f1fb7e6e3c1a59",
            "task_type": "DATASET",
            "n_labels": 1,
            "precision": ["FP32"],
            "version": 1,
        },
        "datasets_info": [
            {
                "id": "60d31793d5f1fb7e6e3c1a52",
                "is_deleted": False,
                "name": "dummy_dataset_storage",
                "n_images": 10,
                "n_frames": 5,
                "n_samples": 15,
            }
        ],
        "scores": [
            {"name": "Accuracy", "value": 0.5, "label_id": fxt_mongo_id(4)},
            {"name": "Accuracy", "value": 0.5, "label_id": None},
        ],
    }


@pytest.fixture
def fxt_model_test_results_rest(fxt_model_test_result_rest):
    return {
        "test_results": [
            fxt_model_test_result_rest,
            fxt_model_test_result_rest,
        ]
    }

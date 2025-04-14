# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import pytest

from tests.fixtures.values import DummyValues, IDOffsets

from sc_sdk.entities.dataset_storage import NullDatasetStorage
from sc_sdk.entities.metrics import MultiScorePerformance, ScoreMetric
from sc_sdk.entities.model_test_result import ModelTestResult, TestState


@pytest.fixture
def fxt_model_test_result(fxt_ote_id, fxt_mongo_id, fxt_project_identifier, fxt_model, fxt_dataset_storage):
    performance = MultiScorePerformance(
        additional_scores=[
            ScoreMetric(name="F-Measure", value=0.5, label_id=None),
            ScoreMetric(name="F-Measure", value=0.5, label_id=fxt_ote_id(4)),
        ]
    )
    yield ModelTestResult(
        id_=fxt_ote_id(IDOffsets.MODEL_TEST_RESULT),
        name="test",
        project_identifier=fxt_project_identifier,
        model_storage_id=fxt_model.model_storage.id_,
        model_id=fxt_model.id_,
        dataset_storage_ids=[fxt_dataset_storage.id_],
        job_id=fxt_ote_id(1),
        ground_truth_dataset=fxt_mongo_id(2),
        prediction_dataset=fxt_mongo_id(3),
        state=TestState.DONE,
        performance=performance,
        creation_date=DummyValues.CREATION_DATE,
    )


@pytest.fixture
def fxt_model_test_result_with_accuracy_metric(
    fxt_ote_id, fxt_mongo_id, fxt_project_identifier, fxt_model, fxt_dataset_storage
):
    performance = MultiScorePerformance(
        additional_scores=[
            ScoreMetric(name="Accuracy", value=0.5, label_id=None),
            ScoreMetric(name="Accuracy", value=0.5, label_id=fxt_ote_id(4)),
        ]
    )
    yield ModelTestResult(
        id_=fxt_ote_id(IDOffsets.MODEL_TEST_RESULT),
        name="test",
        project_identifier=fxt_project_identifier,
        model_storage_id=fxt_model.model_storage.id_,
        model_id=fxt_model.id_,
        dataset_storage_ids=[fxt_dataset_storage.id_],
        job_id=fxt_ote_id(1),
        ground_truth_dataset=fxt_mongo_id(2),
        prediction_dataset=fxt_mongo_id(3),
        state=TestState.DONE,
        performance=performance,
        creation_date=DummyValues.CREATION_DATE,
    )


@pytest.fixture
def fxt_model_test_result_deleted_ds(fxt_ote_id, fxt_project_identifier, fxt_mongo_id, fxt_model):
    performance = MultiScorePerformance(
        additional_scores=[
            ScoreMetric(name="F-Measure", value=0.5, label_id=None),
            ScoreMetric(name="F-Measure", value=0.5, label_id=fxt_ote_id(4)),
        ]
    )
    yield ModelTestResult(
        id_=fxt_ote_id(IDOffsets.MODEL_TEST_RESULT),
        name="test",
        project_identifier=fxt_project_identifier,
        model_storage_id=fxt_model.model_storage.id_,
        model_id=fxt_model.id_,
        dataset_storage_ids=[NullDatasetStorage().id_],
        job_id=fxt_ote_id(1),
        ground_truth_dataset=fxt_mongo_id(2),
        prediction_dataset=fxt_mongo_id(3),
        state=TestState.DONE,
        performance=performance,
        creation_date=DummyValues.CREATION_DATE,
    )


@pytest.fixture
def fxt_model_test_result_rest(fxt_model_test_result, fxt_ote_id):
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
            {"name": "F-measure", "value": 0.5, "label_id": fxt_ote_id(4)},
            {"name": "F-measure", "value": 0.5, "label_id": None},
        ],
    }


@pytest.fixture
def fxt_model_test_result_with_accuracy_metric_rest(fxt_model_test_result, fxt_ote_id):
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
            {"name": "Accuracy", "value": 0.5, "label_id": fxt_ote_id(4)},
            {"name": "Accuracy", "value": 0.5, "label_id": None},
        ],
    }


@pytest.fixture
def fxt_model_test_result_deleted_ds_rest():
    return {
        "id": "60d31793d5f1fb7e6e3c1adb",
        "name": "test",
        "creation_time": "2022-08-05T12:50:10.525000+00:00",
        "job_info": {"id": "60d31793d5f1fb7e6e3c1a50", "status": "DONE"},
        "model_info": {
            "group_id": "60d31793d5f1fb7e6e3c1a50",
            "id": "60d31793d5f1fb7e6e3c1a50",
            "template_id": "test_template_dataset",
            "task_id": "60d31793d5f1fb7e6e3c1a59",
            "task_type": "DATASET",
            "optimization_type": "NONE",
            "n_labels": 1,
            "precision": ["FP32"],
            "version": 1,
        },
        "datasets_info": [
            {
                "id": "",
                "is_deleted": True,
                "name": "",
                "n_images": 0,
                "n_frames": 0,
                "n_samples": 0,
            }
        ],
        "scores": [{"name": "F_measure", "value": 0.5, "label_id": None}],
    }


@pytest.fixture
def fxt_model_test_results_rest(fxt_model_test_result_rest):
    return {
        "test_results": [
            fxt_model_test_result_rest,
            fxt_model_test_result_rest,
        ]
    }

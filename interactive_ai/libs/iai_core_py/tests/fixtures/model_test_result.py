# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import copy
from random import choice, randint, random, sample, uniform

import pytest

from iai_core.entities.annotation import Annotation
from iai_core.entities.datasets import Dataset
from iai_core.entities.metrics import AnomalyLocalizationPerformance, MultiScorePerformance, ScoreMetric
from iai_core.entities.model_test_result import ModelTestResult, TestState
from iai_core.entities.scored_label import ScoredLabel
from iai_core.entities.shapes import Rectangle

from .values import IDOffsets


@pytest.fixture
def fxt_model_test_result(fxt_ote_id, fxt_mongo_id, fxt_empty_project, fxt_model, fxt_dataset_storage, fxt_dataset):
    performance = MultiScorePerformance(
        primary_score=ScoreMetric(name="Accuracy", value=0.7),
        additional_scores=[
            ScoreMetric(name="F-Measure", value=0.7),
            ScoreMetric(name="Precision", value=0.6),
            ScoreMetric(name="Recall", value=0.8),
            ScoreMetric(name="F-Measure", value=0.9, label_id=fxt_ote_id(1000)),
            ScoreMetric(name="F-Measure", value=0.5, label_id=fxt_ote_id(1001)),
        ],
    )
    ground_truth_dataset = copy.deepcopy(fxt_dataset)
    ground_truth_dataset.id_ = fxt_mongo_id(2)
    prediction_dataset = copy.deepcopy(fxt_dataset)
    prediction_dataset.id_ = fxt_mongo_id(3)
    yield ModelTestResult(
        id_=fxt_ote_id(IDOffsets.MODEL_TEST_RESULT),
        name="test",
        project_identifier=fxt_empty_project.identifier,
        model_storage_id=fxt_model.model_storage.id_,
        model_id=fxt_model.id_,
        dataset_storage_ids=[fxt_dataset_storage.id_],
        job_id=fxt_ote_id(1),
        ground_truth_dataset=ground_truth_dataset,
        prediction_dataset=prediction_dataset,
        state=TestState.DONE,
        performance=performance,
    )


@pytest.fixture
def fxt_model_test_result_anomaly_local_score(
    fxt_ote_id, fxt_mongo_id, fxt_empty_project, fxt_model, fxt_dataset_storage, fxt_dataset
):
    ground_truth_dataset = copy.deepcopy(fxt_dataset)
    ground_truth_dataset.id_ = fxt_mongo_id(2)
    prediction_dataset = copy.deepcopy(fxt_dataset)
    prediction_dataset.id_ = fxt_mongo_id(3)
    performance = AnomalyLocalizationPerformance(
        global_score=ScoreMetric(name="Accuracy", value=0.7),
        local_score=ScoreMetric(name="F-Measure", value=0.7),
        dashboard_metrics=[],
    )
    performance = performance.as_multi_score_performance()
    yield ModelTestResult(
        id_=fxt_ote_id(IDOffsets.MODEL_TEST_RESULT + 1),
        name="test_anomaly_local_score",
        project_identifier=fxt_empty_project.identifier,
        model_storage_id=fxt_model.model_storage.id_,
        model_id=fxt_model.id_,
        dataset_storage_ids=[fxt_dataset_storage.id_],
        job_id=fxt_ote_id(1),
        ground_truth_dataset=ground_truth_dataset,
        prediction_dataset=prediction_dataset,
        state=TestState.DONE,
        performance=performance,
    )


@pytest.fixture
def fxt_broken_model_test_result(fxt_model_test_result):
    broken_model_test_result = copy.deepcopy(fxt_model_test_result)
    broken_model_test_result.ground_truth_dataset_id = None
    broken_model_test_result.prediction_dataset_id = None
    yield broken_model_test_result


@pytest.fixture
def fxt_model_test_result_rest():
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
            "n_labels": 1,
            "precision": ["FP32"],
            "version": 1,
        },
        "datasets_info": [
            {
                "id": "60d31793d5f1fb7e6e3c1a4f",
                "is_deleted": False,
                "name": "dummy_dataset_storage",
                "n_images": 10,
                "n_frames": 5,
                "n_samples": 15,
            }
        ],
        "scores": [{"name": "F-measure", "value": 0.5, "label_id": None}],
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
def fxt_prediction_dataset_classification(fxt_ground_truth_dataset_classification):
    """
    Prediction dataset for classification tasks
    - same number of items (10) of ground truth dataset
    - same 4 labels of ground truth dataset
    - if i is even, keep the same labels
    - if i is odd, randomize the labels
    """
    prediction_dataset: Dataset = copy.deepcopy(fxt_ground_truth_dataset_classification)
    labels = prediction_dataset.get_labels()
    for i, item in enumerate(prediction_dataset):
        if i % 2 == 1:
            scored_labels = [
                ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=1.0)
                for label in sample(labels, randint(1, 4))
            ]
            item.annotation_scene.annotations[0].set_labels(scored_labels)
    yield prediction_dataset


@pytest.fixture
def fxt_ground_truth_dataset_detection(
    fxt_mongo_id,
    fxt_dataset_item,
    fxt_detection_label_factory,
    fxt_annotation_scene,
    fxt_empty_detection_label,
):
    """
    Ground truth dataset for detection tasks
    - 10 items
    - 4 labels
    - dataset item i includes i annotations with random shapes and labels
    """
    items = []
    labels = [fxt_detection_label_factory(i) for i in range(4)]
    for i in range(10):
        item = fxt_dataset_item(i)
        annotations = []
        for _j in range(i):
            x1, y1 = random(), random()
            x2, y2 = uniform(x1, 1.0), uniform(y1, 1.0)
            rectangle = Rectangle(x1, y1, x2, y2)
            label = choice(labels)
            scored_label = ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=1.0)
            annotation = Annotation(shape=rectangle, labels=[scored_label])
            annotations.append(annotation)
        if len(annotations) == 0:  # add empty label
            rectangle = Rectangle(0, 0, 1, 1)
            scored_label = ScoredLabel(label_id=fxt_empty_detection_label.id_, is_empty=True, probability=1.0)
            annotation = Annotation(shape=rectangle, labels=[scored_label])
            annotations.append(annotation)
        item.annotation_scene = copy.deepcopy(fxt_annotation_scene)
        item.annotation_scene.annotations = annotations
        items.append(item)

    yield Dataset(items=items, id=fxt_mongo_id(1))


@pytest.fixture
def fxt_prediction_dataset_detection(fxt_ground_truth_dataset_detection, fxt_dataset_item, fxt_annotation_scene):
    """
    Prediction dataset for detection tasks
    - same number of items (10) of ground truth dataset
    - same 4 labels of ground truth dataset
    - if i is even, includes same annotations from ground truth dataset
    - if i is odd, applies one of these operations randomly for each annotation
        - remove annotation
        - duplicate annotation
        - leave annotation unchanged and add full-box annotation
    """
    pred_items = []
    labels = fxt_ground_truth_dataset_detection.get_labels()
    for i, gt_item in enumerate(fxt_ground_truth_dataset_detection):
        pred_item = fxt_dataset_item(100 + i)
        if i % 2 == 1:  # odd-indexed dataset items
            pred_annotations = []
            for annotation in gt_item.annotation_scene.annotations:
                c = choice([1, 2, 3])
                if c == 1:  # remove
                    pass
                elif c == 2:  # duplicate
                    pred_annotations.append(annotation)
                elif c == 3:  # keep and add full-box
                    pred_annotations.append(annotation)
                    label = choice(labels)
                    pred_annotations.append(
                        Annotation(
                            Rectangle(0.0, 0.0, 1.0, 1.0),
                            [ScoredLabel(label_id=label.id_, is_empty=label.is_empty, probability=0.7)],
                        )
                    )
        else:  # even-indexed dataset items
            pred_annotations = gt_item.annotation_scene.annotations
        pred_item.annotation_scene = copy.deepcopy(fxt_annotation_scene)
        pred_item.annotation_scene.annotations = pred_annotations
        pred_items.append(pred_item)
    yield pred_items


@pytest.fixture
def fxt_ground_truth_dataset_segmentation(fxt_ground_truth_dataset_detection):
    # Reuse 'detection' fixture since bounding boxes are compatible with 'segmentation'
    yield fxt_ground_truth_dataset_detection


@pytest.fixture
def fxt_prediction_dataset_segmentation(fxt_prediction_dataset_detection):
    # Reuse 'detection' fixture since bounding boxes are compatible with 'segmentation'
    yield fxt_prediction_dataset_detection

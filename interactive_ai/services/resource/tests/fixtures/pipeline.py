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

import pytest


@pytest.fixture
def fxt_detection_crop_classification_pipeline_data():
    yield {
        "connections": [
            {"from": "Dataset", "to": "Detection task"},
            {"from": "Detection task", "to": "Crop task"},
            {"from": "Crop task", "to": "Classification task"},
        ],
        "tasks": [
            {"task_type": "dataset", "title": "Dataset"},
            {
                "task_type": "detection",
                "title": "Detection task",
                "labels": [
                    {
                        "name": "dog",
                        "color": "#ffffff",
                        "group": "Default Detection",
                        "parent_id": None,
                        "hotkey": "crtl+0",
                    }
                ],
            },
            {"task_type": "crop", "title": "Crop task"},
            {
                "task_type": "classification",
                "title": "Classification task",
                "labels": [
                    {
                        "name": "small",
                        "color": "#fffffe",
                        "group": "Default Classification",
                        "parent_id": "dog",
                        "hotkey": "crtl+1",
                    },
                    {
                        "name": "large",
                        "color": "#fffffd",
                        "group": "Default Classification",
                        "parent_id": "dog",
                        "hotkey": "crtl+2",
                    },
                ],
            },
        ],
    }


@pytest.fixture
def fxt_detection_crop_classification_data(
    fxt_detection_crop_classification_pipeline_data,
):
    yield {
        "name": "TEST_dog_detection_crop_small_large_classification_rest_data",
        "pipeline": fxt_detection_crop_classification_pipeline_data,
    }


@pytest.fixture
def fxt_anomaly_classification_pipeline_data():
    pipeline = {
        "connections": [{"from": "Dataset", "to": "Anomaly task"}],
        "tasks": [
            {"task_type": "dataset", "title": "Dataset"},
            {"title": "Anomaly task", "task_type": "anomaly_classification"},
        ],
    }
    yield pipeline


@pytest.fixture
def fxt_detection_pipeline_data():
    yield {
        "connections": [{"from": "Dataset", "to": "Detection task"}],
        "tasks": [
            {"task_type": "dataset", "title": "Dataset"},
            {
                "title": "Detection task",
                "task_type": "detection",
                "model_template_id": "detection",
                "labels": [
                    {
                        "name": "detect_me",
                        "color": "#fffffe",
                        "group": "Default Detection",
                        "parent_id": None,
                        "hotkey": "crtl+1",
                    },
                ],
            },
        ],
    }


@pytest.fixture
def fxt_rotated_detection_pipeline_data():
    yield {
        "connections": [{"from": "Dataset", "to": "Rotated detection task"}],
        "tasks": [
            {"task_type": "dataset", "title": "Dataset"},
            {
                "title": "Rotated detection task",
                "task_type": "rotated_detection",
                "model_template_id": "rotated_detection",
                "labels": [
                    {
                        "name": "detect_me",
                        "color": "#fffffe",
                        "group": "Default Rotated detection",
                        "parent_id": None,
                        "hotkey": "crtl+1",
                    },
                ],
            },
        ],
    }


@pytest.fixture
def fxt_segmentation_pipeline_data():
    yield {
        "connections": [{"from": "Dataset", "to": "Segmentation task"}],
        "tasks": [
            {"task_type": "dataset", "title": "Dataset"},
            {
                "title": "Segmentation task",
                "task_type": "segmentation",
                "model_template_id": "segmentation",
                "labels": [
                    {
                        "name": "segment_me",
                        "color": "#fffffe",
                        "group": "Default Segmentation",
                        "parent_id": None,
                        "hotkey": "crtl+1",
                    },
                ],
            },
        ],
    }


@pytest.fixture
def fxt_instance_segmentation_pipeline_data():
    yield {
        "connections": [{"from": "Dataset", "to": "Instance segmentation task"}],
        "tasks": [
            {"task_type": "dataset", "title": "Dataset"},
            {
                "title": "Instance segmentation task",
                "task_type": "instance_segmentation",
                "model_template_id": "instance_segmentation",
                "labels": [
                    {
                        "name": "segment_me",
                        "color": "#fffffe",
                        "group": "Default Instance segmentation",
                        "parent_id": None,
                        "hotkey": "crtl+1",
                    },
                ],
            },
        ],
    }


@pytest.fixture
def fxt_binary_classification_pipeline_data():
    yield {
        "connections": [{"from": "Dataset", "to": "Classification task"}],
        "tasks": [
            {"task_type": "dataset", "title": "Dataset"},
            {
                "title": "Classification task",
                "task_type": "classification",
                "model_template_id": "classification",
                "labels": [
                    {
                        "name": "small",
                        "color": "#fffffe",
                        "group": "Default Classification",
                        "parent_id": None,
                        "hotkey": "crtl+1",
                    },
                ],
            },
        ],
    }


@pytest.fixture
def fxt_multiclass_classification_pipeline_data():
    yield {
        "connections": [{"from": "Dataset", "to": "Classification task"}],
        "tasks": [
            {"task_type": "dataset", "title": "Dataset"},
            {
                "title": "Classification task",
                "task_type": "classification",
                "model_template_id": "classification",
                "labels": [
                    {
                        "name": "small",
                        "color": "#fffffe",
                        "group": "Default Classification",
                        "parent_id": None,
                        "hotkey": "crtl+1",
                    },
                    {
                        "name": "large",
                        "color": "#fffffe",
                        "group": "Default Classification",
                        "parent_id": None,
                        "hotkey": "crtl+2",
                    },
                    {
                        "name": "quite small",
                        "color": "#fffffe",
                        "group": "small group",
                        "parent_id": "small",
                        "hotkey": "crtl+3",
                    },
                    {
                        "name": "tiny",
                        "color": "#eefffe",
                        "group": "small group",
                        "parent_id": "small",
                        "hotkey": "crtl+4",
                    },
                ],
            },
        ],
    }


@pytest.fixture
def fxt_multilabel_classification_pipeline_data():
    yield {
        "connections": [{"from": "Dataset", "to": "Classification task"}],
        "tasks": [
            {"task_type": "dataset", "title": "Dataset"},
            {
                "title": "Classification task",
                "task_type": "classification",
                "model_template_id": "classification",
                "labels": [
                    {
                        "name": "small",
                        "color": "#fffffe",
                        "group": "Default Classification",
                        "parent_id": None,
                        "hotkey": "crtl+1",
                    },
                    {
                        "name": "large",
                        "color": "#fffffe",
                        "group": "large group",
                        "parent_id": None,
                        "hotkey": "crtl+2",
                    },
                    {
                        "name": "really large",
                        "color": "#fffffe",
                        "group": "really large group",
                        "parent_id": None,
                        "hotkey": "crtl+3",
                    },
                    {
                        "name": "really extremely large",
                        "color": "#feeeee",
                        "group": "really large group",
                        "parent_id": "really large",
                        "hotkey": "crtl+4",
                    },
                    {
                        "name": "simply huuuge",
                        "color": "#effffe",
                        "group": "really large group",
                        "parent_id": "really large",
                        "hotkey": "crtl+5",
                    },
                ],
            },
        ],
    }


@pytest.fixture
def fxt_pipeline_with_label_hierarchy():
    yield {
        "connections": [
            {"from": "Dataset", "to": "Segmentation task"},
            {"from": "Segmentation task", "to": "Crop task"},
            {"from": "Crop task", "to": "Classification task"},
        ],
        "tasks": [
            {"task_type": "dataset", "title": "Dataset"},
            {
                "task_type": "segmentation",
                "title": "Segmentation task",
                "model_template_id": "segmentation",
                "labels": [
                    {
                        "name": "dog",
                        "color": "#ffffff",
                        "group": "Default Segmentation",
                        "parent_id": None,
                        "hotkey": "crtl+0",
                    },
                    {
                        "name": "cat",
                        "color": "#ff0000",
                        "group": "Default Segmentation",
                        "parent_id": None,
                        "hotkey": "crtl+1",
                    },
                ],
            },
            {"task_type": "crop", "title": "Crop task"},
            {
                "task_type": "classification",
                "title": "Classification task",
                "model_template_id": "classification",
                "labels": [
                    {
                        "name": "big dog",
                        "color": "#fffffe",
                        "group": "Dog",
                        "parent_id": "dog",
                        "hotkey": "crtl+2",
                    },
                    {
                        "name": "small dog",
                        "color": "#fffffc",
                        "group": "Dog",
                        "parent_id": "dog",
                        "hotkey": "crtl+3",
                    },
                    {
                        "name": "big cat",
                        "color": "#fffffd",
                        "group": "Cat",
                        "parent_id": "cat",
                        "hotkey": "crtl+4",
                    },
                    {
                        "name": "small cat",
                        "color": "#fffffb",
                        "group": "Cat",
                        "parent_id": "cat",
                        "hotkey": "crtl+5",
                    },
                ],
            },
        ],
    }


@pytest.fixture
def fxt_pipeline_detection_to_segmentation():
    yield {
        "connections": [
            {"from": "Dataset", "to": "Detection task"},
            {"from": "Detection task", "to": "Crop task"},
            {"from": "Crop task", "to": "Segmentation task"},
        ],
        "tasks": [
            {"task_type": "dataset", "title": "Dataset"},
            {
                "task_type": "detection",
                "title": "Detection task",
                "model_template_id": "detection",
                "labels": [
                    {
                        "name": "car",
                        "color": "#ffffff",
                        "group": "Default Detection",
                        "parent_id": None,
                        "hotkey": "crtl+0",
                    }
                ],
            },
            {"task_type": "crop", "title": "Crop task"},
            {
                "task_type": "segmentation",
                "title": "Segmentation task",
                "model_template_id": "segmentation",
                "labels": [
                    {
                        "name": "car wheel",
                        "color": "#fffffe",
                        "group": "Default Segmentation",
                        "parent_id": None,
                        "hotkey": "crtl+2",
                    },
                    {
                        "name": "car window",
                        "color": "#fffffc",
                        "group": "Default Segmentation",
                        "parent_id": None,
                        "hotkey": "crtl+3",
                    },
                ],
            },
        ],
    }

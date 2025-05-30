# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import contextlib
from typing import Any

import pytest
from _pytest.fixtures import FixtureRequest
from jsonschema.exceptions import ValidationError

from communication.exceptions import (
    BadNumberOfConnectionsException,
    BadNumberOfLabelsException,
    DuplicateHotkeysException,
    DuplicateLabelNamesException,
    DuplicateTaskNamesException,
    EmptyProjectNameException,
    InvalidLabelDeletedException,
    MismatchingParentsInLabelGroupException,
    MultiTaskLabelGroupException,
    NoTasksConnectionsException,
    NoTasksInProjectException,
    ParentLabelNotFoundException,
    ReservedLabelNameException,
    SelfReferencingParentLabelException,
    TooManyTasksException,
    UnconnectedTasksException,
    UnsupportedHierarchicalLabelsException,
)
from communication.rest_data_validator import ProjectRestValidator
from features.feature_flags import FeatureFlag


@pytest.fixture
def fxt_create_dataset_task_rest():
    yield {"title": "Dataset task", "task_type": "dataset"}


@pytest.fixture
def fxt_update_dataset_task_rest(fxt_create_dataset_task_rest, fxt_mongo_id):
    fxt_create_dataset_task_rest["id"] = fxt_mongo_id(1)
    yield fxt_create_dataset_task_rest


@pytest.fixture
def fxt_create_crop_task_rest():
    yield {"title": "Crop task", "task_type": "crop"}


@pytest.fixture
def fxt_update_crop_task_rest(fxt_create_crop_task_rest, fxt_mongo_id):
    fxt_create_crop_task_rest["id"] = fxt_mongo_id(2)
    fxt_create_crop_task_rest["title"] = "Updated crop task"
    yield fxt_create_crop_task_rest


@pytest.fixture
def fxt_create_detection_task_rest():
    yield {
        "title": "Detection task",
        "task_type": "detection",
        "labels": [{"name": "dummy_object"}],
    }


@pytest.fixture
def fxt_create_segmentation_task_rest():
    yield {
        "title": "Segmentation task",
        "task_type": "segmentation",
        "labels": [{"name": "dummy_object"}],
    }


@pytest.fixture
def fxt_create_detection_task_rest_with_hotkey():
    yield {
        "title": "Detection task",
        "task_type": "detection",
        "labels": [{"name": "dummy_object", "hotkey": 1}],
    }


@pytest.fixture
def fxt_update_detection_task_rest(fxt_create_detection_task_rest, fxt_mongo_id):
    fxt_create_detection_task_rest["id"] = fxt_mongo_id(3)
    fxt_create_detection_task_rest["labels"]: list[dict[str, Any]] = [
        {"name": "dummy_object", "id": fxt_mongo_id(4), "color": "#000000"},
        {"name": "new_label", "color": "#000001", "id": fxt_mongo_id(0)},
    ]
    yield fxt_create_detection_task_rest


@pytest.fixture
def fxt_create_classification_task_rest():
    yield {
        "title": "Classification task",
        "task_type": "classification",
        "labels": [{"name": "object_a"}, {"name": "object_b"}, {"name": "object_c"}],
    }


@pytest.fixture
def fxt_update_classification_task_rest(fxt_create_classification_task_rest, fxt_mongo_id):
    fxt_create_classification_task_rest["id"] = fxt_mongo_id(5)
    fxt_create_classification_task_rest["labels"] = [
        {"name": "object_a", "id": fxt_mongo_id(6), "color": "#000000"},
        {"name": "object_b", "id": fxt_mongo_id(7), "color": "#000001"},
        {"name": "object_c", "id": fxt_mongo_id(8), "color": "#000002"},
        {
            "name": "new_object_1",
            "parent_id": fxt_mongo_id(6),
            "id": fxt_mongo_id(9),
            "color": "#000003",
        },
        {
            "name": "new_object_2",
            "parent_id": fxt_mongo_id(6),
            "id": fxt_mongo_id(10),
            "color": "#000004",
        },
    ]
    yield fxt_create_classification_task_rest


@pytest.fixture
def fxt_update_segmentation_task_rest(fxt_create_segmentation_task_rest, fxt_mongo_id):
    fxt_create_segmentation_task_rest["id"] = fxt_mongo_id(5)
    fxt_create_segmentation_task_rest["labels"] = [
        {"name": "dummy_object", "id": fxt_mongo_id(4), "color": "#000000"},
        {"name": "new_label", "color": "#000001", "id": fxt_mongo_id(0)},
    ]
    yield fxt_create_segmentation_task_rest


@pytest.fixture
def fxt_create_anomaly_task_rest():
    yield {
        "title": "Anomaly task",
        "task_type": "anomaly",
        "labels": [],
    }


@pytest.fixture
def fxt_update_anomaly_task_rest(fxt_mongo_id):
    yield {
        "title": "Anomaly task",
        "task_type": "anomaly",
        "labels": [
            {"name": "normal", "color": "#00111111"},
            {"name": "anomalous", "color": "#00222222"},
        ],
        "id": fxt_mongo_id(11),
    }


@pytest.fixture
def fxt_create_keypoint_detection_task_rest():
    yield {
        "title": "Keypoint detection task",
        "task_type": "keypoint_detection",
        "labels": [
            {
                "name": "head",
                "group": "Default keypoint detection",
                "color": "#09FF27",
                "parent_id": None,
                "hotkey": "crtl+0",
            },
            {
                "name": "neck",
                "color": "#FF7809",
                "group": "Default keypoint detection",
                "parent_id": None,
                "hotkey": "crtl+1",
            },
            {
                "name": "back",
                "color": "#0919FF",
                "group": "Default keypoint detection",
                "parent_id": None,
                "hotkey": "crtl+2",
            },
            {
                "name": "left_shoulder",
                "color": "#FF09BD",
                "group": "Default keypoint detection",
                "parent_id": None,
                "hotkey": "crtl+3",
            },
            {
                "name": "right_shoulder",
                "color": "#FF0909",
                "group": "Default keypoint detection",
                "parent_id": None,
                "hotkey": "crtl+4",
            },
        ],
        "keypoint_structure": {
            "edges": [
                {"nodes": ["head", "neck"]},
                {"nodes": ["neck", "back"]},
                {"nodes": ["neck", "left_shoulder"]},
                {"nodes": ["neck", "right_shoulder"]},
            ],
            "positions": [
                {"label": "head", "x": 0.1, "y": 0.2},
                {"label": "neck", "x": 0.3, "y": 0.4},
                {"label": "back", "x": 0.5, "y": 0.6},
                {"label": "left_shoulder", "x": 0.7, "y": 0.8},
                {"label": "right_shoulder", "x": 0.9, "y": 0.1},
            ],
        },
    }


@pytest.fixture
def fxt_update_keypoint_detection_task_rest(fxt_mongo_id):
    yield {
        "title": "Keypoint detection task",
        "task_type": "keypoint_detection",
        "labels": [
            {
                "name": "head",
                "color": "#09FF27",
                "id": fxt_mongo_id(12),
            },
            {
                "name": "neck",
                "color": "#FF7809",
                "id": fxt_mongo_id(13),
            },
            {
                "name": "back",
                "color": "#0919FF",
                "id": fxt_mongo_id(14),
            },
            {
                "name": "left_shoulder",
                "color": "#FF09BD",
                "id": fxt_mongo_id(15),
            },
            {
                "name": "right_shoulder",
                "color": "#FF0909",
                "id": fxt_mongo_id(16),
            },
        ],
        "keypoint_structure": {
            "edges": [
                {"nodes": [fxt_mongo_id(12), fxt_mongo_id(13)]},
                {"nodes": [fxt_mongo_id(13), fxt_mongo_id(14)]},
                {"nodes": [fxt_mongo_id(14), fxt_mongo_id(15)]},
                {"nodes": [fxt_mongo_id(15), fxt_mongo_id(16)]},
            ],
            "positions": [
                {"label": fxt_mongo_id(12), "x": 0.1, "y": 0.2},
                {"label": fxt_mongo_id(13), "x": 0.3, "y": 0.4},
                {"label": fxt_mongo_id(14), "x": 0.5, "y": 0.6},
                {"label": fxt_mongo_id(15), "x": 0.7, "y": 0.8},
                {"label": fxt_mongo_id(16), "x": 0.9, "y": 0.1},
            ],
        },
        "id": fxt_mongo_id(11),
    }


@pytest.fixture
def fxt_create_invalid_project_rest_missing_fields(fxt_create_dataset_task_rest, fxt_create_detection_task_rest):
    yield {
        "name": "dummy_project",
        "pipeline": {
            # intentionally missing 'connections' field
            "tasks": [fxt_create_detection_task_rest, fxt_create_dataset_task_rest]
        },
    }


@pytest.fixture
def fxt_update_invalid_project_rest_missing_fields(
    fxt_update_dataset_task_rest,
    fxt_update_detection_task_rest,
    fxt_mongo_id,
):
    yield {
        "id": fxt_mongo_id(10),
        "name": "dummy_project",
        "pipeline": {
            # intentionally missing 'connections' field
            "tasks": [fxt_update_detection_task_rest, fxt_update_dataset_task_rest]
        },
    }


@pytest.fixture
def fxt_create_valid_project_rest_single_task(fxt_create_dataset_task_rest, fxt_create_detection_task_rest):
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [fxt_create_dataset_task_rest, fxt_create_detection_task_rest],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_detection_task_rest["title"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_update_valid_project_rest_single_task(
    fxt_update_dataset_task_rest, fxt_update_detection_task_rest, fxt_mongo_id
):
    yield {
        "name": "dummy_project",
        "id": fxt_mongo_id(10),
        "pipeline": {
            "tasks": [fxt_update_dataset_task_rest, fxt_update_detection_task_rest],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_detection_task_rest["id"],
                }
            ],
        },
        "performance": {
            "score": None,
            "task_performances": [
                {
                    "task_id": fxt_update_detection_task_rest["id"],
                    "score": None,
                },
            ],
        },
    }


@pytest.fixture
def fxt_create_valid_project_rest_multi_task(
    fxt_create_dataset_task_rest,
    fxt_create_detection_task_rest,
    fxt_create_crop_task_rest,
    fxt_create_classification_task_rest,
):
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_create_detection_task_rest,
                fxt_create_dataset_task_rest,
                fxt_create_classification_task_rest,
                fxt_create_crop_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_detection_task_rest["title"],
                },
                {
                    "from": fxt_create_crop_task_rest["title"],
                    "to": fxt_create_classification_task_rest["title"],
                },
                {
                    "from": fxt_create_detection_task_rest["title"],
                    "to": fxt_create_crop_task_rest["title"],
                },
            ],
        },
    }


@pytest.fixture
def fxt_update_valid_project_rest_multi_task(
    fxt_update_dataset_task_rest,
    fxt_update_detection_task_rest,
    fxt_update_crop_task_rest,
    fxt_update_classification_task_rest,
    fxt_mongo_id,
):
    yield {
        "name": "dummy_project",
        "id": fxt_mongo_id(10),
        "pipeline": {
            "tasks": [
                fxt_update_detection_task_rest,
                fxt_update_dataset_task_rest,
                fxt_update_classification_task_rest,
                fxt_update_crop_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_detection_task_rest["id"],
                },
                {
                    "from": fxt_update_crop_task_rest["id"],
                    "to": fxt_update_classification_task_rest["id"],
                },
                {
                    "from": fxt_update_detection_task_rest["id"],
                    "to": fxt_update_crop_task_rest["id"],
                },
            ],
        },
    }


@pytest.fixture
def fxt_create_valid_project_rest_deep_hierarchy(fxt_create_dataset_task_rest, fxt_create_classification_task_rest):
    fxt_create_classification_task_rest["labels"] = [
        {"name": "top1", "group": "grp1"},
        {"name": "top2", "group": "grp1"},
        {"name": "mid1", "parent_id": "top1", "group": "grp2"},
        {"name": "mid2", "parent_id": "top1", "group": "grp2"},
        {"name": "bot1", "parent_id": "mid1", "group": "grp3"},
    ]
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_create_dataset_task_rest,
                fxt_create_classification_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_classification_task_rest["title"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_update_valid_project_rest_deep_hierarchy(
    fxt_update_dataset_task_rest, fxt_update_classification_task_rest, fxt_mongo_id
):
    fxt_update_classification_task_rest["labels"] = [
        {"id": fxt_mongo_id(1), "name": "top1", "group": "grp1", "color": "#00111111"},
        {"id": fxt_mongo_id(2), "name": "top2", "group": "grp1", "color": "#00222222"},
        {"name": "mid1", "parent_id": "top1", "group": "grp2", "color": "#00222222"},
        {"name": "mid2", "parent_id": "top1", "group": "grp2", "color": "#00333333"},
        {"name": "bot1", "parent_id": "mid1", "group": "grp3", "color": "#00444444"},
    ]
    yield {
        "name": "dummy_project",
        "id": fxt_mongo_id(10),
        "pipeline": {
            "tasks": [
                fxt_update_dataset_task_rest,
                fxt_update_classification_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_classification_task_rest["id"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_create_valid_project_rest_anomaly_task(fxt_create_dataset_task_rest, fxt_create_anomaly_task_rest):
    yield {
        "name": "dummy_anomaly_project",
        "pipeline": {
            "tasks": [
                fxt_create_dataset_task_rest,
                fxt_create_anomaly_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_anomaly_task_rest["title"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_update_valid_project_rest_anomaly_task(
    fxt_update_dataset_task_rest,
    fxt_update_anomaly_task_rest,
    fxt_mongo_id,
):
    yield {
        "name": "dummy_anomaly_project",
        "id": fxt_mongo_id(10),
        "pipeline": {
            "tasks": [
                fxt_update_dataset_task_rest,
                fxt_update_anomaly_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_anomaly_task_rest["id"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_create_valid_project_rest_keypoint_detection_task(
    fxt_create_dataset_task_rest, fxt_create_keypoint_detection_task_rest, fxt_enable_feature_flag_name
):
    fxt_enable_feature_flag_name(FeatureFlag.FEATURE_FLAG_KEYPOINT_DETECTION.name)
    yield {
        "name": "dummy_keypoint_detection_project",
        "pipeline": {
            "tasks": [
                fxt_create_dataset_task_rest,
                fxt_create_keypoint_detection_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_keypoint_detection_task_rest["title"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_update_valid_project_rest_keypoint_detection_task(
    fxt_update_dataset_task_rest,
    fxt_update_keypoint_detection_task_rest,
    fxt_enable_feature_flag_name,
    fxt_mongo_id,
):
    fxt_enable_feature_flag_name(FeatureFlag.FEATURE_FLAG_KEYPOINT_DETECTION.name)
    yield {
        "name": "dummy_keypoint_detection_project",
        "id": fxt_mongo_id(10),
        "pipeline": {
            "tasks": [
                fxt_update_dataset_task_rest,
                fxt_update_keypoint_detection_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_keypoint_detection_task_rest["id"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_create_invalid_project_rest_anomaly_task_with_labels(
    fxt_create_valid_project_rest_anomaly_task,
):
    anomaly_task = fxt_create_valid_project_rest_anomaly_task
    anomaly_task["pipeline"]["tasks"][1]["labels"] = [
        {"name": "normal", "color": "#00111111"},
        {"name": "anomalous", "color": "#00222222"},
    ]
    yield anomaly_task


@pytest.fixture
def fxt_create_invalid_project_rest_anomaly_task_deprecated(
    fxt_create_valid_project_rest_anomaly_task,
):
    fxt_create_valid_project_rest_anomaly_task["pipeline"]["tasks"][1]["task_type"] = "anomaly_classification"
    yield fxt_create_valid_project_rest_anomaly_task


@pytest.fixture
def fxt_update_invalid_project_rest_anomaly_task_without_labels(
    fxt_update_valid_project_rest_anomaly_task,
):
    anomaly_task = fxt_update_valid_project_rest_anomaly_task
    anomaly_task["pipeline"]["tasks"][1]["labels"] = []
    yield anomaly_task


@pytest.fixture
def fxt_create_invalid_project_rest_no_connections(fxt_create_dataset_task_rest, fxt_create_detection_task_rest):
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [fxt_create_dataset_task_rest, fxt_create_detection_task_rest],
            "connections": [],
        },
    }


@pytest.fixture
def fxt_update_invalid_project_rest_no_connections(
    fxt_update_dataset_task_rest, fxt_update_detection_task_rest, fxt_mongo_id
):
    yield {
        "name": "dummy_project",
        "id": fxt_mongo_id(10),
        "pipeline": {
            "tasks": [fxt_update_dataset_task_rest, fxt_update_detection_task_rest],
            "connections": [],
        },
    }


@pytest.fixture
def fxt_create_invalid_project_rest_no_tasks(fxt_create_dataset_task_rest, fxt_create_detection_task_rest):
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_detection_task_rest["title"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_update_invalid_project_rest_no_tasks(
    fxt_update_dataset_task_rest, fxt_update_detection_task_rest, fxt_mongo_id
):
    yield {
        "name": "dummy_project",
        "id": fxt_mongo_id(10),
        "pipeline": {
            "tasks": [],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_detection_task_rest["id"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_create_invalid_project_rest_duplicate_task_titles(
    fxt_create_dataset_task_rest,
    fxt_create_detection_task_rest,
    fxt_create_crop_task_rest,
    fxt_create_classification_task_rest,
):
    fxt_create_classification_task_rest["title"] = fxt_create_detection_task_rest["title"]
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_create_detection_task_rest,
                fxt_create_dataset_task_rest,
                fxt_create_classification_task_rest,
                fxt_create_crop_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_detection_task_rest["title"],
                },
                {
                    "from": fxt_create_crop_task_rest["title"],
                    "to": fxt_create_classification_task_rest["title"],
                },
                {
                    "from": fxt_create_detection_task_rest["title"],
                    "to": fxt_create_crop_task_rest["title"],
                },
            ],
        },
    }


@pytest.fixture
def fxt_update_invalid_project_rest_duplicate_task_titles(
    fxt_update_dataset_task_rest,
    fxt_update_detection_task_rest,
    fxt_update_crop_task_rest,
    fxt_update_classification_task_rest,
    fxt_mongo_id,
):
    fxt_update_classification_task_rest["title"] = fxt_update_detection_task_rest["title"]
    yield {
        "id": fxt_mongo_id(10),
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_update_detection_task_rest,
                fxt_update_dataset_task_rest,
                fxt_update_classification_task_rest,
                fxt_update_crop_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_detection_task_rest["id"],
                },
                {
                    "from": fxt_update_crop_task_rest["id"],
                    "to": fxt_update_classification_task_rest["id"],
                },
                {
                    "from": fxt_update_detection_task_rest["id"],
                    "to": fxt_update_crop_task_rest["id"],
                },
            ],
        },
    }


@pytest.fixture
def fxt_create_invalid_project_rest_empty_name(fxt_create_dataset_task_rest, fxt_create_detection_task_rest):
    yield {
        "name": "        \n",
        "pipeline": {
            "tasks": [fxt_create_dataset_task_rest, fxt_create_detection_task_rest],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_detection_task_rest["title"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_update_invalid_project_rest_empty_name(
    fxt_update_dataset_task_rest, fxt_update_detection_task_rest, fxt_mongo_id
):
    yield {
        "id": fxt_mongo_id(10),
        "name": "        \n",
        "pipeline": {
            "tasks": [fxt_update_dataset_task_rest, fxt_update_detection_task_rest],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_detection_task_rest["id"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_create_invalid_project_rest_missing_connection(
    fxt_create_dataset_task_rest,
    fxt_create_detection_task_rest,
    fxt_create_crop_task_rest,
    fxt_create_classification_task_rest,
):
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_create_detection_task_rest,
                fxt_create_dataset_task_rest,
                fxt_create_classification_task_rest,
                fxt_create_crop_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_detection_task_rest["title"],
                },
                {
                    "from": fxt_create_detection_task_rest["title"],
                    "to": fxt_create_crop_task_rest["title"],
                },
            ],
        },
    }


@pytest.fixture
def fxt_update_invalid_project_rest_missing_connection(
    fxt_update_dataset_task_rest,
    fxt_update_detection_task_rest,
    fxt_update_crop_task_rest,
    fxt_update_classification_task_rest,
    fxt_mongo_id,
):
    yield {
        "id": fxt_mongo_id(10),
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_update_detection_task_rest,
                fxt_update_dataset_task_rest,
                fxt_update_classification_task_rest,
                fxt_update_crop_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_detection_task_rest["id"],
                },
                {
                    "from": fxt_update_detection_task_rest["id"],
                    "to": fxt_update_crop_task_rest["id"],
                },
            ],
        },
    }


@pytest.fixture
def fxt_create_invalid_project_rest_bad_connection(
    fxt_create_dataset_task_rest,
    fxt_create_detection_task_rest,
    fxt_create_crop_task_rest,
    fxt_create_classification_task_rest,
):
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_create_detection_task_rest,
                fxt_create_dataset_task_rest,
                fxt_create_classification_task_rest,
                fxt_create_crop_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_detection_task_rest["title"],
                },
                {
                    "from": fxt_create_detection_task_rest["title"],
                    "to": fxt_create_crop_task_rest["title"],
                },
                {
                    "from": fxt_create_crop_task_rest["title"],
                    "to": "BAD TASK",
                },
            ],
        },
    }


@pytest.fixture
def fxt_update_invalid_project_rest_bad_connection(
    fxt_update_dataset_task_rest,
    fxt_update_detection_task_rest,
    fxt_update_crop_task_rest,
    fxt_update_classification_task_rest,
    fxt_mongo_id,
):
    yield {
        "id": fxt_mongo_id(10),
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_update_detection_task_rest,
                fxt_update_dataset_task_rest,
                fxt_update_classification_task_rest,
                fxt_update_crop_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_detection_task_rest["id"],
                },
                {
                    "from": fxt_update_detection_task_rest["id"],
                    "to": fxt_update_crop_task_rest["id"],
                },
                {
                    "from": fxt_update_crop_task_rest["id"],
                    "to": fxt_mongo_id(999),
                },
            ],
        },
    }


@pytest.fixture
def fxt_create_invalid_project_rest_classification_one_label(
    fxt_create_dataset_task_rest, fxt_create_classification_task_rest
):
    fxt_create_classification_task_rest["labels"] = [{"name": "dummy_object"}]
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_create_dataset_task_rest,
                fxt_create_classification_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_classification_task_rest["title"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_update_invalid_project_rest_classification_one_label(
    fxt_update_dataset_task_rest, fxt_update_classification_task_rest, fxt_mongo_id
):
    fxt_update_classification_task_rest["labels"] = [{"name": "dummy_object", "color": "#00112233"}]
    yield {
        "id": fxt_mongo_id(10),
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_update_dataset_task_rest,
                fxt_update_classification_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_classification_task_rest["id"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_create_invalid_project_rest_hierarchical_cls_one_top_label(
    fxt_create_dataset_task_rest, fxt_create_classification_task_rest
):
    fxt_create_classification_task_rest["labels"] = [
        {"name": "top"},
        {"name": "bot", "parent_id": "top"},
    ]
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_create_dataset_task_rest,
                fxt_create_classification_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_classification_task_rest["title"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_update_invalid_project_rest_hierarchical_cls_one_top_label(
    fxt_update_dataset_task_rest, fxt_update_classification_task_rest, fxt_mongo_id
):
    fxt_update_classification_task_rest["labels"] = [
        {"name": "top", "color": "#00111111"},
        {"name": "bot", "parent_id": "top", "color": "#00222222"},
    ]
    yield {
        "id": fxt_mongo_id(10),
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_update_dataset_task_rest,
                fxt_update_classification_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_classification_task_rest["id"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_create_invalid_project_rest_duplicate_label_names(fxt_create_dataset_task_rest, fxt_create_detection_task_rest):
    fxt_create_detection_task_rest["labels"] = [
        {"name": "dummy_object"},
        {"name": "object_a"},
        {"name": "dummy_object"},
    ]
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [fxt_create_detection_task_rest, fxt_create_dataset_task_rest],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_detection_task_rest["title"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_update_invalid_project_rest_duplicate_label_names(
    fxt_update_dataset_task_rest, fxt_update_detection_task_rest, fxt_mongo_id
):
    fxt_update_detection_task_rest["labels"] = [
        {"name": "dummy_object", "color": "#00111111"},
        {"name": "object_a", "color": "#00222222"},
        {"name": "dummy_object", "color": "#00333333"},
    ]
    yield {
        "id": fxt_mongo_id(10),
        "name": "dummy_project",
        "pipeline": {
            "tasks": [fxt_update_detection_task_rest, fxt_update_dataset_task_rest],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_detection_task_rest["id"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_create_invalid_project_rest_multi_task_duplicate_label_names(
    fxt_create_dataset_task_rest,
    fxt_create_detection_task_rest,
    fxt_create_crop_task_rest,
    fxt_create_classification_task_rest,
):
    fxt_create_classification_task_rest["labels"].extend(fxt_create_detection_task_rest["labels"])
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_create_detection_task_rest,
                fxt_create_dataset_task_rest,
                fxt_create_classification_task_rest,
                fxt_create_crop_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_detection_task_rest["title"],
                },
                {
                    "from": fxt_create_crop_task_rest["title"],
                    "to": fxt_create_classification_task_rest["title"],
                },
                {
                    "from": fxt_create_detection_task_rest["title"],
                    "to": fxt_create_crop_task_rest["title"],
                },
            ],
        },
    }


@pytest.fixture
def fxt_update_invalid_project_rest_multi_task_duplicate_label_names(
    fxt_update_dataset_task_rest,
    fxt_update_detection_task_rest,
    fxt_update_crop_task_rest,
    fxt_update_classification_task_rest,
    fxt_mongo_id,
):
    fxt_update_classification_task_rest["labels"].extend(fxt_update_detection_task_rest["labels"])
    yield {
        "id": fxt_mongo_id(10),
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_update_detection_task_rest,
                fxt_update_dataset_task_rest,
                fxt_update_classification_task_rest,
                fxt_update_crop_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_detection_task_rest["id"],
                },
                {
                    "from": fxt_update_crop_task_rest["id"],
                    "to": fxt_update_classification_task_rest["id"],
                },
                {
                    "from": fxt_update_detection_task_rest["id"],
                    "to": fxt_update_crop_task_rest["id"],
                },
            ],
        },
    }


@pytest.fixture()
def fxt_create_invalid_project_rest_duplicate_label_hotkeys(
    fxt_create_dataset_task_rest, fxt_create_detection_task_rest
):
    fxt_create_detection_task_rest["labels"] = [
        {"name": "dummy_object_a", "hotkey": "A"},
        {"name": "dummy_object_b", "hotkey": "A"},
    ]
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [fxt_create_detection_task_rest, fxt_create_dataset_task_rest],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_detection_task_rest["title"],
                }
            ],
        },
    }


@pytest.fixture()
def fxt_update_invalid_project_rest_duplicate_label_hotkeys(
    fxt_update_dataset_task_rest, fxt_update_detection_task_rest, fxt_mongo_id
):
    fxt_update_detection_task_rest["labels"] = [
        {"name": "dummy_object_a", "hotkey": "A", "color": "#00111111"},
        {"name": "dummy_object_b", "hotkey": "A", "color": "#00222222"},
    ]
    yield {
        "id": fxt_mongo_id(10),
        "name": "dummy_project",
        "pipeline": {
            "tasks": [fxt_update_detection_task_rest, fxt_update_dataset_task_rest],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_detection_task_rest["id"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_create_invalid_project_rest_non_existing_parent(
    fxt_create_dataset_task_rest, fxt_create_classification_task_rest
):
    fxt_create_classification_task_rest["labels"] = [
        {"name": "dummy_object"},
        {"name": "object_a", "parent_id": "non_existing_label"},
    ]
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_create_dataset_task_rest,
                fxt_create_classification_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_classification_task_rest["title"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_update_invalid_project_rest_non_existing_parent(
    fxt_update_dataset_task_rest, fxt_update_classification_task_rest, fxt_mongo_id
):
    fxt_update_classification_task_rest["labels"] = [
        {"name": "dummy_object", "color": "#00111111"},
        {"name": "object_a", "parent_id": "non_existing_label", "color": "#00222222"},
    ]
    yield {
        "id": fxt_mongo_id(10),
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_update_dataset_task_rest,
                fxt_update_classification_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_classification_task_rest["id"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_create_invalid_project_rest_self_referencing_parent(
    fxt_create_dataset_task_rest, fxt_create_classification_task_rest
):
    fxt_create_classification_task_rest["labels"] = [
        {"name": "object_a"},
        {"name": "object_b"},
        {"name": "object_c", "parent_id": "object_c"},
    ]
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_create_dataset_task_rest,
                fxt_create_classification_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_classification_task_rest["title"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_update_invalid_project_rest_self_referencing_parent(
    fxt_update_dataset_task_rest, fxt_update_classification_task_rest, fxt_mongo_id
):
    fxt_update_classification_task_rest["labels"] = [
        {"name": "object_a", "color": "#00111111"},
        {"name": "object_b", "color": "#00222222"},
        {"name": "object_c", "parent_id": "object_c", "color": "#00333333"},
    ]
    yield {
        "id": fxt_mongo_id(10),
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_update_dataset_task_rest,
                fxt_update_classification_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_classification_task_rest["id"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_create_invalid_project_rest_local_task_with_hierarchy(
    fxt_create_dataset_task_rest, fxt_create_detection_task_rest
):
    fxt_create_detection_task_rest["labels"] = [
        {"name": "object_a"},
        {"name": "object_b", "parent_id": "object_a"},
    ]
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [fxt_create_dataset_task_rest, fxt_create_detection_task_rest],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_detection_task_rest["title"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_update_invalid_project_rest_local_task_with_hierarchy(
    fxt_update_dataset_task_rest, fxt_update_detection_task_rest, fxt_mongo_id
):
    fxt_update_detection_task_rest["labels"] = [
        {"name": "object_a", "color": "#00111111"},
        {"name": "object_b", "parent_id": "object_a", "color": "#00222222"},
    ]
    yield {
        "id": fxt_mongo_id(10),
        "name": "dummy_project",
        "pipeline": {
            "tasks": [fxt_update_dataset_task_rest, fxt_update_detection_task_rest],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_detection_task_rest["id"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_create_invalid_project_rest_label_group_in_multiple_tasks(
    fxt_create_dataset_task_rest,
    fxt_create_detection_task_rest,
    fxt_create_crop_task_rest,
    fxt_create_classification_task_rest,
):
    fxt_create_classification_task_rest["labels"] = [
        {"name": "object_a", "group": "dummy_group"},
        {"name": "object_b"},
    ]
    fxt_create_detection_task_rest["labels"] = [{"name": "dummy_object", "group": "dummy_group"}]
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_create_detection_task_rest,
                fxt_create_dataset_task_rest,
                fxt_create_classification_task_rest,
                fxt_create_crop_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_detection_task_rest["title"],
                },
                {
                    "from": fxt_create_crop_task_rest["title"],
                    "to": fxt_create_classification_task_rest["title"],
                },
                {
                    "from": fxt_create_detection_task_rest["title"],
                    "to": fxt_create_crop_task_rest["title"],
                },
            ],
        },
    }


@pytest.fixture
def fxt_update_invalid_project_rest_label_group_in_multiple_tasks(
    fxt_update_dataset_task_rest,
    fxt_update_detection_task_rest,
    fxt_update_crop_task_rest,
    fxt_update_classification_task_rest,
    fxt_mongo_id,
):
    fxt_update_classification_task_rest["labels"] = [
        {"name": "object_a", "group": "dummy_group", "color": "#00111111"},
        {"name": "object_b", "color": "#00222222"},
    ]
    fxt_update_detection_task_rest["labels"] = [{"name": "dummy_object", "group": "dummy_group", "color": "#00333333"}]
    yield {
        "id": fxt_mongo_id(10),
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_update_detection_task_rest,
                fxt_update_dataset_task_rest,
                fxt_update_classification_task_rest,
                fxt_update_crop_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_detection_task_rest["id"],
                },
                {
                    "from": fxt_update_crop_task_rest["id"],
                    "to": fxt_update_classification_task_rest["id"],
                },
                {
                    "from": fxt_update_detection_task_rest["id"],
                    "to": fxt_update_crop_task_rest["id"],
                },
            ],
        },
    }


@pytest.fixture
def fxt_create_invalid_project_rest_same_group_hierarchical_labels(
    fxt_create_dataset_task_rest, fxt_create_classification_task_rest
):
    fxt_create_classification_task_rest["labels"] = [
        {"name": "top1", "group": "grp1"},
        {"name": "top2", "group": "grp2"},
        {"name": "bot1", "parent_id": "top1", "group": "grp1"},
    ]
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_create_dataset_task_rest,
                fxt_create_classification_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_classification_task_rest["title"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_update_invalid_project_rest_same_group_hierarchical_labels(
    fxt_update_dataset_task_rest, fxt_update_classification_task_rest, fxt_mongo_id
):
    fxt_update_classification_task_rest["labels"] = [
        {"name": "top1", "group": "grp1", "color": "#00111111"},
        {"name": "top2", "group": "grp2", "color": "#00222222"},
        {"name": "bot1", "parent_id": "top1", "group": "grp1", "color": "#00333333"},
    ]
    yield {
        "id": fxt_mongo_id(10),
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_update_dataset_task_rest,
                fxt_update_classification_task_rest,
            ],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_classification_task_rest["id"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_create_invalid_project_rest_empty_label_name_conflict(
    fxt_create_dataset_task_rest, fxt_create_detection_task_rest
):
    fxt_create_detection_task_rest["labels"] = [
        {"name": "dummy_object"},
        {"name": "No object"},
    ]
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [fxt_create_dataset_task_rest, fxt_create_detection_task_rest],
            "connections": [
                {
                    "from": fxt_create_dataset_task_rest["title"],
                    "to": fxt_create_detection_task_rest["title"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_create_invalid_project_rest_too_many_tasks(
    fxt_create_dataset_task_rest,
    fxt_create_detection_task_rest,
    fxt_create_crop_task_rest,
    fxt_create_classification_task_rest,
    fxt_create_segmentation_task_rest,
):
    yield {
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_create_dataset_task_rest,
                fxt_create_detection_task_rest,
                fxt_create_crop_task_rest,
                fxt_create_classification_task_rest,
                fxt_create_segmentation_task_rest,
            ],
            "connections": [
                {"from": "Dataset", "to": "Detection"},
                {"from": "Detection", "to": "Crop"},
                {"from": "Crop", "to": "Classification"},
                {"from": "Classification", "to": "Segmentation"},
            ],
        },
    }


@pytest.fixture
def fxt_update_invalid_project_rest_too_many_tasks(
    fxt_mongo_id,
    fxt_update_dataset_task_rest,
    fxt_update_detection_task_rest,
    fxt_update_crop_task_rest,
    fxt_update_classification_task_rest,
    fxt_update_segmentation_task_rest,
):
    yield {
        "id": fxt_mongo_id(10),
        "name": "dummy_project",
        "pipeline": {
            "tasks": [
                fxt_update_dataset_task_rest,
                fxt_update_detection_task_rest,
                fxt_update_crop_task_rest,
                fxt_update_classification_task_rest,
                fxt_update_segmentation_task_rest,
            ],
            "connections": [
                {"from": fxt_update_dataset_task_rest["id"], "to": fxt_update_detection_task_rest["id"]},
                {"from": fxt_update_detection_task_rest["id"], "to": fxt_update_crop_task_rest["id"]},
                {"from": fxt_update_crop_task_rest["id"], "to": fxt_update_classification_task_rest["id"]},
                {"from": fxt_update_classification_task_rest["id"], "to": fxt_update_segmentation_task_rest["id"]},
            ],
        },
    }


@pytest.fixture
def fxt_update_invalid_project_rest_empty_label_name_conflict(
    fxt_update_dataset_task_rest, fxt_update_detection_task_rest, fxt_mongo_id
):
    fxt_update_detection_task_rest["labels"] = [
        {"name": "dummy_object", "color": "#00111111"},
        {"name": "No object", "color": "#00222222"},
    ]
    yield {
        "id": fxt_mongo_id(10),
        "name": "dummy_project",
        "pipeline": {
            "tasks": [fxt_update_dataset_task_rest, fxt_update_detection_task_rest],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_detection_task_rest["id"],
                }
            ],
        },
    }


@pytest.fixture
def fxt_update_invalid_project_rest_delete_empty_label(
    fxt_update_dataset_task_rest, fxt_update_detection_task_rest, fxt_mongo_id
):
    pipeline = {
        "id": fxt_mongo_id(10),
        "name": "dummy_project",
        "pipeline": {
            "tasks": [fxt_update_dataset_task_rest, fxt_update_detection_task_rest],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_detection_task_rest["id"],
                }
            ],
        },
    }
    pipeline["pipeline"]["tasks"][1]["labels"][0]["is_empty"] = True
    pipeline["pipeline"]["tasks"][1]["labels"][0]["is_deleted"] = True
    yield pipeline


@pytest.fixture
def fxt_update_invalid_project_rest_delete_last_label(
    fxt_update_dataset_task_rest, fxt_update_detection_task_rest, fxt_mongo_id
):
    pipeline = {
        "id": fxt_mongo_id(10),
        "name": "dummy_project",
        "pipeline": {
            "tasks": [fxt_update_dataset_task_rest, fxt_update_detection_task_rest],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_detection_task_rest["id"],
                }
            ],
        },
    }
    for label_data in pipeline["pipeline"]["tasks"][1]["labels"]:
        label_data["is_deleted"] = True
    yield pipeline


@pytest.fixture()
def fxt_update_valid_project_rest_reuse_deleted_label_hotkeys(
    fxt_update_dataset_task_rest, fxt_update_detection_task_rest, fxt_mongo_id
):
    fxt_update_detection_task_rest["labels"] = [
        {
            "name": "dummy_object_a",
            "hotkey": "A",
            "is_deleted": True,
            "color": "#00111111",
        },
        {"name": "dummy_object_b", "hotkey": "A", "color": "#00222222"},
    ]
    yield {
        "id": fxt_mongo_id(10),
        "name": "dummy_project",
        "pipeline": {
            "tasks": [fxt_update_dataset_task_rest, fxt_update_detection_task_rest],
            "connections": [
                {
                    "from": fxt_update_dataset_task_rest["id"],
                    "to": fxt_update_detection_task_rest["id"],
                }
            ],
        },
    }


class TestProjectRestValidator:
    # fmt: off
    @pytest.mark.parametrize(
        "lazyfxt_project_rest, expected_exception",
        (
            ("fxt_create_valid_project_rest_single_task", None),
            ("fxt_create_valid_project_rest_multi_task", None),
            ("fxt_create_valid_project_rest_deep_hierarchy", None),
            ("fxt_create_valid_project_rest_anomaly_task", None),
            ("fxt_create_valid_project_rest_keypoint_detection_task", None),
            ("fxt_create_invalid_project_rest_anomaly_task_with_labels", BadNumberOfLabelsException),
            ("fxt_create_invalid_project_rest_missing_fields", ValidationError),
            ("fxt_create_invalid_project_rest_no_tasks", NoTasksInProjectException),
            ("fxt_create_invalid_project_rest_duplicate_task_titles", DuplicateTaskNamesException),
            ("fxt_create_invalid_project_rest_no_connections", NoTasksConnectionsException),
            ("fxt_create_invalid_project_rest_missing_connection", BadNumberOfConnectionsException),
            ("fxt_create_invalid_project_rest_bad_connection", UnconnectedTasksException),
            ("fxt_create_invalid_project_rest_empty_name", EmptyProjectNameException),
            ("fxt_create_invalid_project_rest_classification_one_label", BadNumberOfLabelsException),
            ("fxt_create_invalid_project_rest_hierarchical_cls_one_top_label", BadNumberOfLabelsException),
            ("fxt_create_invalid_project_rest_duplicate_label_names", DuplicateLabelNamesException),
            ("fxt_create_invalid_project_rest_multi_task_duplicate_label_names", DuplicateLabelNamesException),
            ("fxt_create_invalid_project_rest_duplicate_label_hotkeys", DuplicateHotkeysException),
            ("fxt_create_invalid_project_rest_non_existing_parent", ParentLabelNotFoundException),
            ("fxt_create_invalid_project_rest_self_referencing_parent", SelfReferencingParentLabelException),
            ("fxt_create_invalid_project_rest_local_task_with_hierarchy", UnsupportedHierarchicalLabelsException),
            ("fxt_create_invalid_project_rest_label_group_in_multiple_tasks", MultiTaskLabelGroupException),
            ("fxt_create_invalid_project_rest_same_group_hierarchical_labels", MismatchingParentsInLabelGroupException),
            ("fxt_create_invalid_project_rest_empty_label_name_conflict", ReservedLabelNameException),
            ("fxt_create_invalid_project_rest_too_many_tasks", TooManyTasksException),
        ),
        ids=[
            "valid single task project",
            "valid multi task project",
            "valid project with a deep hierarchy of labels",
            "valid anomaly project",
            "valid keypoint detection project",
            "invalid anomaly due to unexpected labels",
            "invalid due to missing mandatory fields",
            "invalid due to empty tasks list",
            "invalid due to duplicate task titles",
            "invalid due to empty connections list",
            "invalid due to missing connections",
            "invalid due to bad connections",
            "invalid due to empty name (no valid characters)",
            "invalid classification due to insufficient labels",
            "invalid hier. class. due to insufficient labels in the top level",
            "invalid due to duplicate label names in a task",
            "invalid due to duplicate labels names across tasks",
            "invalid task due to duplicate label hotkeys in a task",
            "invalid due to parent_id pointing to a non-existing label",
            "invalid due to parent_id pointing to the label itself",
            "invalid due to a local task with label with non-null parent",
            "invalid due to duplicate label group across tasks",
            "invalid due to hierarchical labels having the same group",
            "invalid due to a label with the same name of the empty one",
            "invalid due to too many tasks"
        ],
    )
    # fmt: on
    def test_validate_creation_data_statically(
        self, lazyfxt_project_rest, expected_exception, request: FixtureRequest
    ) -> None:
        # Arrange
        fxt_project_rest = request.getfixturevalue(lazyfxt_project_rest)
        context: Any
        if expected_exception is None:
            context = contextlib.nullcontext()
        else:
            context = pytest.raises(expected_exception)

        # Act
        with context:
            ProjectRestValidator().validate_creation_data_statically(fxt_project_rest)

    # fmt: off
    @pytest.mark.parametrize(
        "lazyfxt_project_rest, expected_exception",
        (
            ("fxt_update_valid_project_rest_single_task", None),
            ("fxt_update_valid_project_rest_multi_task", None),
            ("fxt_update_valid_project_rest_deep_hierarchy", None),
            ("fxt_update_valid_project_rest_anomaly_task", None),
            ("fxt_update_valid_project_rest_keypoint_detection_task", None),
            ("fxt_update_invalid_project_rest_anomaly_task_without_labels", BadNumberOfLabelsException),
            ("fxt_update_invalid_project_rest_missing_fields", ValidationError),
            ("fxt_update_invalid_project_rest_no_tasks", NoTasksInProjectException),
            ("fxt_update_invalid_project_rest_duplicate_task_titles", DuplicateTaskNamesException),
            ("fxt_update_invalid_project_rest_no_connections", NoTasksConnectionsException),
            ("fxt_update_invalid_project_rest_missing_connection", BadNumberOfConnectionsException),
            ("fxt_update_invalid_project_rest_bad_connection", UnconnectedTasksException),
            ("fxt_update_invalid_project_rest_empty_name", EmptyProjectNameException),
            ("fxt_update_invalid_project_rest_classification_one_label", BadNumberOfLabelsException),
            ("fxt_update_invalid_project_rest_hierarchical_cls_one_top_label", BadNumberOfLabelsException),
            ("fxt_update_invalid_project_rest_duplicate_label_names", DuplicateLabelNamesException),
            ("fxt_update_invalid_project_rest_multi_task_duplicate_label_names", DuplicateLabelNamesException),
            ("fxt_update_invalid_project_rest_duplicate_label_hotkeys", DuplicateHotkeysException),
            ("fxt_update_invalid_project_rest_non_existing_parent", ParentLabelNotFoundException),
            ("fxt_update_invalid_project_rest_self_referencing_parent", SelfReferencingParentLabelException),
            ("fxt_update_invalid_project_rest_local_task_with_hierarchy", UnsupportedHierarchicalLabelsException),
            ("fxt_update_invalid_project_rest_label_group_in_multiple_tasks", MultiTaskLabelGroupException),
            ("fxt_update_invalid_project_rest_same_group_hierarchical_labels", MismatchingParentsInLabelGroupException),
            ("fxt_update_invalid_project_rest_empty_label_name_conflict", ReservedLabelNameException),
            ("fxt_update_invalid_project_rest_delete_empty_label", InvalidLabelDeletedException),
            ("fxt_update_invalid_project_rest_delete_last_label", InvalidLabelDeletedException),
            ("fxt_update_invalid_project_rest_too_many_tasks", TooManyTasksException),
            ("fxt_update_valid_project_rest_reuse_deleted_label_hotkeys", None),
        ),
        ids=[
            "valid single task project",
            "valid multi task project",
            "valid project with a deep hierarchy of labels",
            "valid anomaly project",
            "valid keypoint detection project",
            "invalid anomaly due to missing labels",
            "invalid due to missing mandatory fields",
            "invalid due to empty tasks list",
            "invalid due to duplicate task titles",
            "invalid due to empty connections list",
            "invalid due to missing connections",
            "invalid due to bad connections",
            "invalid due to empty name (no valid characters)",
            "invalid classification due to insufficient labels",
            "invalid hier. class. due to insufficient labels in the top level",
            "invalid due to duplicate label names in a task",
            "invalid due to duplicate labels names across tasks",
            "invalid task due to duplicate label hotkeys in a task",
            "invalid due to parent_id pointing to a non-existing label",
            "invalid due to parent_id pointing to the label itself",
            "invalid due to a local task with label with non-null parent",
            "invalid due to duplicate label group across tasks",
            "invalid due to hierarchical labels having the same group",
            "invalid due to a label with the same name of the empty one",
            "invalid due to deleted empty label",
            "invalid due to deleted last label",
            "invalid due to too many tasks",
            "valid where the hotkey of a deleted label gets reused",
        ],
    )
    # fmt: on
    def test_validate_update_data_statically(
        self, lazyfxt_project_rest, expected_exception, request: FixtureRequest
    ) -> None:
        # Arrange
        fxt_project_rest = request.getfixturevalue(lazyfxt_project_rest)
        context: Any
        if expected_exception is None:
            context = contextlib.nullcontext()
        else:
            context = pytest.raises(expected_exception)

        # Act
        with context:
            ProjectRestValidator().validate_update_data_statically(fxt_project_rest)

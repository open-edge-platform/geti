# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from copy import deepcopy
from typing import Any

import pytest


def turn_creation_project_data_into_update(project_creation_data: dict[str, Any], fxt_mongo_id) -> dict[str, Any]:
    project_data = deepcopy(project_creation_data)
    label_name_to_id = {}
    project_data["id"] = fxt_mongo_id(0)
    id_iterator = 1
    for task_dict in project_data["tasks_dict"].values():
        task_dict["id"] = fxt_mongo_id(id_iterator)
        id_iterator += 1
        if "labels" not in task_dict:
            continue
        for label_name, label_dict in task_dict["labels"].items():
            label_dict["id"] = fxt_mongo_id(id_iterator)
            label_name_to_id[label_name] = label_dict["id"]
            id_iterator += 1
            label_dict["is_deleted"] = False
            label_dict["do_revisit"] = False

        for label_name, label_dict in task_dict["labels"].items():  # Update parent reference [name -> id]
            parent_id = label_dict.get("parent_id", None)
            if parent_id is not None:
                label_dict["parent_id"] = label_name_to_id.get(parent_id, "null")

    return project_data


@pytest.fixture
def fxt_binary_classification_project_data():
    yield {
        "name": "Test binary classification project",
        "tasks_dict": {
            "Dataset": {"task_type": "dataset"},
            "Classification task": {
                "task_type": "classification",
                "labels": {
                    "small": {
                        "color": "#fffffe",
                        "group": "Default Classification",
                        "parent_id": None,
                        "hotkey": "crtl+1",
                    },
                    "small?": {
                        "color": "#ffffff",
                        "group": "Default Classification",
                        "parent_id": None,
                        "hotkey": "crtl+2",
                    },
                },
            },
        },
    }


@pytest.fixture
def fxt_hierarchy_classification_project_data_2():
    yield {
        "name": "Test hierarchy classification project",
        "tasks_dict": {
            "Dataset": {"task_type": "dataset"},
            "Classification task": {
                "task_type": "classification",
                "labels": {
                    "1": {
                        "color": "#edb200ff",
                        "group": "Group 1",
                        "parent_id": None,
                        "hotkey": "",
                    },
                    "1.1": {
                        "color": "#548fadff",
                        "group": "Group 1.X",
                        "parent_id": "1",
                        "hotkey": "",
                    },
                    "1.1.1": {
                        "color": "#00f5d4ff",
                        "group": "Group 1.1.X",
                        "parent_id": "1.1",
                        "hotkey": "",
                    },
                    "1.1.2": {
                        "color": "#5b69ffff",
                        "group": "Group 1.1.X",
                        "parent_id": "1.1",
                        "hotkey": "",
                    },
                    "1.2": {
                        "color": "#9d3b1aff",
                        "group": "Group 1.X",
                        "parent_id": "1",
                        "hotkey": "",
                    },
                    "1.3": {
                        "color": "#d7bc5eff",
                        "group": "Group 1.X",
                        "parent_id": "1",
                        "hotkey": "",
                    },
                    "2": {
                        "color": "#708541ff",
                        "group": "Group 2",
                        "parent_id": None,
                        "hotkey": "",
                    },
                    "2.1": {
                        "color": "#c9e649ff",
                        "group": "Group 2.X",
                        "parent_id": "2",
                        "hotkey": "",
                    },
                },
            },
        },
    }


@pytest.fixture
def fxt_multiclass_classification_project_data():
    yield {
        "name": "Test multiclass classification project",
        "tasks_dict": {
            "Dataset": {"task_type": "dataset"},
            "Classification task": {
                "task_type": "classification",
                "labels": {
                    "small": {
                        "color": "#fffffe",
                        "group": "Default Classification",
                        "parent_id": None,
                        "hotkey": "crtl+1",
                    },
                    "large": {
                        "color": "#fffffe",
                        "group": "Default Classification",
                        "parent_id": None,
                        "hotkey": "crtl+2",
                    },
                    "quite small": {
                        "color": "#fffffe",
                        "group": "small group",
                        "parent_id": "small",
                        "hotkey": "crtl+3",
                    },
                    "tiny": {
                        "color": "#eefffe",
                        "group": "small group",
                        "parent_id": "small",
                        "hotkey": "crtl+4",
                    },
                },
            },
        },
    }


@pytest.fixture
def fxt_multilabel_classification_project_data():
    yield {
        "name": "Test multilabel classification project",
        "tasks_dict": {
            "Dataset": {"task_type": "dataset"},
            "Classification task": {
                "task_type": "classification",
                "labels": {
                    "small": {
                        "color": "#fffffe",
                        "group": "Default Classification",
                        "parent_id": None,
                        "hotkey": "crtl+1",
                    },
                    "large": {
                        "color": "#fffffe",
                        "group": "large group",
                        "parent_id": None,
                        "hotkey": "crtl+2",
                    },
                    "really large": {
                        "namor": "#fffffe",
                        "group": "really large group",
                        "parent_id": None,
                        "hotkey": "crtl+3",
                    },
                    "really extremely large": {
                        "name": "#feeeee",
                        "group": "really large group",
                        "parent_id": "really large",
                        "hotkey": "crtl+4",
                    },
                    "simply huuuge": {
                        "namor": "#effffe",
                        "group": "really large group",
                        "parent_id": "really large",
                        "hotkey": "crtl+5",
                    },
                },
            },
        },
    }


@pytest.fixture
def fxt_detection_classification_tasks():
    yield {
        "Dataset": {"task_type": "dataset"},
        "Detection task": {
            "task_type": "detection",
            "labels": {
                "dog": {
                    "color": "#ffffff",
                    "group": "Default Detection",
                    "parent_id": None,
                    "hotkey": "crtl+0",
                }
            },
        },
        "Crop task": {"task_type": "crop"},
        "Classification task": {
            "task_type": "classification",
            "labels": {
                "small": {
                    "color": "#fffffe",
                    "group": "Default Classification",
                    "parent_id": "dog",
                    "hotkey": "crtl+1",
                },
                "large": {
                    "color": "#fffffd",
                    "group": "Default Classification",
                    "parent_id": "dog",
                    "hotkey": "crtl+2",
                },
            },
        },
    }


@pytest.fixture
def fxt_detection_classification_project_data(
    fxt_detection_classification_tasks,
):
    yield {
        "name": "TEST_dog_detection_crop_small_large_classification_project_data",
        "tasks_dict": fxt_detection_classification_tasks,
    }


@pytest.fixture
def fxt_update_valid_detection_classification_data(fxt_detection_classification_project_data, fxt_mongo_id):
    yield turn_creation_project_data_into_update(fxt_detection_classification_project_data, fxt_mongo_id)


@pytest.fixture
def fxt_update_invalid_detection_classification_project_data_label_addition(
    fxt_detection_classification_project_data, fxt_mongo_id
):
    update_data = turn_creation_project_data_into_update(fxt_detection_classification_project_data, fxt_mongo_id)
    update_data["tasks_dict"]["Classification task"]["labels"]["kitty"] = {
        "color": "#fffffa",
        "group": "Default Classification",
        "parent_id": "cat",
        "hotkey": "crtl+3",
        "is_anomalous": False,
        "is_empty": False,
    }
    yield update_data


@pytest.fixture
def fxt_update_hierarchy_classification_project_data_2(fxt_hierarchy_classification_project_data_2, fxt_mongo_id):
    update_data = turn_creation_project_data_into_update(fxt_hierarchy_classification_project_data_2, fxt_mongo_id)
    update_data["tasks_dict"]["Classification task"]["labels"]["2.2"] = {
        "color": "#c9e649ff",
        "group": "Group 2.X",
        "parent_id": update_data["tasks_dict"]["Classification task"]["labels"]["2"]["id"],
        "hotkey": "",
        "revisit_affected_annotations": True,
    }
    yield update_data


@pytest.fixture
def fxt_invalid_project_data_label_duplication(fxt_detection_classification_project_data):
    project_data = fxt_detection_classification_project_data
    project_data["tasks_dict"]["Classification task"]["labels"]["dog"] = project_data["tasks_dict"][
        "Classification task"
    ]["labels"]["small"]
    del project_data["tasks_dict"]["Classification task"]["labels"]["small"]
    yield project_data


@pytest.fixture
def fxt_update_invalid_project_data_label_duplication(fxt_invalid_project_data_label_duplication, fxt_mongo_id):
    yield turn_creation_project_data_into_update(fxt_invalid_project_data_label_duplication, fxt_mongo_id)


@pytest.fixture
def fxt_binary_classification_project_update_data(fxt_binary_classification_project_data, fxt_mongo_id):
    yield turn_creation_project_data_into_update(fxt_binary_classification_project_data, fxt_mongo_id)


@pytest.fixture
def fxt_detection_classification_project_update_data(fxt_detection_classification_project_data, fxt_mongo_id):
    yield turn_creation_project_data_into_update(fxt_detection_classification_project_data, fxt_mongo_id)


@pytest.fixture
def fxt_label_hierarchy_task_chain_project_update_data(fxt_label_hierarchy_task_chain_project_data, fxt_mongo_id):
    yield turn_creation_project_data_into_update(fxt_label_hierarchy_task_chain_project_data, fxt_mongo_id)


@pytest.fixture
def fxt_update_anomaly_classification_project_data(fxt_anomaly_classification_project_data, fxt_mongo_id):
    update_data = fxt_anomaly_classification_project_data
    update_data["tasks_dict"]["Anomaly task"]["labels"] = {
        "normal": {
            "color": "#fffffe",
            "is_anomalous": False,
            "is_empty": False,
            "group": "default - anomaly_classification",
        },
        "anomalous": {
            "color": "#fffffc",
            "is_anomalous": True,
            "is_empty": False,
            "group": "default - anomaly_classification",
        },
    }
    yield turn_creation_project_data_into_update(update_data, fxt_mongo_id)


@pytest.fixture
def fxt_update_invalid_detection_classification_label_addition(fxt_detection_classification_project_update_data):
    update_data = fxt_detection_classification_project_update_data
    update_data["tasks_dict"]["Detection task"]["labels"]["cat"] = {
        "color": "#fffffa",
        "group": "Default Detection",
        "parent_id": None,
        "hotkey": "crtl+9",
    }
    yield update_data


@pytest.fixture
def fxt_update_invalid_anomaly_label_addition(fxt_update_anomaly_classification_project_data):
    update_data = fxt_update_anomaly_classification_project_data
    del update_data["tasks_dict"]["Anomaly task"]["labels"]["normal"]
    update_data["tasks_dict"]["Anomaly task"]["labels"]["new normal"] = {
        "color": "#fffffa",
        "is_anomalous": False,
        "is_empty": False,
        "group": "default - anomaly_classification",
    }
    yield update_data


@pytest.fixture
def fxt_update_invalid_anomaly_label_deletion(fxt_update_anomaly_classification_project_data):
    update_data = fxt_update_anomaly_classification_project_data
    update_data["tasks_dict"]["Anomaly task"]["labels"]["normal"]["is_deleted"] = True
    yield update_data


@pytest.fixture
def fxt_update_invalid_all_labels_deletion(fxt_detection_classification_project_update_data):
    update_data = fxt_detection_classification_project_update_data
    update_data["tasks_dict"]["Detection task"]["labels"]["dog"]["is_deleted"] = True
    yield update_data


@pytest.fixture
def fxt_update_hotkey_of_deleted_label_reused(fxt_binary_classification_project_update_data):
    update_data = fxt_binary_classification_project_update_data
    update_data["tasks_dict"]["Classification task"]["labels"]["small"]["is_deleted"] = True
    update_data["tasks_dict"]["Classification task"]["labels"]["big"] = {
        "color": "#fffffe",
        "group": "Default Classification",
        "parent_id": None,
        "hotkey": "crtl+1",
    }
    yield update_data


@pytest.fixture
def fxt_update_invalid_project_anomaly_task_without_labels(fxt_anomaly_classification_project_data, fxt_mongo_id):
    yield turn_creation_project_data_into_update(fxt_anomaly_classification_project_data, fxt_mongo_id)


@pytest.fixture
def fxt_update_invalid_project_data_no_tasks(fxt_invalid_project_data_no_tasks, fxt_mongo_id):
    yield turn_creation_project_data_into_update(fxt_invalid_project_data_no_tasks, fxt_mongo_id)


@pytest.fixture
def fxt_update_invalid_project_data_no_empty_name(fxt_invalid_project_data_no_empty_name, fxt_mongo_id):
    yield turn_creation_project_data_into_update(fxt_invalid_project_data_no_empty_name, fxt_mongo_id)


@pytest.fixture
def fxt_update_invalid_project_data_classification_one_label(
    fxt_invalid_project_data_classification_one_label, fxt_mongo_id
):
    yield turn_creation_project_data_into_update(fxt_invalid_project_data_classification_one_label, fxt_mongo_id)


@pytest.fixture
def fxt_update_invalid_project_data_hierarchical_cls_one_top_label(
    fxt_invalid_project_data_hierarchical_cls_one_top_label, fxt_mongo_id
):
    yield turn_creation_project_data_into_update(fxt_invalid_project_data_hierarchical_cls_one_top_label, fxt_mongo_id)


@pytest.fixture
def fxt_update_invalid_project_data_duplicate_label_hotkeys(
    fxt_invalid_project_data_duplicate_label_hotkeys, fxt_mongo_id
):
    yield turn_creation_project_data_into_update(fxt_invalid_project_data_duplicate_label_hotkeys, fxt_mongo_id)


@pytest.fixture
def fxt_update_invalid_project_data_missing_parent_label(fxt_invalid_project_data_missing_parent_label, fxt_mongo_id):
    yield turn_creation_project_data_into_update(fxt_invalid_project_data_missing_parent_label, fxt_mongo_id)


@pytest.fixture
def fxt_update_invalid_project_data_self_referencing_parent(
    fxt_invalid_project_data_self_referencing_parent, fxt_mongo_id
):
    yield turn_creation_project_data_into_update(fxt_invalid_project_data_self_referencing_parent, fxt_mongo_id)


@pytest.fixture
def fxt_update_invalid_project_data_local_task_with_hierarchy(
    fxt_invalid_project_data_local_task_with_hierarchy, fxt_mongo_id
):
    yield turn_creation_project_data_into_update(fxt_invalid_project_data_local_task_with_hierarchy, fxt_mongo_id)


@pytest.fixture
def fxt_update_invalid_project_data_label_group_in_multiple_tasks(
    fxt_invalid_project_data_label_group_in_multiple_tasks, fxt_mongo_id
):
    yield turn_creation_project_data_into_update(fxt_invalid_project_data_label_group_in_multiple_tasks, fxt_mongo_id)


@pytest.fixture
def fxt_update_invalid_project_data_same_group_hierarchical_labels(
    fxt_invalid_project_data_same_group_hierarchical_labels, fxt_mongo_id
):
    yield turn_creation_project_data_into_update(fxt_invalid_project_data_same_group_hierarchical_labels, fxt_mongo_id)


@pytest.fixture
def fxt_update_invalid_project_data_empty_label_name_conflict(
    fxt_invalid_project_data_empty_label_name_conflict, fxt_mongo_id
):
    yield turn_creation_project_data_into_update(fxt_invalid_project_data_empty_label_name_conflict, fxt_mongo_id)


@pytest.fixture
def fxt_detection_to_segmentation_project_data():
    yield {
        "name": "Test detection project",
        "tasks_dict": {
            "Dataset": {"task_type": "dataset"},
            "Detection task": {
                "task_type": "detection",
                "labels": {
                    "car": {
                        "color": "#ffffff",
                        "group": "Default Detection",
                        "parent_id": None,
                        "hotkey": "crtl+0",
                    }
                },
            },
            "Crop task": {"task_type": "crop"},
            "Segmentation task": {
                "task_type": "segmentation",
                "labels": {
                    "car wheel": {
                        "color": "#fffffe",
                        "group": "Default Segmentation",
                        "parent_id": None,
                        "hotkey": "crtl+2",
                    },
                    "car window": {
                        "color": "#fffffc",
                        "group": "Default Segmentation",
                        "parent_id": None,
                        "hotkey": "crtl+3",
                    },
                },
            },
        },
    }


@pytest.fixture
def fxt_segmentation_project_data():
    yield {
        "name": "Test segmentation project",
        "tasks_dict": {
            "Dataset": {"task_type": "dataset"},
            "Segmentation task": {
                "task_type": "segmentation",
                "labels": {
                    "segment_me": {
                        "color": "#fffffe",
                        "group": "Default Segmentation",
                        "parent_id": None,
                        "hotkey": "crtl+1",
                    },
                },
            },
        },
    }


@pytest.fixture
def fxt_anomaly_classification_project_data():
    yield {
        "name": "Test anomaly classification  project",
        "tasks_dict": {
            "Dataset": {"task_type": "dataset"},
            "Anomaly task": {"task_type": "anomaly_classification"},
        },
    }


@pytest.fixture
def fxt_invalid_anomaly_classification_project_data(fxt_anomaly_classification_project_data):
    fxt_anomaly_classification_project_data["tasks_dict"]["Anomaly task"]["labels"] = {
        "car wheel": {
            "color": "#fffffe",
            "group": "Default Segmentation",
            "parent_id": None,
            "hotkey": "crtl+2",
        },
        "car window": {
            "color": "#fffffc",
            "group": "Default Segmentation",
            "parent_id": None,
            "hotkey": "crtl+3",
        },
    }
    yield fxt_anomaly_classification_project_data


@pytest.fixture
def fxt_invalid_project_data_no_tasks():
    yield {
        "name": "Test segmentation project",
        "tasks_dict": {},
    }


@pytest.fixture
def fxt_invalid_project_data_no_empty_name(fxt_anomaly_classification_project_data):
    fxt_anomaly_classification_project_data["name"] = "    \n"
    yield fxt_anomaly_classification_project_data


@pytest.fixture
def fxt_invalid_project_data_classification_one_label(fxt_binary_classification_project_data):
    fxt_binary_classification_project_data["tasks_dict"]["Classification task"]["labels"] = {"dummy_name": {}}
    yield fxt_binary_classification_project_data


@pytest.fixture
def fxt_invalid_project_data_hierarchical_cls_one_top_label(fxt_binary_classification_project_data):
    fxt_binary_classification_project_data["tasks_dict"]["Classification task"]["labels"] = {
        "top_name": {},
        "second_name": {"parent_id": "top_name"},
    }
    yield fxt_binary_classification_project_data


@pytest.fixture
def fxt_invalid_project_data_duplicate_label_hotkeys(fxt_binary_classification_project_data):
    fxt_binary_classification_project_data["tasks_dict"]["Classification task"]["labels"] = {
        "top_name": {"hotkey": "crtl+3"},
        "second_name": {"hotkey": "crtl+3"},
    }
    yield fxt_binary_classification_project_data


@pytest.fixture
def fxt_invalid_project_data_missing_parent_label(fxt_binary_classification_project_data):
    fxt_binary_classification_project_data["tasks_dict"]["Classification task"]["labels"]["new_label"] = {
        "parent_id": "not existing one"
    }
    yield fxt_binary_classification_project_data


@pytest.fixture
def fxt_invalid_project_data_local_task_with_hierarchy(fxt_segmentation_project_data):
    fxt_segmentation_project_data["tasks_dict"]["Segmentation task"]["labels"]["new_label"] = {
        "parent_id": "not existing one"
    }
    yield fxt_segmentation_project_data


@pytest.fixture
def fxt_invalid_project_data_self_referencing_parent(fxt_binary_classification_project_data):
    fxt_binary_classification_project_data["tasks_dict"]["Classification task"]["labels"]["new_label"] = {
        "parent_id": "new_label"
    }
    yield fxt_binary_classification_project_data


@pytest.fixture
def fxt_invalid_project_data_label_group_in_multiple_tasks(fxt_detection_classification_project_data):
    fxt_detection_classification_project_data["tasks_dict"]["Classification task"]["labels"]["new_label"] = {
        "group": "group_name"
    }
    fxt_detection_classification_project_data["tasks_dict"]["Detection task"]["labels"]["another_label"] = {
        "group": "group_name"
    }
    yield fxt_detection_classification_project_data


@pytest.fixture
def fxt_invalid_project_data_same_group_hierarchical_labels(fxt_binary_classification_project_data):
    fxt_binary_classification_project_data["tasks_dict"]["Classification task"]["labels"] = {
        "label one": {"parent_id": "label two", "group": "grp 1"},
        "label two": {"group": "grp 2"},
        "label three": {"parent_id": "label four", "group": "grp 1"},
        "label four": {"group": "grp 2"},
    }
    yield fxt_binary_classification_project_data


@pytest.fixture
def fxt_invalid_project_data_empty_label_name_conflict(fxt_detection_classification_project_data):
    fxt_detection_classification_project_data["tasks_dict"]["Detection task"]["labels"]["No object"] = {
        "group": "group_name"
    }
    yield fxt_detection_classification_project_data


@pytest.fixture
def fxt_invalid_project_data_label_in_non_trainable_task():
    yield {
        "name": "Label in Dataset task",
        "tasks_dict": {
            "Dataset": {"task_type": "dataset", "labels": {"should not be here": {"group": "group_name"}}},
            "Crop": {"task_type": "crop"},
        },
    }


@pytest.fixture
def fxt_label_hierarchy_task_chain_project_data():
    yield {
        "name": "Test hierarchy project",
        "tasks_dict": {
            "Dataset": {"task_type": "dataset"},
            "Detection task": {
                "task_type": "detection",
                "labels": {
                    "dog": {
                        "color": "#ffffff",
                        "group": "Default detection",
                        "parent_id": None,
                        "hotkey": "crtl+0",
                    },
                    "cat": {
                        "name": "cat",
                        "color": "#ff0000",
                        "group": "Default detection",
                        "parent_id": None,
                        "hotkey": "crtl+1",
                    },
                },
            },
            "Crop task": {"task_type": "crop"},
            "Classification task": {
                "task_type": "classification",
                "labels": {
                    "big dog": {
                        "color": "#fffffe",
                        "group": "Dog",
                        "parent_id": "dog",
                        "hotkey": "crtl+2",
                    },
                    "small dog": {
                        "color": "#fffffc",
                        "group": "Dog",
                        "parent_id": "dog",
                        "hotkey": "crtl+3",
                    },
                    "big cat": {
                        "color": "#fffffd",
                        "group": "Cat",
                        "parent_id": "cat",
                        "hotkey": "crtl+4",
                    },
                    "small cat": {
                        "color": "#fffffb",
                        "group": "Cat",
                        "parent_id": "cat",
                        "hotkey": "crtl+5",
                    },
                },
            },
        },
    }


@pytest.fixture
def fxt_keypoint_detection_project_data():
    yield {
        "name": "Test keypoint detection project",
        "tasks_dict": {
            "Dataset": {"task_type": "dataset"},
            "Keypoint detection task": {
                "task_type": "Keypoint_detection",
                "labels": {
                    "head": {
                        "color": "#09FF27",
                        "group": "Default keypoint detection",
                        "parent_id": None,
                        "hotkey": "crtl+0",
                    },
                    "neck": {
                        "color": "#FF7809",
                        "group": "Default keypoint detection",
                        "parent_id": None,
                        "hotkey": "crtl+1",
                    },
                    "back": {
                        "color": "#0919FF",
                        "group": "Default keypoint detection",
                        "parent_id": None,
                        "hotkey": "crtl+2",
                    },
                    "left_shoulder": {
                        "color": "#FF09BD",
                        "group": "Default keypoint detection",
                        "parent_id": None,
                        "hotkey": "crtl+3",
                    },
                    "right_shoulder": {
                        "color": "#FF0909",
                        "group": "Default keypoint detection",
                        "parent_id": None,
                        "hotkey": "crtl+4",
                    },
                },
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
            },
        },
    }


@pytest.fixture
def fxt_keypoint_detection_duplicate_edge_project_data(fxt_keypoint_detection_project_data):
    data = fxt_keypoint_detection_project_data
    data["tasks_dict"]["Keypoint detection task"]["keypoint_structure"]["edges"].append(
        {"nodes": ["neck", "right_shoulder"]}
    )
    yield data


@pytest.fixture
def fxt_keypoint_detection_too_many_nodes_project_data(fxt_keypoint_detection_project_data):
    data = fxt_keypoint_detection_project_data
    data["tasks_dict"]["Keypoint detection task"]["keypoint_structure"]["edges"].append(
        {"nodes": ["neck", "right_shoulder", "left_shoulder"]}
    )
    yield data


@pytest.fixture
def fxt_keypoint_detection_invalid_node_name_project_data(fxt_keypoint_detection_project_data):
    data = fxt_keypoint_detection_project_data
    data["tasks_dict"]["Keypoint detection task"]["keypoint_structure"]["edges"].append(
        {"nodes": ["", "right_shoulder"]}
    )
    yield data


@pytest.fixture
def fxt_keypoint_detection_valid_update_project_data(fxt_keypoint_detection_project_data, fxt_mongo_id):
    data = turn_creation_project_data_into_update(fxt_keypoint_detection_project_data, fxt_mongo_id)
    data["tasks_dict"]["Keypoint detection task"]["labels"]["hip"] = {
        "color": "#FF0909",
        "group": "Default keypoint detection",
        "parent_id": None,
        "hotkey": "crtl+5",
    }
    data["tasks_dict"]["Keypoint detection task"]["keypoint_structure"]["edges"].append({"nodes": ["hip", "back"]})
    data["tasks_dict"]["Keypoint detection task"]["keypoint_structure"]["positions"].append(
        {"label": "hip", "x": 0.5, "y": 0.5}
    )
    yield data

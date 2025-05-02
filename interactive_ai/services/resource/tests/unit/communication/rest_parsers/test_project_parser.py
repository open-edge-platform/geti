# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import logging

import pytest

from communication.rest_parsers import RestProjectParser, RestProjectUpdateParser

from geti_types import ID
from iai_core_py.entities.model_template import TaskType

logger = logging.getLogger(__name__)


@pytest.fixture
def fxt_create_project_multilabel_classification_rest_body():
    yield {
        "name": "TestMultilabelClassification",
        "pipeline": {
            "connections": [{"from": "Dataset", "to": "Classification task"}],
            "tasks": [
                {"title": "Dataset", "task_type": "dataset"},
                {
                    "title": "Classification task",
                    "task_type": "classification",
                    "labels": [
                        {
                            "name": "label_A",
                            "color": "#9b5de5ff",
                            "group": "Classification labels___label_A",
                            "parent_id": None,
                            "hotkey": "SHIFT+A",
                        },
                        {
                            "name": "label_B",
                            "color": "#80e9afff",
                            "group": "Classification labels___label_B",
                            "parent_id": None,
                            "hotkey": "SHIFT+B",
                        },
                        {
                            "name": "label_C",
                            "color": "#708541ff",
                            "group": "Classification labels___label_C",
                            "parent_id": None,
                            "hotkey": "SHIFT+C",
                        },
                    ],
                },
            ],
        },
    }


@pytest.fixture
def fxt_create_project_hierarchical_classification_rest_body():
    yield {
        "name": "TestClassificationHierarchical",
        "pipeline": {
            "connections": [{"from": "Dataset", "to": "Classification task"}],
            "tasks": [
                {"title": "Dataset", "task_type": "dataset"},
                {
                    "title": "Classification task",
                    "task_type": "classification",
                    "labels": [
                        {
                            "name": "label_A",
                            "color": "#81407bff",
                            "group": "group_root",
                            "parent_id": None,
                            "hotkey": "",
                        },
                        {
                            "name": "label_A_1",
                            "color": "#00a5cfff",
                            "group": "group_root___group_A",
                            "parent_id": "label_A",
                            "hotkey": "",
                        },
                        {
                            "name": "label_A_1_x",
                            "color": "#9d3b1aff",
                            "group": "group_root___group_A___group_A_1",
                            "parent_id": "label_A_1",
                            "hotkey": "",
                        },
                        {
                            "name": "label_A_1_y",
                            "color": "#9b5de5ff",
                            "group": "group_root___group_A___group_A_1",
                            "parent_id": "label_A_1",
                            "hotkey": "",
                        },
                        {
                            "name": "label_A_2",
                            "color": "#25a18eff",
                            "group": "group_root___group_A",
                            "parent_id": "label_A",
                            "hotkey": "",
                        },
                        {
                            "name": "label_B",
                            "color": "#ff5662ff",
                            "group": "group_root",
                            "parent_id": None,
                            "hotkey": "",
                        },
                    ],
                },
            ],
        },
    }


@pytest.fixture
def fxt_create_project_anomaly_rest_body():
    yield {
        "name": "TestAnomaly",
        "pipeline": {
            "connections": [{"from": "Dataset", "to": "Anomaly task"}],
            "tasks": [
                {"title": "Dataset", "task_type": "dataset"},
                {
                    "title": "Anomaly task",
                    "task_type": "anomaly",
                    "labels": [],
                },
            ],
        },
    }


@pytest.fixture
def fxt_create_project_detection_classification_rest_body():
    yield {
        "name": "TestDetectionClassification",
        "pipeline": {
            "connections": [
                {"from": "Dataset", "to": "Detection task"},
                {"from": "Detection task", "to": "Crop task"},
                {"from": "Crop task", "to": "Classification task"},
            ],
            "tasks": [
                {"title": "Dataset", "task_type": "dataset"},
                {
                    "title": "Detection task",
                    "task_type": "detection",
                    "labels": [
                        {
                            "name": "label_det",
                            "color": "#e96115ff",
                            "group": "default_detection",
                            "parent_id": None,
                        }
                    ],
                },
                {
                    "title": "Classification task",
                    "task_type": "classification",
                    "labels": [
                        {
                            "name": "label_cls_A",
                            "color": "#708541ff",
                            "group": "default_classification",
                            "parent_id": None,
                            "hotkey": "",
                        },
                        {
                            "name": "label_cls_B",
                            "color": "#80e9afff",
                            "group": "default_classification",
                            "parent_id": None,
                            "hotkey": "",
                        },
                    ],
                },
                {"title": "Crop task", "task_type": "crop"},
            ],
        },
    }


@pytest.fixture
def fxt_update_project_change_name():
    yield {
        "creation_time": "Wed, 01 Mar 2023 08:31:46 GMT",
        "id": "63ff0d72be67f5fb6749feb1",
        "name": "TestMultilabelClassificationUpdated",
        "pipeline": {
            "connections": [{"from": "63ff0d72be67f5fb6749feaf", "to": "63ff0d72be67f5fb6749feb0"}],
            "tasks": [
                {
                    "id": "63ff0d72be67f5fb6749feaf",
                    "task_type": "dataset",
                    "title": "Dataset",
                },
                {
                    "id": "63ff0d72be67f5fb6749feb0",
                    "task_type": "classification",
                    "title": "Classification task",
                    "labels": [
                        {
                            "id": "63ff0d72be67f5fb6749feb8",
                            "name": "label_A",
                            "color": "#9b5de5ff",
                            "group": "Classification labels___label_A",
                            "hotkey": "SHIFT+A",
                            "parent_id": None,
                            "is_empty": False,
                            "is_anomalous": False,
                        },
                        {
                            "id": "63ff0d72be67f5fb6749feba",
                            "name": "label_B",
                            "color": "#80e9afff",
                            "group": "Classification labels___label_B",
                            "hotkey": "SHIFT+B",
                            "parent_id": None,
                            "is_empty": False,
                            "is_anomalous": False,
                        },
                        {
                            "id": "63ff0d72be67f5fb6749febc",
                            "name": "label_C",
                            "color": "#708541ff",
                            "group": "Classification labels___label_C",
                            "hotkey": "SHIFT+C",
                            "parent_id": None,
                            "is_empty": False,
                            "is_anomalous": False,
                        },
                        {
                            "id": "63ff0d72be67f5fb6749febe",
                            "name": "No class",
                            "color": "#9ecb55ff",
                            "group": "No class",
                            "hotkey": "",
                            "parent_id": None,
                            "is_empty": True,
                            "is_anomalous": False,
                        },
                    ],
                },
            ],
        },
        "performance": {
            "score": None,
            "task_performances": [
                {
                    "task_id": "63ff0d72be67f5fb6749feb0",
                    "score": None,
                },
            ],
        },
        "thumbnail": "/api/v1/organizations/60d31793d5f1fb7e6e3c1a4e/workspaces/63fcd417be67f5fb6749fe18"
        "/projects/63ff0d72be67f5fb6749feb1/thumbnail",
        "datasets": [
            {
                "id": "63ff0d72be67f5fb6749feb2",
                "name": "Dataset",
                "use_for_training": True,
                "creation_time": "2023-03-01T08:31:46.055000+00:00",
            }
        ],
    }


@pytest.fixture
def fxt_update_project_add_remove_labels():
    yield {
        "creation_time": "Wed, 01 Mar 2023 08:31:46 GMT",
        "id": "63ff0d72be67f5fb6749feb1",
        "name": "TestMultilabelClassification",
        "pipeline": {
            "connections": [{"from": "63ff0d72be67f5fb6749feaf", "to": "63ff0d72be67f5fb6749feb0"}],
            "tasks": [
                {
                    "id": "63ff0d72be67f5fb6749feaf",
                    "task_type": "dataset",
                    "title": "Dataset",
                },
                {
                    "id": "63ff0d72be67f5fb6749feb0",
                    "task_type": "classification",
                    "title": "Classification task",
                    "labels": [
                        {
                            "id": "63ff0d72be67f5fb6749feb8",
                            "name": "label_A",
                            "color": "#9b5de5ff",
                            "group": "Classification labels___label_A",
                            "hotkey": "SHIFT+A",
                            "parent_id": None,
                            "is_empty": False,
                            "is_anomalous": False,
                        },
                        {
                            "id": "63ff0d72be67f5fb6749feba",
                            "name": "label_B",
                            "color": "#80e9afff",
                            "group": "Classification labels___label_B",
                            "hotkey": "SHIFT+B",
                            "parent_id": None,
                            "is_empty": False,
                            "is_anomalous": False,
                        },
                        {
                            "name": "label_C",
                            "color": "#708541ff",
                            "group": "Classification labels___label_C",
                            "hotkey": "SHIFT+C",
                            "parent_id": None,
                            "is_empty": False,
                            "is_anomalous": False,
                            "id": "63ff0d72be67f5fb6749febc",
                            "is_deleted": True,
                        },
                        {
                            "name": "label_new",
                            "color": "#00f5d4ff",
                            "group": "Classification labels___label_new",
                            "hotkey": "",
                            "parent_id": None,
                            "is_empty": False,
                            "is_anomalous": False,
                            "revisit_affected_annotations": True,
                        },
                    ],
                },
            ],
        },
        "performance": {
            "score": None,
            "task_performances": [
                {
                    "task_id": "63ff0d72be67f5fb6749feb0",
                    "score": None,
                },
            ],
        },
        "thumbnail": "/api/v1/organizations/60d31793d5f1fb7e6e3c1a4e/workspaces/63fcd417be67f5fb6749fe18"
        "/projects/63ff0d72be67f5fb6749feb1/thumbnail",
        "datasets": [
            {
                "id": "63ff0d72be67f5fb6749feb2",
                "name": "Dataset",
                "use_for_training": True,
                "creation_time": "2023-03-01T08:31:46.055000+00:00",
            }
        ],
    }


class TestRestProjectParser:
    """Unit tests for RestProjectParser"""

    def test_get_project_name(self, fxt_create_project_multilabel_classification_rest_body) -> None:
        rest_data: dict = fxt_create_project_multilabel_classification_rest_body
        parser = RestProjectParser(rest_data=rest_data)

        parsed_project_name = parser.get_project_name()

        assert parsed_project_name == "TestMultilabelClassification"

    def test_get_connections(self, fxt_create_project_detection_classification_rest_body) -> None:
        rest_data: dict = fxt_create_project_detection_classification_rest_body
        parser = RestProjectParser(rest_data=rest_data)

        parsed_connections = parser.get_connections()

        expected_connections = {
            ("Dataset", "Detection task"),
            ("Detection task", "Crop task"),
            ("Crop task", "Classification task"),
        }
        assert set(parsed_connections) == expected_connections

    def test_get_tasks_names(self, fxt_create_project_detection_classification_rest_body) -> None:
        rest_data: dict = fxt_create_project_detection_classification_rest_body
        parser = RestProjectParser(rest_data=rest_data)

        parsed_tasks = parser.get_tasks_names()

        expected_tasks = {
            "Dataset",
            "Detection task",
            "Crop task",
            "Classification task",
        }
        assert set(parsed_tasks) == expected_tasks

    def test_get_task_type_by_name(self, fxt_create_project_detection_classification_rest_body) -> None:
        rest_data: dict = fxt_create_project_detection_classification_rest_body
        parser = RestProjectParser(rest_data=rest_data)
        task_dataset_name = "Dataset"
        task_detection_name = "Detection task"
        task_crop_name = "Crop task"
        task_classification_name = "Classification task"

        parsed_dataset_task_type = parser.get_task_type_by_name(task_dataset_name)
        parsed_detection_task_type = parser.get_task_type_by_name(task_detection_name)
        parsed_crop_task_type = parser.get_task_type_by_name(task_crop_name)
        parsed_classification_task_type = parser.get_task_type_by_name(task_classification_name)

        assert parsed_dataset_task_type == TaskType.DATASET
        assert parsed_detection_task_type == TaskType.DETECTION
        assert parsed_crop_task_type == TaskType.CROP
        assert parsed_classification_task_type == TaskType.CLASSIFICATION

    @pytest.mark.parametrize(
        "task_name,expected_labels",
        [
            ("Classification task", {"label_A", "label_B", "label_C"}),
            ("Anomaly task", set()),
        ],
        ids=["classification", "anomaly"],
    )
    def test_get_custom_labels_names_by_task(
        self,
        fxt_create_project_multilabel_classification_rest_body,
        fxt_create_project_anomaly_rest_body,
        task_name,
        expected_labels,
    ) -> None:
        rest_data: dict
        if task_name == "Classification task":
            rest_data = fxt_create_project_multilabel_classification_rest_body
        elif task_name == "Anomaly task":
            rest_data = fxt_create_project_anomaly_rest_body
        else:
            raise ValueError("Invalid task name")
        parser = RestProjectParser(rest_data=rest_data)

        parsed_label_names = parser.get_custom_labels_names_by_task(task_name=task_name)

        assert set(parsed_label_names) == expected_labels

    def test_get_label_group_by_name(self, fxt_create_project_multilabel_classification_rest_body) -> None:
        rest_data: dict = fxt_create_project_multilabel_classification_rest_body
        parser = RestProjectParser(rest_data=rest_data)
        expected_group_by_label = {
            "label_A": "Classification labels___label_A",
            "label_B": "Classification labels___label_B",
            "label_C": "Classification labels___label_C",
        }

        for label_name, expected_label_group_name in expected_group_by_label.items():
            parsed_label_group_name = parser.get_label_group_by_name(
                task_name="Classification task",
                label_name=label_name,
            )

            assert parsed_label_group_name == expected_label_group_name

    def test_get_label_hotkey_by_name(self, fxt_create_project_multilabel_classification_rest_body) -> None:
        rest_data: dict = fxt_create_project_multilabel_classification_rest_body
        parser = RestProjectParser(rest_data=rest_data)
        expected_hotkey_by_label = {
            "label_A": "SHIFT+A",
            "label_B": "SHIFT+B",
            "label_C": "SHIFT+C",
        }

        for label_name, expected_label_hotkey in expected_hotkey_by_label.items():
            parsed_label_hotkey = parser.get_label_hotkey_by_name(
                task_name="Classification task",
                label_name=label_name,
            )

            assert parsed_label_hotkey == expected_label_hotkey

    def test_get_label_color_by_name(self, fxt_create_project_multilabel_classification_rest_body) -> None:
        rest_data: dict = fxt_create_project_multilabel_classification_rest_body
        parser = RestProjectParser(rest_data=rest_data)
        expected_color_by_label = {
            "label_A": "#9b5de5ff",
            "label_B": "#80e9afff",
            "label_C": "#708541ff",
        }

        for label_name, expected_label_color in expected_color_by_label.items():
            logger.info("Checking label %s", label_name)
            parsed_label_color = parser.get_label_color_by_name(
                task_name="Classification task",
                label_name=label_name,
            )

            assert parsed_label_color == expected_label_color

    def test_get_label_parent_by_name(self, fxt_create_project_hierarchical_classification_rest_body) -> None:
        rest_data: dict = fxt_create_project_hierarchical_classification_rest_body
        parser = RestProjectParser(rest_data=rest_data)
        expected_parent_by_label = {
            "label_A": "",
            "label_B": "",
            "label_A_1": "label_A",
            "label_A_2": "label_A",
            "label_A_1_x": "label_A_1",
            "label_A_1_y": "label_A_1",
        }

        for label_name, expected_label_parent in expected_parent_by_label.items():
            logger.info("Checking label %s", label_name)
            parsed_label_parent = parser.get_label_parent_by_name(
                task_name="Classification task",
                label_name=label_name,
            )

            assert parsed_label_parent == expected_label_parent


class TestRestProjectUpdateParser:
    """Unit tests for RestProjectUpdateParser"""

    def test_get_project_name(self, fxt_update_project_change_name) -> None:
        rest_data: dict = fxt_update_project_change_name
        parser = RestProjectUpdateParser(rest_data=rest_data)

        parsed_project_name = parser.get_project_name()

        assert parsed_project_name == "TestMultilabelClassificationUpdated"

    def test_get_connections(self, fxt_update_project_change_name) -> None:
        rest_data: dict = fxt_update_project_change_name
        parser = RestProjectUpdateParser(rest_data=rest_data)

        parsed_connections = parser.get_connections()

        expected_connections = {("63ff0d72be67f5fb6749feaf", "63ff0d72be67f5fb6749feb0")}
        assert set(parsed_connections) == expected_connections

    def test_get_tasks_names(self, fxt_update_project_change_name) -> None:
        rest_data: dict = fxt_update_project_change_name
        parser = RestProjectUpdateParser(rest_data=rest_data)

        parsed_tasks = parser.get_tasks_names()

        expected_tasks = {
            "Dataset",
            "Classification task",
        }
        assert set(parsed_tasks) == expected_tasks

    def test_get_task_type_by_name(self, fxt_update_project_change_name) -> None:
        rest_data: dict = fxt_update_project_change_name
        parser = RestProjectUpdateParser(rest_data=rest_data)
        task_dataset_name = "Dataset"
        task_classification_name = "Classification task"

        parsed_dataset_task_type = parser.get_task_type_by_name(task_dataset_name)
        parsed_classification_task_type = parser.get_task_type_by_name(task_classification_name)

        assert parsed_dataset_task_type == TaskType.DATASET
        assert parsed_classification_task_type == TaskType.CLASSIFICATION

    @pytest.mark.parametrize(
        "lazyfxt_update_request, expected_labels",
        [
            ("fxt_update_project_change_name", {"label_A", "label_B", "label_C"}),
            # note: 'label_C' is deleted but still present in the request
            (
                "fxt_update_project_add_remove_labels",
                {"label_A", "label_B", "label_C", "label_new"},
            ),
        ],
    )
    def test_get_custom_labels_names_by_task(self, request, lazyfxt_update_request, expected_labels) -> None:
        rest_data: dict = request.getfixturevalue(lazyfxt_update_request)
        parser = RestProjectUpdateParser(rest_data=rest_data)

        parsed_label_names = parser.get_custom_labels_names_by_task(task_name="Classification task")

        assert set(parsed_label_names) == expected_labels

    def test_get_label_group_by_name(self, fxt_update_project_change_name) -> None:
        rest_data: dict = fxt_update_project_change_name
        parser = RestProjectUpdateParser(rest_data=rest_data)
        expected_group_by_label = {
            "label_A": "Classification labels___label_A",
            "label_B": "Classification labels___label_B",
            "label_C": "Classification labels___label_C",
        }

        for label_name, expected_label_group_name in expected_group_by_label.items():
            parsed_label_group_name = parser.get_label_group_by_name(
                task_name="Classification task",
                label_name=label_name,
            )

            assert parsed_label_group_name == expected_label_group_name

    def test_get_label_hotkey_by_name(self, fxt_update_project_change_name) -> None:
        rest_data: dict = fxt_update_project_change_name
        parser = RestProjectUpdateParser(rest_data=rest_data)
        expected_hotkey_by_label = {
            "label_A": "SHIFT+A",
            "label_B": "SHIFT+B",
            "label_C": "SHIFT+C",
        }

        for label_name, expected_label_hotkey in expected_hotkey_by_label.items():
            parsed_label_hotkey = parser.get_label_hotkey_by_name(
                task_name="Classification task",
                label_name=label_name,
            )

            assert parsed_label_hotkey == expected_label_hotkey

    def test_get_label_color_by_name(self, fxt_update_project_change_name) -> None:
        rest_data: dict = fxt_update_project_change_name
        parser = RestProjectUpdateParser(rest_data=rest_data)
        expected_color_by_label = {
            "label_A": "#9b5de5ff",
            "label_B": "#80e9afff",
            "label_C": "#708541ff",
        }

        for label_name, expected_label_color in expected_color_by_label.items():
            logger.info("Checking label %s", label_name)
            parsed_label_color = parser.get_label_color_by_name(
                task_name="Classification task",
                label_name=label_name,
            )

            assert parsed_label_color == expected_label_color

    def test_get_label_parent_by_name(self, fxt_update_project_change_name) -> None:
        rest_data: dict = fxt_update_project_change_name
        parser = RestProjectUpdateParser(rest_data=rest_data)
        expected_parent_by_label = {
            "label_A": "",
            "label_B": "",
            "label_C": "",
        }

        for label_name, expected_label_parent in expected_parent_by_label.items():
            logger.info("Checking label %s", label_name)
            parsed_label_parent = parser.get_label_parent_by_name(
                task_name="Classification task",
                label_name=label_name,
            )

            assert parsed_label_parent == expected_label_parent

    def test_get_task_id_by_name(self, fxt_update_project_change_name) -> None:
        rest_data: dict = fxt_update_project_change_name
        parser = RestProjectUpdateParser(rest_data=rest_data)

        parsed_task_id = parser.get_task_id_by_name(task_name="Classification task")

        assert parsed_task_id == ID("63ff0d72be67f5fb6749feb0")

    def test_get_label_id_by_name(self, fxt_update_project_change_name) -> None:
        rest_data: dict = fxt_update_project_change_name
        parser = RestProjectUpdateParser(rest_data=rest_data)

        parsed_label_id = parser.get_label_id_by_name(task_name="Classification task", label_name="label_A")

        assert parsed_label_id == ID("63ff0d72be67f5fb6749feb8")

    def test_get_added_labels_names_by_task(self, fxt_update_project_add_remove_labels) -> None:
        rest_data: dict = fxt_update_project_add_remove_labels
        parser = RestProjectUpdateParser(rest_data=rest_data)

        parsed_added_labels = parser.get_added_labels_names_by_task(task_name="Classification task")

        expected_parsed_added_labels = {"label_new"}
        assert set(parsed_added_labels) == expected_parsed_added_labels

    def test_get_deleted_labels_names_by_task(self, fxt_update_project_add_remove_labels) -> None:
        rest_data: dict = fxt_update_project_add_remove_labels
        parser = RestProjectUpdateParser(rest_data=rest_data)

        parsed_deleted_labels = parser.get_deleted_labels_names_by_task(task_name="Classification task")

        expected_parsed_deleted_labels = {"label_C"}
        assert set(parsed_deleted_labels) == expected_parsed_deleted_labels

    def test_get_revisit_state_by_label_name(self, fxt_update_project_add_remove_labels) -> None:
        rest_data: dict = fxt_update_project_add_remove_labels
        parser = RestProjectUpdateParser(rest_data=rest_data)

        parsed_revisit_state = parser.get_revisit_state_by_label_name(
            task_name="Classification task", label_name="label_new"
        )

        assert parsed_revisit_state is True

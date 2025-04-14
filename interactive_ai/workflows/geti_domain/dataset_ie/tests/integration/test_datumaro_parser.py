# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from typing import Any

import datumaro as dm
import pytest
from jobs_common_extras.datumaro_conversion.convert_utils import ConvertUtils
from jobs_common_extras.datumaro_conversion.definitions import ANOMALY_PROJECT_TYPES, GetiProjectType
from sc_sdk.entities.model_template import TaskType

from job.utils.datumaro_parser import DatumaroProjectParser
from job.utils.exceptions import DatasetParsingException
from job.utils.import_utils import ImportUtils


@pytest.mark.DatasetIEMsComponent
class TestDatumaroProjectParser:
    @pytest.mark.parametrize(
        "fxt_dm_dataset_str, project_type",
        [
            ["fxt_datumaro_dataset", GetiProjectType.CLASSIFICATION],
            ["fxt_datumaro_dataset", GetiProjectType.DETECTION],
            ["fxt_datumaro_dataset_segmentation", GetiProjectType.SEGMENTATION],
            ["fxt_datumaro_dataset_instances_segmentation", GetiProjectType.INSTANCE_SEGMENTATION],
            ["fxt_datumaro_dataset_multi_label", GetiProjectType.CLASSIFICATION],
            ["fxt_datumaro_dataset_hierarchical", GetiProjectType.CLASSIFICATION],
            [
                "fxt_datumaro_dataset_rotated_detection",
                GetiProjectType.ROTATED_DETECTION,
            ],
            [
                "fxt_datumaro_dataset_anomaly_cls",
                GetiProjectType.ANOMALY_CLASSIFICATION,
            ],
            ["fxt_datumaro_dataset_anomaly_det", GetiProjectType.ANOMALY_DETECTION],
            [
                "fxt_datumaro_dataset_anomaly_seg",
                GetiProjectType.ANOMALY_SEGMENTATION,
            ],
        ],
    )
    def test_datumaro_parser_single_task(self, request, fxt_dm_dataset_str, project_type):  # noqa: C901
        fxt_datumaro_dataset = request.getfixturevalue(fxt_dm_dataset_str)

        project_name = f"test_datumaro_parser_{project_type.name.lower()}"

        is_anomaly_project = project_type in ANOMALY_PROJECT_TYPES

        # Assume that the user selects all annotated labels
        dm_annotated_label_ids = set()
        for dm_item in fxt_datumaro_dataset:
            dm_annotated_label_ids.update([dm_ann.label for dm_ann in dm_item.annotations])

        # Extract label_meta from the dm_dataset
        # label_meta contains 'name', 'color', and 'hotkey' of label
        dm_label_cate = fxt_datumaro_dataset.categories()[dm.AnnotationType.label]
        dm_label_names = [
            dm_label_info.name
            for dm_label_id, dm_label_info in enumerate(dm_label_cate.items)
            if dm_label_id in dm_annotated_label_ids
        ]

        # Filter label_meta by task_type
        # Get group, parent of labels from the dm_dataset
        (dm_groups, dm_labelname_to_parent, dm_label_metas) = ConvertUtils.get_label_metadata(
            dm_categories=fxt_datumaro_dataset.categories(),
            dm_infos=fxt_datumaro_dataset.infos(),
            selected_labels=dm_label_names,
            project_type=project_type,
        )

        # Store group, parent of label for easy testing
        dm_labelname_to_group = {}
        if dm_groups is not None:
            for dm_group in dm_groups:
                group_name = dm_group["name"]
                for label_name in dm_group["labels"]:
                    dm_labelname_to_group[label_name] = group_name
        if dm_labelname_to_parent is None:
            dm_labelname_to_parent = {}

        # Call DatumaroProjectParser
        dm_parser = DatumaroProjectParser(
            project_name=project_name,
            project_type=project_type,
            dm_infos=fxt_datumaro_dataset.infos(),
            dm_categories=fxt_datumaro_dataset.categories(),
            label_to_ann_types=ImportUtils.get_label_to_ann_types(dm_dataset=fxt_datumaro_dataset),
            selected_labels=dm_label_names,
        )

        project_type_to_last_task_type = {
            GetiProjectType.CLASSIFICATION: TaskType.CLASSIFICATION,
            GetiProjectType.DETECTION: TaskType.DETECTION,
            GetiProjectType.SEGMENTATION: TaskType.SEGMENTATION,
            GetiProjectType.INSTANCE_SEGMENTATION: TaskType.INSTANCE_SEGMENTATION,
            GetiProjectType.ROTATED_DETECTION: TaskType.ROTATED_DETECTION,
            GetiProjectType.ANOMALY_CLASSIFICATION: TaskType.ANOMALY_CLASSIFICATION,
            GetiProjectType.ANOMALY_DETECTION: TaskType.ANOMALY_DETECTION,
            GetiProjectType.ANOMALY_SEGMENTATION: TaskType.ANOMALY_SEGMENTATION,
        }
        last_task_type = project_type_to_last_task_type[project_type]
        last_task_name = dm_parser.get_tasks_names()[-1]

        expected_task_names = []
        for task_type in [TaskType.DATASET, last_task_type]:
            expected_task_names.append(
                f"{ImportUtils.task_type_to_rest_api_string(task_type).replace('_', ' ').title()}"
            )

        expected_connections = []
        for i in range(len(expected_task_names) - 1):
            expected_connections.append((expected_task_names[i], expected_task_names[i + 1]))

        # ProjectBuilder creates pre-defined labels for anomaly project.
        # Thus, DatumaroParser shouldn't provide any label_metas
        if is_anomaly_project:
            dm_label_metas = []

        # Check if the dm_parser parses the dm_dataset properly
        assert project_name == dm_parser.get_project_name()
        assert sorted(dm_parser.get_tasks_names()) == sorted(expected_task_names)
        assert dm_parser.get_connections() == tuple(expected_connections)
        assert sorted([dm_label_meta["name"] for dm_label_meta in dm_label_metas]) == sorted(
            dm_parser.get_custom_labels_names_by_task(task_name=last_task_name)
        )

        for dm_label_meta in dm_label_metas:
            label_name = dm_label_meta["name"]
            if label_name in dm_labelname_to_parent:
                parent_name = dm_parser.get_label_parent_by_name(task_name=last_task_name, label_name=label_name)
                assert parent_name == dm_labelname_to_parent[label_name]
            if label_name in dm_labelname_to_group:
                group_name = dm_parser.get_label_group_by_name(task_name=last_task_name, label_name=label_name)
                assert group_name == dm_labelname_to_group[label_name]
            if "color" in dm_label_meta:
                color = dm_parser.get_label_color_by_name(task_name=last_task_name, label_name=label_name)
                assert color == dm_label_meta["color"]
            if "hotkey" in dm_label_meta:
                color = dm_parser.get_label_hotkey_by_name(task_name=last_task_name, label_name=label_name)
                assert color == dm_label_meta["hotkey"]

    @pytest.mark.parametrize(
        "fxt_dm_dataset_str, project_type",
        [
            [
                "fxt_datumaro_dataset_chained_det_cls",
                GetiProjectType.CHAINED_DETECTION_CLASSIFICATION,
            ],
            [
                "fxt_datumaro_dataset_chained_det_seg",
                GetiProjectType.CHAINED_DETECTION_SEGMENTATION,
            ],
        ],
    )
    def test_datumaro_parser_chained_task(  # noqa: C901
        self, request, fxt_enable_feature_flag_name, fxt_dm_dataset_str, project_type
    ):
        fxt_datumaro_dataset = request.getfixturevalue(fxt_dm_dataset_str)
        project_name = f"test_datumaro_parser_{project_type.name.lower()}"

        chained_task_type_with_labels = ImportUtils.parse_chained_task_labels_from_datumaro(
            fxt_datumaro_dataset.infos()
        )

        # exactly 2 task_types should be in chained task project.
        assert len(chained_task_type_with_labels) == 2

        # select all label_names in the dataset
        label_names_dataset = set()
        for _, label_names in chained_task_type_with_labels:
            label_names_dataset.update(label_names)

        # Call DatumaroProjectParser
        dm_parser = DatumaroProjectParser(
            project_name=project_name,
            project_type=project_type,
            dm_infos=fxt_datumaro_dataset.infos(),
            dm_categories=fxt_datumaro_dataset.categories(),
            label_to_ann_types=ImportUtils.get_label_to_ann_types(dm_dataset=fxt_datumaro_dataset),
            selected_labels=label_names_dataset,
        )

        assert project_type in [
            GetiProjectType.CHAINED_DETECTION_CLASSIFICATION,
            GetiProjectType.CHAINED_DETECTION_SEGMENTATION,
        ]

        expected_task_types = [
            TaskType.DATASET,
            TaskType.DETECTION,
            TaskType.CROP,
            (
                TaskType.CLASSIFICATION
                if project_type == GetiProjectType.CHAINED_DETECTION_CLASSIFICATION
                else TaskType.SEGMENTATION
            ),
        ]
        expected_task_names = []
        for task_type in expected_task_types:
            expected_task_names.append(
                f"{ImportUtils.task_type_to_rest_api_string(task_type).replace('_', ' ').title()}"
            )

        expected_connections = []
        for i in range(len(expected_task_names) - 1):
            expected_connections.append((expected_task_names[i], expected_task_names[i + 1]))

        # Check if the dm_parser parses the dm_dataset properly
        assert project_name == dm_parser.get_project_name()
        assert sorted(dm_parser.get_tasks_names()) == sorted(expected_task_names)
        assert dm_parser.get_connections() == tuple(expected_connections)

        for task_name in dm_parser.get_tasks_names():
            task_type = dm_parser.get_task_type_by_name(task_name=task_name)
            for expected_task_type, expected_labels in chained_task_type_with_labels:
                if task_type == expected_task_type:
                    assert sorted(dm_parser.get_custom_labels_names_by_task(task_name)) == sorted(expected_labels)

        # Filter label_meta by task_type
        # Get group, parent of labels from the dm_dataset
        dm_label_names = set()
        for _, label_names in chained_task_type_with_labels:
            dm_label_names.update(label_names)

        (dm_groups, dm_labelname_to_parent, dm_label_metas) = ConvertUtils.get_label_metadata(
            dm_categories=fxt_datumaro_dataset.categories(),
            dm_infos=fxt_datumaro_dataset.infos(),
            selected_labels=list(dm_label_names),
            project_type=project_type,
        )

        # Store group, parent of label for easy testing
        dm_labelname_to_group = {}
        if dm_groups is not None:
            for dm_group in dm_groups:
                group_name = dm_group["name"]
                for label_name in dm_group["labels"]:
                    dm_labelname_to_group[label_name] = group_name
        if dm_labelname_to_parent is None:
            dm_labelname_to_parent = {}

        for task_name in dm_parser.get_tasks_names():
            task_label_names = dm_parser.get_custom_labels_names_by_task(task_name=task_name)
            for dm_label_meta in dm_label_metas:
                label_name = dm_label_meta["name"]
                if label_name not in task_label_names:
                    continue

                if label_name in dm_labelname_to_parent:
                    parent_name = dm_parser.get_label_parent_by_name(task_name=task_name, label_name=label_name)
                    assert parent_name == dm_labelname_to_parent[label_name]
                if label_name in dm_labelname_to_group:
                    group_name = dm_parser.get_label_group_by_name(task_name=task_name, label_name=label_name)
                    assert group_name == dm_labelname_to_group[label_name]
                if "color" in dm_label_meta:
                    color = dm_parser.get_label_color_by_name(task_name=task_name, label_name=label_name)
                    assert color == dm_label_meta["color"]
                if "hotkey" in dm_label_meta:
                    color = dm_parser.get_label_hotkey_by_name(task_name=task_name, label_name=label_name)
                    assert color == dm_label_meta["hotkey"]

    @pytest.mark.parametrize(
        "fxt_dm_dataset_str, project_type",
        [
            [
                "fxt_datumaro_dataset",
                GetiProjectType.CLASSIFICATION,
            ],
            ["fxt_datumaro_dataset_multi_label", GetiProjectType.CLASSIFICATION],
            [
                "fxt_datumaro_dataset_hierarchical",
                GetiProjectType.HIERARCHICAL_CLASSIFICATION,
            ],
            [
                "fxt_datumaro_dataset_chained_det_cls",
                GetiProjectType.CHAINED_DETECTION_CLASSIFICATION,
            ],
        ],
    )
    def test_datumaro_parser_classification_top_2_labels(
        self, request, fxt_enable_feature_flag_name, fxt_dm_dataset_str, project_type
    ):
        fxt_datumaro_dataset = request.getfixturevalue(fxt_dm_dataset_str)
        project_name = f"test_datumaro_parser_{project_type.name.lower()}"

        label_to_ann_types = ImportUtils.get_label_to_ann_types(dm_dataset=fxt_datumaro_dataset)
        project_label_names = ImportUtils.get_valid_project_labels(
            project_type=project_type,
            dm_infos=fxt_datumaro_dataset.infos(),
            dm_categories=fxt_datumaro_dataset.categories(),
            label_to_ann_types=label_to_ann_types,
            include_all_labels=True,
        )

        assert len(project_label_names) > 0

        if project_type == GetiProjectType.HIERARCHICAL_CLASSIFICATION:
            project_type = GetiProjectType.CLASSIFICATION

        label_to_ann_types = ImportUtils.get_label_to_ann_types(dm_dataset=fxt_datumaro_dataset)
        # select no label
        with pytest.raises(DatasetParsingException):
            DatumaroProjectParser(
                project_name=project_name,
                project_type=project_type,
                dm_infos=fxt_datumaro_dataset.infos(),
                dm_categories=fxt_datumaro_dataset.categories(),
                label_to_ann_types=label_to_ann_types,
                selected_labels=[],
            )

        # select only 1 label
        with pytest.raises(DatasetParsingException):
            DatumaroProjectParser(
                project_name=project_name,
                project_type=project_type,
                dm_infos=fxt_datumaro_dataset.infos(),
                dm_categories=fxt_datumaro_dataset.categories(),
                label_to_ann_types=label_to_ann_types,
                selected_labels=[project_label_names[0]],
            )

    @pytest.mark.parametrize(
        "fxt_dm_dataset_str, project_type",
        [
            [
                "fxt_datumaro_dataset",
                GetiProjectType.DETECTION,
            ],
        ],
    )
    def test_datumaro_parser_detection_bad_label_selection(
        self, request, fxt_enable_feature_flag_name, fxt_dm_dataset_str, project_type
    ):
        fxt_datumaro_dataset = request.getfixturevalue(fxt_dm_dataset_str)
        project_name = f"test_datumaro_parser_{project_type.name.lower()}"

        label_to_ann_types = ImportUtils.get_label_to_ann_types(dm_dataset=fxt_datumaro_dataset)
        project_label_names = ImportUtils.get_valid_project_labels(
            project_type=project_type,
            dm_infos=fxt_datumaro_dataset.infos(),
            dm_categories=fxt_datumaro_dataset.categories(),
            label_to_ann_types=label_to_ann_types,
            include_all_labels=True,
        )

        assert len(project_label_names) > 0

        # select no label
        with pytest.raises(DatasetParsingException):
            DatumaroProjectParser(
                project_name=project_name,
                project_type=project_type,
                dm_infos=fxt_datumaro_dataset.infos(),
                dm_categories=fxt_datumaro_dataset.categories(),
                label_to_ann_types=ImportUtils.get_label_to_ann_types(dm_dataset=fxt_datumaro_dataset),
                selected_labels=[],
            )

    def test_get_label_color_by_name(self, fxt_datumaro_dataset) -> None:
        parser = DatumaroProjectParser(
            project_name="test_project_name",
            project_type=GetiProjectType.DETECTION,
            dm_infos=fxt_datumaro_dataset.infos(),
            dm_categories=fxt_datumaro_dataset.categories(),
            label_to_ann_types=ImportUtils.get_label_to_ann_types(dm_dataset=fxt_datumaro_dataset),
            selected_labels=["person"],
            color_by_label={"person": "#12345678"},
        )
        task_name = "Detection"

        parsed_color = parser.get_label_color_by_name(task_name=task_name, label_name="person")

        assert parsed_color == "#12345678"

    def _compare_pipelines(self, actual: dict[Any, Any], expected: dict[Any, Any]) -> bool:  # noqa: C901
        """
        Compare two parsed pipeline results
        Note that the values of "labels" is a list of label metas where the order of
        items do not mater
        e.g.)
            "labels": [
                { "name": "bicycle", "group": "default - Classification" },
                { "name": "car", "group": "default - Classification" },
                { "name": "person", "group": "default - Classification" }
            ]
        Thus _compare_helper() is designed to sort the items of "labels" before
        the comparison

        :return: True if pipelines are identical
        """

        def __compare_helper(item0: Any, item1: Any, ignore_order: bool = False) -> bool:  # noqa: C901
            if type(item0) is not type(item1):
                return False

            t = type(item0)

            if t is dict:
                if len(item0) != len(item1):
                    return False

                for key in item0.keys():
                    if key not in item1:
                        return False
                    ignore_order = key == "labels"
                    if not __compare_helper(item0[key], item1[key], ignore_order):
                        return False
            elif t is list:
                if ignore_order:
                    item0.sort(key=lambda x: x["name"])
                    item1.sort(key=lambda x: x["name"])

                if len(item0) != len(item1):
                    return False

                for val0, val1 in zip(item0, item1):
                    if not __compare_helper(val0, val1):
                        return False
            else:
                if item0 != item1:
                    return False

            return True

        return __compare_helper(actual, expected)

    @pytest.mark.parametrize(
        "fxt_dm_dataset_str, project_type",
        [
            ["fxt_datumaro_dataset", GetiProjectType.CLASSIFICATION],
            ["fxt_datumaro_dataset", GetiProjectType.DETECTION],
            ["fxt_datumaro_dataset_segmentation", GetiProjectType.SEGMENTATION],
            ["fxt_datumaro_dataset_instances_segmentation", GetiProjectType.INSTANCE_SEGMENTATION],
            ["fxt_datumaro_dataset_multi_label", GetiProjectType.CLASSIFICATION],
            ["fxt_datumaro_dataset_hierarchical", GetiProjectType.CLASSIFICATION],
            [
                "fxt_datumaro_dataset_rotated_detection",
                GetiProjectType.ROTATED_DETECTION,
            ],
            [
                "fxt_datumaro_dataset_anomaly_cls",
                GetiProjectType.ANOMALY_CLASSIFICATION,
            ],
            ["fxt_datumaro_dataset_anomaly_det", GetiProjectType.ANOMALY_DETECTION],
            [
                "fxt_datumaro_dataset_anomaly_seg",
                GetiProjectType.ANOMALY_SEGMENTATION,
            ],
            [
                "fxt_datumaro_dataset_chained_det_cls",
                GetiProjectType.CHAINED_DETECTION_CLASSIFICATION,
            ],
            [
                "fxt_datumaro_dataset_chained_det_seg",
                GetiProjectType.CHAINED_DETECTION_SEGMENTATION,
            ],
        ],
    )
    def test_generate_pipeline_data(
        self,
        request,
        fxt_enable_feature_flag_name,
        fxt_dm_dataset_str,
        project_type,
        fxt_expected_pipeline_by_project_parser,
    ) -> None:
        fxt_datumaro_dataset = request.getfixturevalue(fxt_dm_dataset_str)
        dm_project_parser = DatumaroProjectParser(
            project_name=f"test_{project_type.name.lower()}_project",
            project_type=project_type,
            dm_infos=fxt_datumaro_dataset.infos(),
            dm_categories=fxt_datumaro_dataset.categories(),
            label_to_ann_types=ImportUtils.get_label_to_ann_types(dm_dataset=fxt_datumaro_dataset),
            include_all_labels=True,
        )

        parsed_pipeline = dm_project_parser.parse_project_pipeline()
        expected_pipeline = fxt_expected_pipeline_by_project_parser[fxt_dm_dataset_str][project_type]

        assert self._compare_pipelines(parsed_pipeline, expected_pipeline)

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import copy
from collections.abc import Iterable
from unittest.mock import patch

import pytest
from geti_types import ID
from iai_core.entities.label import Domain
from iai_core.entities.model_template import TaskType
from jobs_common_extras.datumaro_conversion.definitions import GetiProjectType

from job.repos.data_repo import ImportDataRepo
from job.tasks.import_tasks.parse_dataset_new_project import _parse_dataset_for_import_to_new_project
from job.utils.import_utils import ImportUtils
from tests.fixtures.datasets import (
    DatasetInfo,
    get_dataset_info,
    warning_dataset_contain_no_labels,
    warning_local_annotations_lost,
)
from tests.test_helpers import save_dataset


@pytest.mark.DatasetIEMsComponent
class TestParseDatasetNewProject:
    """
    Unit test for parse_datset_new_project.py
    """

    @staticmethod
    def _parse_dataset_for_import_to_new_project(data_repo: ImportDataRepo, dataset_id: ID) -> tuple[list, list]:
        with patch(
            "job.tasks.import_tasks.parse_dataset_new_project.ImportDataRepo",
            return_value=data_repo,
        ):
            (
                supported_project_types,
                warnings,
            ) = _parse_dataset_for_import_to_new_project(import_id=str(dataset_id))

        return supported_project_types, warnings

    @staticmethod
    def _get_expected_warnings(
        project_types: Iterable[GetiProjectType],
        domain_to_warnings: dict[Domain, set[tuple]],
        exported_project_type: GetiProjectType = GetiProjectType.UNKNOWN,
    ) -> set[tuple]:
        warnings: set[tuple] = set()
        warnings.update(domain_to_warnings.get(Domain.NULL, set()))
        for project_type in project_types:
            domain = ImportUtils.project_type_to_label_domain(project_type=project_type)
            if domain in domain_to_warnings:
                warnings.update(domain_to_warnings[domain])

        if exported_project_type in [GetiProjectType.ANOMALY_DETECTION, GetiProjectType.ANOMALY_SEGMENTATION]:
            warnings.add(warning_local_annotations_lost())

        if not project_types:
            warnings.add(warning_dataset_contain_no_labels())

        return warnings

    @staticmethod
    def _get_candidate_project_types(supported_project_types):
        return [
            ImportUtils.rest_task_type_to_project_type(project_meta["project_type"])
            for project_meta in supported_project_types
        ]

    def _check_projects_from_parse_dataset_for_import_to_new_project(
        self,
        data_repo: ImportDataRepo,
        dataset_id: ID,
        expected_projects: dict[GetiProjectType, set[str]],
        expected_warnings: set[tuple],
        expected_group_names: dict[GetiProjectType, set[str]] = {},
        expected_keypoint_structure: dict[str, list] = {},
    ):
        (
            supported_project_types,
            warnings,
        ) = self._parse_dataset_for_import_to_new_project(data_repo, dataset_id)

        assert len(supported_project_types) == len(expected_projects), [
            meta["project_type"] for meta in supported_project_types
        ]
        for project_meta in supported_project_types:
            project_type = ImportUtils.rest_task_type_to_project_type(project_meta["project_type"])
            assert project_type in expected_projects
            labels = set()
            for task in project_meta["pipeline"]["tasks"]:
                labels.update([label["name"] for label in task["labels"]])
                if task["task_type"] == TaskType.KEYPOINT_DETECTION.name.lower():
                    assert task["keypoint_structure"] == expected_keypoint_structure
                else:
                    assert "keypoint_structure" not in task
            assert labels == expected_projects[project_type], (project_type, labels)
            # check label groups name for cross_project
            if project_type in expected_group_names:
                group_names = expected_group_names[project_type]
                groups = set()
                for task in project_meta["pipeline"]["tasks"]:
                    groups.update([label["group"] for label in task["labels"]])
                assert group_names == groups, (project_type, groups, group_names)

        assert len(warnings) == len(expected_warnings)
        for w in warnings:
            warning = [w["type"], w["name"], w["description"]]
            if "affected_images" in w:
                warning.append(w["affected_images"])
            assert tuple(warning) in expected_warnings

    def _get_expected_output_from_geti_exported_datumaro_dataset(
        self, dataset_info: DatasetInfo
    ) -> tuple[dict[GetiProjectType, set[str]], dict[GetiProjectType, set[str]], set[tuple]]:
        src_project_type = dataset_info.exported_project_type
        expected_groups = {}
        expected_labels: dict[GetiProjectType, set[str]] = copy.deepcopy(dataset_info.label_names_by_cross_project)
        # set re-import case (src=dst)

        if src_project_type in [
            GetiProjectType.ANOMALY_DETECTION,
            GetiProjectType.ANOMALY_SEGMENTATION,
        ]:
            expected_labels.pop(GetiProjectType.ANOMALY, None)
        else:
            expected_labels[src_project_type] = dataset_info.label_names
            if src_project_type == GetiProjectType.ANOMALY_CLASSIFICATION:
                expected_groups[src_project_type] = {"Anomaly Task Labels"}
        if dataset_info.label_names:
            expected_labels[src_project_type] = dataset_info.label_names

        for dst_project_type in dataset_info.label_names_by_cross_project:
            if dst_project_type == GetiProjectType.ANOMALY:
                continue
            trainable_tasks = ImportUtils.get_trainable_tasks_of_project_type(dst_project_type)
            group_names = set()
            if src_project_type == GetiProjectType.DETECTION and dst_project_type == GetiProjectType.CLASSIFICATION:
                # Detection -> multi-label classification
                assert trainable_tasks == [TaskType.CLASSIFICATION]
                for label in dataset_info.label_names_by_cross_project[dst_project_type]:
                    group_names.add(f"Classification Task Labels for '{label}'")
            else:
                for t in trainable_tasks:
                    task_name = ImportUtils.task_type_to_rest_api_string(t).replace("_", " ").title()
                    group_names.add(f"{task_name} Task Labels")

            expected_groups[dst_project_type] = group_names
        warnings = self._get_expected_warnings(
            expected_labels.keys(),
            dataset_info.warnings,
            exported_project_type=dataset_info.exported_project_type,
        )
        return expected_labels, expected_groups, warnings

    def _test_parse_dataset_for_import_to_new_project__datumaro_format(
        self,
        dataset_id,
        dataset_info: DatasetInfo,
        import_data_repo,
    ):
        # geti-exported datumaro dataset
        if dataset_info.exported_project_type != GetiProjectType.UNKNOWN:
            labels, groups, warnings = self._get_expected_output_from_geti_exported_datumaro_dataset(dataset_info)
            self._check_projects_from_parse_dataset_for_import_to_new_project(
                import_data_repo,
                ID(dataset_id),
                labels,
                warnings,
                expected_group_names=groups,
                expected_keypoint_structure=dataset_info.keypoint_structure,
            )

        # if this dataset is not exported from Geti
        with patch(
            "jobs_common_extras.datumaro_conversion.import_utils.ImportUtils.get_exported_project_type",
            return_value=GetiProjectType.UNKNOWN,
        ) as mock_get_exported_project_type:
            warnings = self._get_expected_warnings(dataset_info.label_names_by_ann_based_project, dataset_info.warnings)
            self._check_projects_from_parse_dataset_for_import_to_new_project(
                import_data_repo,
                ID(dataset_id),
                dataset_info.label_names_by_ann_based_project,
                warnings,
                expected_keypoint_structure=dataset_info.keypoint_structure,
            )
            mock_get_exported_project_type.assert_called()

    def test_parse_dataset_for_import_to_new_project__datumaro_format(
        self,
        fxt_dataset_id__datumaro,
        fxt_import_data_repo,
    ):
        fxt_dataset_id, dataset_info = fxt_dataset_id__datumaro
        self._test_parse_dataset_for_import_to_new_project__datumaro_format(
            fxt_dataset_id, dataset_info, fxt_import_data_repo
        )

    @pytest.mark.parametrize(
        "anomaly_dataset_id",
        (
            "fxt_datumaro_dataset_anomaly_cls_id",
            "fxt_datumaro_dataset_anomaly_det_id",
            "fxt_datumaro_dataset_anomaly_seg_id",
        ),
    )
    def test_parse_dataset_for_import_to_new_project__datumaro_format__anomaly(
        self,
        anomaly_dataset_id,
        fxt_import_data_repo,
        request,
    ):
        dataset_id = request.getfixturevalue(anomaly_dataset_id)
        dataset_info = get_dataset_info(anomaly_dataset_id)

        self._test_parse_dataset_for_import_to_new_project__datumaro_format(
            dataset_id, dataset_info, fxt_import_data_repo
        )

    def test_parse_dataset_for_import_to_new_project__datumaro_format__keypoint_detection(
        self,
        fxt_dataumaro_dataset_keypoint_id,
        fxt_import_data_repo,
        fxt_keypoint_detection,  # Do not delete this fixture
    ):
        """
        Keypoint detection dataset could be imported to new project (req: CVS-107582).
        """
        keypoint_labels = {
            "nose",  # 1
            "left_eye",  # 2
            "right_eye",  # 3
            "left_ear",  # 4
            "right_ear",  # 5
            "left_shoulder",  # 6
            "right_shoulder",  # 7
            "left_elbow",  # 8
            "right_elbow",  # 9
            "left_wrist",  # 10
            "right_wrist",  # 11
            "left_hip",  # 12
            "right_hip",  # 13
            "left_knee",  # 14
            "right_knee",  # 15
            "left_ankle",  # 16
            "right_ankle",  # 17
        }
        keypoint_structure = {
            "edges": [
                {"nodes": ["left_shoulder", "left_hip"]},  # [6,12]
                {"nodes": ["left_ear", "left_shoulder"]},  # [4,6]
                {"nodes": ["left_hip", "right_hip"]},  # [12,13]
                {"nodes": ["right_ear", "right_shoulder"]},  # [5,7]
                {"nodes": ["right_ankle", "right_knee"]},  # [17,15]
                {"nodes": ["right_elbow", "right_wrist"]},  # [9,11]
                {"nodes": ["nose", "right_eye"]},  # [1,3]
                {"nodes": ["left_shoulder", "left_elbow"]},  # [6,8]
                {"nodes": ["right_shoulder", "right_hip"]},  # [7,13]
                {"nodes": ["left_knee", "left_hip"]},  # [14,12]
                {"nodes": ["left_eye", "left_ear"]},  # [2,4]
                {"nodes": ["nose", "left_eye"]},  # [1,2]
                {"nodes": ["right_knee", "right_hip"]},  # [15,13]
                {"nodes": ["right_shoulder", "right_elbow"]},  # [7,9]
                {"nodes": ["left_shoulder", "right_shoulder"]},  # [6,7]
                {"nodes": ["right_eye", "right_ear"]},  # [3,5]
                {"nodes": ["left_elbow", "left_wrist"]},  # [8,10]
                {"nodes": ["left_eye", "right_eye"]},  # [2,3]
                {"nodes": ["left_ankle", "left_knee"]},  # [16,14]
            ],
            "positions": [
                {"label": "nose", "x": 0.1, "y": 0.4},
                {"label": "left_eye", "x": 0.2, "y": 0.5},
                {"label": "right_eye", "x": 0.3, "y": 0.6},
                {"label": "left_ear", "x": 0.4, "y": 0.7},
                {"label": "right_ear", "x": 0.5, "y": 0.8},
                {"label": "left_shoulder", "x": 0.6, "y": 0.9},
                {"label": "right_shoulder", "x": 0.7, "y": 1.0},
                {"label": "left_elbow", "x": 0.8, "y": 0.9},
                {"label": "right_elbow", "x": 0.9, "y": 0.8},
                {"label": "left_wrist", "x": 1.0, "y": 0.7},
                {"label": "right_wrist", "x": 0.9, "y": 0.6},
                {"label": "left_hip", "x": 0.8, "y": 0.5},
                {"label": "right_hip", "x": 0.7, "y": 0.4},
                {"label": "left_knee", "x": 0.6, "y": 0.3},
                {"label": "right_knee", "x": 0.5, "y": 0.2},
                {"label": "left_ankle", "x": 0.4, "y": 0.1},
                {"label": "right_ankle", "x": 0.3, "y": 0.0},
            ],
        }
        if fxt_keypoint_detection:
            dataset_info = DatasetInfo(
                exported_project_type=GetiProjectType.KEYPOINT_DETECTION,
                label_names=keypoint_labels,
                label_names_by_ann_based_project={  # bbox, points
                    GetiProjectType.DETECTION: {"person"},
                    GetiProjectType.KEYPOINT_DETECTION: keypoint_labels,
                },
                keypoint_structure=keypoint_structure,
                num_items=4,
            )
        else:
            dataset_info = DatasetInfo(
                exported_project_type=GetiProjectType.UNKNOWN,
                label_names=set(),  # empty: it should be handled as if it's not exported from Geti.
                label_names_by_ann_based_project={  # bbox
                    GetiProjectType.DETECTION: {"person"},
                },
                num_items=4,
            )

        self._test_parse_dataset_for_import_to_new_project__datumaro_format(
            fxt_dataumaro_dataset_keypoint_id, dataset_info, fxt_import_data_repo
        )

    def test_parse_dataset_for_import_to_new_project__public_dataset(
        self, fxt_dataset_id__public, fxt_import_data_repo
    ):
        """
        Candidate tasks should support defined task mappings(CVS-105432) and disable other mappings.

        For public formats(coco, voc, yolo) + Datumaro format not exported from Geti:
            candidate tasks would be decided based on annotation types.
            - label -> classification
            - bbox -> detection
            - polygon/ellipse/mask -> segmentation.
        """
        fxt_dataset_id, dataset_info = fxt_dataset_id__public
        warnings = self._get_expected_warnings(dataset_info.label_names_by_ann_based_project, dataset_info.warnings)
        self._check_projects_from_parse_dataset_for_import_to_new_project(
            fxt_import_data_repo,
            ID(fxt_dataset_id),
            dataset_info.label_names_by_ann_based_project,
            warnings,
        )

    def test_parse_dataset_for_import_to_new_project__by_annotation_types(
        self,
        fxt_dataset_definition,
        fxt_dataset_labels,
        fxt_dm_dataset_generator,
        fxt_import_data_repo,
        request,
    ):
        """
        Candidate tasks should support defined task mappings(CVS-105432) and disable other mappings.

        For public formats(coco, voc, yolo) + Datumaro format not exported from Geti:
            candidate tasks would be decided based on annotation types.
            - label -> classification
            - bbox -> detection
            - polygon/ellipse/mask -> segmentation.
        """

        dm_dataset_definition, dataset_info = fxt_dataset_definition

        label_names = [label["name"] for label in fxt_dataset_labels]
        dm_dataset = fxt_dm_dataset_generator(label_names, dm_dataset_definition)
        dataset_id = save_dataset(fxt_import_data_repo, dm_dataset, "datumaro")
        warnings = self._get_expected_warnings(dataset_info.label_names_by_ann_based_project, dataset_info.warnings)

        self._check_projects_from_parse_dataset_for_import_to_new_project(
            fxt_import_data_repo,
            dataset_id,
            dataset_info.label_names_by_ann_based_project,
            warnings,
        )

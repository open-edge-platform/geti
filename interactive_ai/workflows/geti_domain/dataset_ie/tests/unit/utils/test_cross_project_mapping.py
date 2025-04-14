# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""Test export utils"""

from copy import deepcopy
from typing import NamedTuple
from unittest.mock import MagicMock, patch

import pytest
from datumaro import AnnotationType, CategoriesInfo, Dataset, LabelCategories, Polygon
from jobs_common_extras.datumaro_conversion.definitions import GetiProjectType

from job.utils.cross_project_mapping import (
    CrossProjectConverterAnomalyDetSegToCls,
    CrossProjectConverterBase,
    CrossProjectConverterDetSegToDet,
    CrossProjectConverterDetSegToRot,
    CrossProjectConverterDetSegToSeg,
    CrossProjectConverterDetToCls,
    CrossProjectConverterDetToRot,
    CrossProjectConverterRotToDet,
    CrossProjectConverterSegToDet,
    CrossProjectConverterSegToDetSeg,
    CrossProjectMapper,
    LabelInfo,
)
from job.utils.datumaro_parser import get_project_metas_with_labels
from job.utils.exceptions import ResearvedLabelException, UnsupportedMappingException
from job.utils.import_utils import ImportUtils


class ANN(NamedTuple):
    type: AnnotationType
    label: int


@pytest.mark.JobsComponent
class TestCrossProjectMapping:
    def test_mapper__check_if_cross_project_mapping_for_new_project(
        self,
        fxt_datumaro_dataset_detection,
    ):
        # Arrange
        dm_dataset = fxt_datumaro_dataset_detection
        label_to_ann_types = ImportUtils.get_label_to_ann_types(dm_dataset=dm_dataset)
        project_metas_with_labels = get_project_metas_with_labels(
            dm_infos=dm_dataset.infos(), dm_categories=dm_dataset.categories(), label_to_ann_types=label_to_ann_types
        )

        # Act
        CrossProjectMapper.check_if_cross_project_mapping_for_new_project(
            dm_dataset=dm_dataset,
            label_to_ann_types=label_to_ann_types,
            project_metas_with_labels=project_metas_with_labels,
        )

        # Assert
        assert len(project_metas_with_labels) == 3
        project_types = {meta["project_type"] for meta in project_metas_with_labels}
        assert project_types == {
            GetiProjectType.DETECTION,
            GetiProjectType.ROTATED_DETECTION,
            GetiProjectType.CLASSIFICATION,
        }
        assert "CrossProjectMapping" in dm_dataset.infos()
        assert set(dm_dataset.infos()["CrossProjectMapping"]) == {
            (
                ImportUtils.project_type_to_rest_api_string(GetiProjectType.DETECTION),
                ImportUtils.project_type_to_rest_api_string(GetiProjectType.ROTATED_DETECTION),
            ),
            (
                ImportUtils.project_type_to_rest_api_string(GetiProjectType.DETECTION),
                ImportUtils.project_type_to_rest_api_string(GetiProjectType.CLASSIFICATION),
            ),
        }

    def test_mapper__check_if_cross_project_mapping_for_new_project_error(
        self,
        fxt_datumaro_dataset_detection,
    ):
        # Arrange
        dm_dataset = fxt_datumaro_dataset_detection
        label_to_ann_types = ImportUtils.get_label_to_ann_types(dm_dataset=dm_dataset)
        project_metas_with_labels = get_project_metas_with_labels(
            dm_infos=dm_dataset.infos(), dm_categories=dm_dataset.categories(), label_to_ann_types=label_to_ann_types
        )
        src_metas = deepcopy(project_metas_with_labels)

        # Act & Assert 1
        with patch(
            "jobs_common_extras.datumaro_conversion.import_utils.ImportUtils.get_exported_project_type",
            return_value=GetiProjectType.UNKNOWN,
        ) as mock_get_exported_project_type:
            CrossProjectMapper.check_if_cross_project_mapping_for_new_project(
                dm_dataset=dm_dataset,
                label_to_ann_types=label_to_ann_types,
                project_metas_with_labels=project_metas_with_labels,
            )
            mock_get_exported_project_type.assert_called_with(dm_dataset.infos())
            dst_metas = deepcopy(project_metas_with_labels)
            assert src_metas == dst_metas
            assert "CrossProjectMapping" not in dm_dataset.infos()

        # Act & Assert 2
        with patch("job.utils.cross_project_mapping.DatumaroProjectParser") as patched_parser:
            patched_parser.side_effect = ValueError("value error")
            CrossProjectMapper.check_if_cross_project_mapping_for_new_project(
                dm_dataset=dm_dataset,
                label_to_ann_types=label_to_ann_types,
                project_metas_with_labels=project_metas_with_labels,
            )
            mock_get_exported_project_type.assert_called_with(dm_dataset.infos())
            dst_metas = deepcopy(project_metas_with_labels)
            assert src_metas == dst_metas
            assert "CrossProjectMapping" not in dm_dataset.infos()

    @pytest.mark.parametrize("is_hierarchical", [True, False])
    @pytest.mark.parametrize("is_multi_labels", [True, False])
    def test_mapper__check_if_cross_project_mapping_for_existing_project(
        self,
        is_hierarchical,
        is_multi_labels,
        fxt_datumaro_dataset_detection,
    ):
        # Arrange
        dm_dataset = fxt_datumaro_dataset_detection
        target_project = GetiProjectType.CLASSIFICATION
        label_to_ann_types = ImportUtils.get_label_to_ann_types(dm_dataset=dm_dataset)

        # Act
        with patch("job.utils.cross_project_mapping.ImportUtils.is_task_hierarhical_or_multi_labels") as patched:
            patched.return_value = (is_hierarchical, is_multi_labels)
            label_names = CrossProjectMapper.check_if_cross_project_mapping_for_existing_project(
                dm_dataset=dm_dataset,
                label_to_ann_types=label_to_ann_types,
                project_type=target_project,
                project_identifier=MagicMock(),
            )

        # Assert
        if is_hierarchical or not is_multi_labels:
            assert len(label_names) == 0
            assert "CrossProjectMapping" not in dm_dataset.infos()
        else:
            assert set(label_names) == {"label0", "label1"}
            assert "CrossProjectMapping" in dm_dataset.infos()
            assert dm_dataset.infos()["CrossProjectMapping"] == [
                (
                    ImportUtils.project_type_to_rest_api_string(GetiProjectType.DETECTION),
                    ImportUtils.project_type_to_rest_api_string(GetiProjectType.CLASSIFICATION),
                ),
            ]

    def test_mapper__check_if_cross_project_mapping_for_existing_project_error(
        self,
        fxt_datumaro_dataset_detection,
    ):
        # Arrange
        dm_dataset = fxt_datumaro_dataset_detection
        target_project = GetiProjectType.ROTATED_DETECTION
        label_to_ann_types = ImportUtils.get_label_to_ann_types(dm_dataset=dm_dataset)

        # Act & Assert
        with patch(
            "jobs_common_extras.datumaro_conversion.import_utils.ImportUtils.get_exported_project_type",
            return_value=GetiProjectType.UNKNOWN,
        ) as mock_get_exported_project_type:
            label_names = CrossProjectMapper.check_if_cross_project_mapping_for_existing_project(
                dm_dataset=dm_dataset,
                label_to_ann_types=label_to_ann_types,
                project_type=target_project,
                project_identifier=MagicMock(),
            )
            mock_get_exported_project_type.assert_called_with(dm_dataset.infos())
            assert label_names == ()
            assert "CrossProjectMapping" not in dm_dataset.infos()

    @pytest.mark.parametrize(
        "target_project, target_convertor",
        (
            (GetiProjectType.DETECTION, CrossProjectConverterSegToDet),
            (GetiProjectType.CHAINED_DETECTION_SEGMENTATION, CrossProjectConverterSegToDetSeg),
        ),
    )
    def test_mapper__convert_annotation_type_for_cross_project(
        self, target_project, target_convertor, fxt_datumaro_dataset_segmentation
    ):
        # Arrange
        dm_dataset: Dataset = fxt_datumaro_dataset_segmentation
        dm_infos = {
            "CrossProjectMapping": [
                [
                    ImportUtils.project_type_to_rest_api_string(GetiProjectType.SEGMENTATION),
                    ImportUtils.project_type_to_rest_api_string(target_project),
                ]
            ]
        }  # We saved mappings as 'tuple' but, json converts 'tuple' to 'list'.
        dm_dataset.transform("project_infos", dst_infos=dm_infos, overwrite=False)
        target_converter_str = target_convertor.__name__

        # Act & Assert
        with (
            patch(
                f"job.utils.cross_project_mapping.{target_converter_str}.apply_converted_label_info"
            ) as mocked_convert_labels,
            patch(
                f"job.utils.cross_project_mapping.{target_converter_str}.convert_annotation_type"
            ) as mocked_convert_anns,
        ):
            # Act
            CrossProjectMapper.convert_annotation_type_for_cross_project(
                dm_dataset=dm_dataset, project_type=target_project
            )

            # Assert
            mocked_convert_anns.assert_called()
            mocked_convert_labels.assert_called()

    @patch("job.utils.cross_project_mapping.CrossProjectConverterDetToRot.apply_converted_label_info")
    @patch("job.utils.cross_project_mapping.CrossProjectConverterDetToRot.convert_annotation_type")
    def test_mapper__convert_annotation_type_for_cross_project_error(
        self, mocked_convert_anns, mocked_convert_labels, fxt_datumaro_dataset_detection
    ):
        # Arrange
        dm_dataset: Dataset = fxt_datumaro_dataset_detection
        dm_infos = {
            "CrossProjectMapping": [
                [
                    ImportUtils.project_type_to_rest_api_string(GetiProjectType.DETECTION),
                    ImportUtils.project_type_to_rest_api_string(GetiProjectType.ROTATED_DETECTION),
                ]
            ]
        }  # We saved mappings as 'tuple' but, json converts 'tuple' to 'list'.
        dm_dataset.transform("project_infos", dst_infos=dm_infos, overwrite=False)
        target_project = GetiProjectType.ROTATED_DETECTION

        # Act & Assert 1
        with patch(
            "jobs_common_extras.datumaro_conversion.import_utils.ImportUtils.get_exported_project_type",
            return_value=GetiProjectType.UNKNOWN,
        ) as mock_get_exported_project_type:
            CrossProjectMapper.convert_annotation_type_for_cross_project(
                dm_dataset=dm_dataset, project_type=target_project
            )
            mock_get_exported_project_type.assert_called_with(dm_dataset.infos())
            assert not mocked_convert_anns.called
            assert not mocked_convert_labels.called

        # Act & Assert 2
        with (
            patch("job.utils.cross_project_mapping.SUPPORTED_CROSS_PROJECT_MAPPINGS") as patched_mapping,
            pytest.raises(UnsupportedMappingException),
        ):
            patched_mapping.get.return_value = {}
            CrossProjectMapper.convert_annotation_type_for_cross_project(
                dm_dataset=dm_dataset, project_type=target_project
            )
            assert not mocked_convert_anns.called
            assert not mocked_convert_labels.called

    @pytest.mark.parametrize(
        "dataset, project_type, label_schema",
        [
            ("fxt_datumaro_dataset_detection", GetiProjectType.ROTATED_DETECTION, ""),
            (
                "fxt_datumaro_dataset_multi_label",
                GetiProjectType.HIERARCHICAL_CLASSIFICATION,
                "fxt_label_schema_hierarchical",
            ),
            ("fxt_datumaro_dataset_hierarchical", GetiProjectType.CLASSIFICATION, "fxt_label_schema_classification"),
        ],
    )
    @patch("job.utils.import_utils.LabelSchemaRepo")
    def test_mapper__is_cross_mapping_case_for_geti_exported_dataset_true(
        self,
        patched_repo,
        dataset,
        project_type,
        label_schema,
        request: pytest.FixtureRequest,
    ):
        # Arrange
        dm_dataset: Dataset = request.getfixturevalue(dataset)
        dst_project = MagicMock()
        if label_schema != "":
            patched_repo().get_latest.return_value = request.getfixturevalue(label_schema)
        # Act
        with patch("job.utils.cross_project_mapping.ImportUtils.get_project_type", return_value=project_type):
            result = CrossProjectMapper.is_cross_mapping_case_for_geti_exported_dataset(
                dm_categories=dm_dataset.categories(), dm_infos=dm_dataset.infos(), project=dst_project
            )

        # Assert
        assert result is True

    @pytest.mark.parametrize(
        "dataset, project_type, label_schema",
        [
            ("fxt_voc_dataset_segmentation", GetiProjectType.DETECTION, ""),
            (
                "fxt_datumaro_dataset_hierarchical",
                GetiProjectType.HIERARCHICAL_CLASSIFICATION,
                "fxt_label_schema_hierarchical",
            ),
        ],
    )
    @patch("job.utils.import_utils.LabelSchemaRepo")
    def test_mapper__is_cross_mapping_case_for_geti_exported_dataset_false(
        self,
        patched_repo,
        dataset,
        project_type,
        label_schema,
        request: pytest.FixtureRequest,
    ):
        # Arrange
        dm_dataset: Dataset = request.getfixturevalue(dataset)
        dst_project = MagicMock()
        if label_schema != "":
            patched_repo().get_latest.return_value = request.getfixturevalue(label_schema)

        # Act
        with patch("job.utils.cross_project_mapping.ImportUtils.get_project_type", return_value=project_type):
            result = CrossProjectMapper.is_cross_mapping_case_for_geti_exported_dataset(
                dm_categories=dm_dataset.categories(), dm_infos=dm_dataset.infos(), project=dst_project
            )

        # Assert
        assert result is False

    def test_converter_base__convert_annotation_type(self, fxt_datumaro_dataset_detection):
        # Arrange
        dm_dataset = fxt_datumaro_dataset_detection
        src_def = self._get_ann_definition(dm_dataset)
        convertor = CrossProjectConverterBase()

        # Act
        convertor.convert_annotation_type(dm_dataset=dm_dataset)
        dst_def = self._get_ann_definition(dm_dataset)

        # Assert
        assert src_def == dst_def

    @pytest.mark.parametrize("calc_label_to_ann_types", [True, False])
    def test_converter_base__get_converted_label_info(self, fxt_datumaro_dataset_detection, calc_label_to_ann_types):
        # Arrange
        dm_dataset = fxt_datumaro_dataset_detection
        convertor = CrossProjectConverterBase()
        dst_project = GetiProjectType.ROTATED_DETECTION
        labels_map = ImportUtils.get_label_to_ann_types(dm_dataset=dm_dataset)

        # Act
        infos, categories, label_to_ann_types = convertor.get_converted_label_info(
            dm_infos=dm_dataset.infos(),
            dm_categories=dm_dataset.categories(),
            dst=dst_project,
            label_to_ann_types=labels_map if calc_label_to_ann_types else {},
        )

        # Assert
        assert infos["GetiProjectTask"] == ImportUtils.project_type_to_rest_api_string(dst_project)
        self._check_expected_labels(categories, ["label0", "label1"])
        if calc_label_to_ann_types:
            assert label_to_ann_types == {"label0": {AnnotationType.bbox}, "label1": {AnnotationType.bbox}}
        else:
            assert label_to_ann_types == {}

    def test_converter_base__apply_converted_label_info(self, fxt_datumaro_dataset_detection):
        # Arrange
        dm_dataset: Dataset = fxt_datumaro_dataset_detection
        convertor = CrossProjectConverterBase()

        # Act
        convertor.apply_converted_label_info(dm_dataset=dm_dataset, dst=GetiProjectType.ROTATED_DETECTION)

        # Assert
        assert dm_dataset.infos()["GetiProjectTask"] == ImportUtils.project_type_to_rest_api_string(
            GetiProjectType.ROTATED_DETECTION
        )
        self._check_expected_labels(dm_dataset.categories(), ["label0", "label1"])

    def test_converter_det2rot__convert_annotation_type(self, fxt_datumaro_dataset_detection):
        # Arrange
        dm_dataset: Dataset = fxt_datumaro_dataset_detection
        # add polygon to check if it will be removed.
        for item in dm_dataset:
            item.annotations.append(Polygon(points=(0, 0, 1, 1, 3, 3, 5, 5), label=0))
            break
        src_def = self._get_ann_definition(dm_dataset)
        convertor = CrossProjectConverterDetToRot()

        # Act
        convertor.convert_annotation_type(dm_dataset=dm_dataset)
        dst_def = self._get_ann_definition(dm_dataset)

        # Assert
        assert set(src_def.keys()) == set(dst_def.keys())
        for id, anns in src_def.items():
            filtered = []
            for src in anns:
                if src.type != AnnotationType.polygon:
                    filtered.append(src)
            for src, dst in zip(filtered, dst_def[id]):
                if src.type == AnnotationType.bbox:
                    assert dst.type == AnnotationType.polygon
                assert src.label == dst.label

    @pytest.mark.parametrize("calc_label_to_ann_types", [True, False])
    def test_converter_det2rot__get_converted_label_info(
        self, fxt_dataset_labels, fxt_dm_dataset_generator, calc_label_to_ann_types
    ):
        # Arrange
        label_names = [label["name"] for label in fxt_dataset_labels]
        definition = {
            "item1": {("bbox", 0)},
            "item2": {("bbox", 1), ("bbox", 2)},
            # check for remove polygons
            "item3": {("bbox", 1), ("polygon", 1)},
            "item4": {("polygon", 3)},
            "item5": {("label", 2)},
        }
        dm_dataset: Dataset = fxt_dm_dataset_generator(label_names, definition)
        convertor = CrossProjectConverterDetToRot()
        dst_project = GetiProjectType.ROTATED_DETECTION
        labels_map = ImportUtils.get_label_to_ann_types(dm_dataset=dm_dataset)

        # Act
        infos, categories, label_to_ann_types = convertor.get_converted_label_info(
            dm_infos=dm_dataset.infos(),
            dm_categories=dm_dataset.categories(),
            dst=dst_project,
            label_to_ann_types=labels_map if calc_label_to_ann_types else {},
        )

        # Assert
        assert infos["GetiProjectTask"] == ImportUtils.project_type_to_rest_api_string(dst_project)
        self._check_expected_labels(categories, label_names)
        if calc_label_to_ann_types:
            assert label_to_ann_types == {
                "bus": set(),
                "cat": {AnnotationType.polygon},
                "dog": {AnnotationType.polygon},
                "truck": {AnnotationType.label, AnnotationType.polygon},
            }
        else:
            assert label_to_ann_types == {}

    def test_converter_det2cls__convert_annotation_type(self, fxt_datumaro_dataset_detection):
        # Arrange
        dm_dataset: Dataset = fxt_datumaro_dataset_detection
        # add polygon to check if it will be removed.
        for item in dm_dataset:
            item.annotations.append(Polygon(points=(0, 0, 1, 1, 3, 3, 5, 5), label=0))
            break
        src_def = self._get_ann_definition(dm_dataset)
        convertor = CrossProjectConverterDetToCls()

        # Act
        convertor.convert_annotation_type(dm_dataset=dm_dataset)
        dst_def = self._get_ann_definition(dm_dataset)

        # Assert
        assert set(src_def.keys()) == set(dst_def.keys())
        for id, anns in src_def.items():
            filtered = []
            for src in anns:
                if src.type != AnnotationType.polygon:
                    filtered.append(src)
            for src, dst in zip(filtered, dst_def[id]):
                if src.type == AnnotationType.bbox:
                    assert dst.type == AnnotationType.label
                assert src.label == dst.label

    @pytest.mark.parametrize("calc_label_to_ann_types", [True, False])
    def test_converter_det2cls__get_converted_label_info(
        self, fxt_dataset_labels, fxt_dm_dataset_generator, calc_label_to_ann_types
    ):
        # Arrange
        label_names = [label["name"] for label in fxt_dataset_labels]
        definition = {
            "item1": {("bbox", 0)},
            "item2": {("bbox", 1), ("bbox", 2)},
            # check for remove polygons
            "item3": {("bbox", 1), ("polygon", 1)},
            "item4": {("polygon", 3)},
            "item5": {("label", 2)},
        }
        dm_dataset: Dataset = fxt_dm_dataset_generator(label_names, definition)
        convertor = CrossProjectConverterDetToCls()
        dst_project = GetiProjectType.CLASSIFICATION
        labels_map = ImportUtils.get_label_to_ann_types(dm_dataset=dm_dataset)

        # Act
        infos, categories, label_to_ann_types = convertor.get_converted_label_info(
            dm_infos=dm_dataset.infos(),
            dm_categories=dm_dataset.categories(),
            dst=dst_project,
            label_to_ann_types=labels_map if calc_label_to_ann_types else {},
        )

        # Assert
        assert infos["GetiProjectTask"] == ImportUtils.project_type_to_rest_api_string(dst_project)
        assert ImportUtils.is_dataset_from_multi_label_classification(categories, infos)
        self._check_expected_labels(categories, label_names)
        if calc_label_to_ann_types:
            assert label_to_ann_types == {
                "bus": set(),
                "cat": {AnnotationType.label},
                "dog": {AnnotationType.label},
                "truck": {AnnotationType.label},
            }
        else:
            assert label_to_ann_types == {}

    def test_converter_rot2det__convert_annotation_type(self, fxt_datumaro_dataset_rotated_detection):
        # Arrange
        dm_dataset: Dataset = fxt_datumaro_dataset_rotated_detection
        src_def = self._get_ann_definition(dm_dataset)
        convertor = CrossProjectConverterRotToDet()

        # Act
        convertor.convert_annotation_type(dm_dataset=dm_dataset)
        dst_def = self._get_ann_definition(dm_dataset)

        # Assert
        assert set(src_def.keys()) == set(dst_def.keys())
        for id, anns in src_def.items():
            for src, dst in zip(anns, dst_def[id]):
                if src.type == AnnotationType.polygon:
                    assert dst.type == AnnotationType.bbox
                assert src.label == dst.label

    @pytest.mark.parametrize("calc_label_to_ann_types", [True, False])
    def test_converter_rot2det__get_converted_label_info(
        self, fxt_datumaro_dataset_rotated_detection, calc_label_to_ann_types
    ):
        # Arrange
        dm_dataset: Dataset = fxt_datumaro_dataset_rotated_detection
        convertor = CrossProjectConverterRotToDet()
        dst_project = GetiProjectType.DETECTION
        labels_map = ImportUtils.get_label_to_ann_types(dm_dataset=dm_dataset)

        # Act
        infos, categories, label_to_ann_types = convertor.get_converted_label_info(
            dm_infos=dm_dataset.infos(),
            dm_categories=dm_dataset.categories(),
            dst=dst_project,
            label_to_ann_types=labels_map if calc_label_to_ann_types else {},
        )

        # Assert
        assert infos["GetiProjectTask"] == ImportUtils.project_type_to_rest_api_string(dst_project)
        self._check_expected_labels(categories, ["ball", "person"])
        if calc_label_to_ann_types:
            assert label_to_ann_types == {"ball": {AnnotationType.bbox}, "person": {AnnotationType.bbox}}
        else:
            assert label_to_ann_types == {}

    def test_converter_seg2det__convert_annotation_type(self, fxt_datumaro_dataset_segmentation):
        # Arrange
        dm_dataset: Dataset = fxt_datumaro_dataset_segmentation
        src_def = self._get_ann_definition(dm_dataset)
        convertor = CrossProjectConverterSegToDet()

        # Act
        convertor.convert_annotation_type(dm_dataset=dm_dataset)
        dst_def = self._get_ann_definition(dm_dataset)

        # Assert
        assert set(src_def.keys()) == set(dst_def.keys())
        for id, anns in src_def.items():
            for src, dst in zip(anns, dst_def[id]):
                if src.type in [AnnotationType.polygon, AnnotationType.mask, AnnotationType.ellipse]:
                    assert dst.type == AnnotationType.bbox
                assert src.label == dst.label

    @pytest.mark.parametrize("calc_label_to_ann_types", [True, False])
    def test_converter_seg2det__get_converted_label_info(
        self, fxt_datumaro_dataset_segmentation, calc_label_to_ann_types
    ):
        # Arrange
        dm_dataset: Dataset = fxt_datumaro_dataset_segmentation
        convertor = CrossProjectConverterSegToDet()
        dst_project = GetiProjectType.DETECTION
        labels_map = ImportUtils.get_label_to_ann_types(dm_dataset=dm_dataset)

        # Act
        infos, categories, label_to_ann_types = convertor.get_converted_label_info(
            dm_infos=dm_dataset.infos(),
            dm_categories=dm_dataset.categories(),
            dst=dst_project,
            label_to_ann_types=labels_map if calc_label_to_ann_types else {},
        )

        # Assert
        assert infos["GetiProjectTask"] == ImportUtils.project_type_to_rest_api_string(dst_project)
        self._check_expected_labels(categories, ["label0", "label1"])
        if calc_label_to_ann_types:
            assert label_to_ann_types == {"label0": {AnnotationType.bbox}, "label1": {AnnotationType.bbox}}
        else:
            assert label_to_ann_types == {}

    def test_converter_anomaly2cls__convert_annotation_type(self, fxt_datumaro_dataset_anomaly_det):
        # Arrange
        dm_dataset: Dataset = fxt_datumaro_dataset_anomaly_det
        src_def = self._get_ann_definition(dm_dataset)
        convertor = CrossProjectConverterAnomalyDetSegToCls()

        # Act
        convertor.convert_annotation_type(dm_dataset=dm_dataset)
        dst_def = self._get_ann_definition(dm_dataset)

        # Assert
        assert set(src_def.keys()) == set(dst_def.keys())
        for id, anns in src_def.items():
            filtered = []
            for src in anns:
                if src.type == AnnotationType.label:
                    filtered.append(src)
            for src, dst in zip(filtered, dst_def[id]):
                assert src == dst

    def test_converter_seg2detseg__convert_annotation_type(self, fxt_datumaro_dataset_segmentation):
        # Arrange
        dm_dataset: Dataset = fxt_datumaro_dataset_segmentation
        src_def = self._get_ann_definition(dm_dataset)
        convertor = CrossProjectConverterSegToDetSeg()

        # Act
        convertor.apply_converted_label_info(dm_dataset, GetiProjectType.CHAINED_DETECTION_SEGMENTATION)
        convertor.convert_annotation_type(dm_dataset=dm_dataset)
        dst_def = self._get_ann_definition(dm_dataset)

        label_cat = dm_dataset.categories()[AnnotationType.label]
        detection_label_id, _ = label_cat.find(CrossProjectConverterSegToDetSeg.DEFAULT_DETECTION_LABEL)

        # Assert
        assert set(src_def.keys()) == set(dst_def.keys())
        for id, anns in src_def.items():
            expected_anns = []
            for src in anns:
                if src.type in [AnnotationType.polygon, AnnotationType.mask, AnnotationType.ellipse]:
                    expected_anns.extend([ANN(src.type, src.label), ANN(AnnotationType.bbox, detection_label_id)])
            assert sorted(expected_anns) == sorted(dst_def[id])

    @pytest.mark.parametrize("calc_label_to_ann_types", [True, False])
    def test_converter_seg2detseg__get_converted_label_info(
        self, fxt_datumaro_dataset_segmentation, calc_label_to_ann_types
    ):
        # Arrange
        dm_dataset: Dataset = fxt_datumaro_dataset_segmentation
        convertor = CrossProjectConverterSegToDetSeg()
        dst_project = GetiProjectType.CHAINED_DETECTION_SEGMENTATION
        labels_map = ImportUtils.get_label_to_ann_types(dm_dataset=dm_dataset)

        # Act
        infos, categories, label_to_ann_types = convertor.get_converted_label_info(
            dm_infos=dm_dataset.infos(),
            dm_categories=dm_dataset.categories(),
            dst=dst_project,
            label_to_ann_types=labels_map if calc_label_to_ann_types else {},
        )

        # Assert
        assert infos["GetiProjectTask"] == ImportUtils.project_type_to_rest_api_string(dst_project)
        self._check_expected_labels(categories, ["label0", "label1", "detection label"])
        if calc_label_to_ann_types:
            assert label_to_ann_types == {
                "label0": {AnnotationType.polygon},
                "label1": {AnnotationType.polygon},
                "detection label": {AnnotationType.bbox},
            }
        else:
            assert label_to_ann_types == {}

    def test_converter_seg2detseg__get_converted_label_info_error(self, fxt_datumaro_dataset_segmentation):
        # Arrange
        dm_dataset: Dataset = fxt_datumaro_dataset_segmentation
        convertor = CrossProjectConverterSegToDetSeg()
        dst_project = GetiProjectType.CHAINED_DETECTION_SEGMENTATION
        dm_infos = dm_dataset.infos()
        dm_categories = dm_dataset.categories()
        dm_labels_map = {
            "label0": {AnnotationType.polygon},
            "label1": {AnnotationType.polygon},
            "detection label": {AnnotationType.bbox},
        }
        wrong_labels_to_ann_types = LabelInfo(
            dm_infos,
            dm_categories,
            dm_labels_map,
        )

        # Act & Assert
        with patch("job.utils.cross_project_mapping.super") as mocked_super, pytest.raises(ResearvedLabelException):
            mocked_super().get_converted_label_info.return_value = wrong_labels_to_ann_types
            _ = convertor.get_converted_label_info(
                dm_infos=dm_infos, dm_categories=dm_categories, dst=dst_project, label_to_ann_types=dm_labels_map
            )
            mocked_super().get_converted_label_info.assert_called()

    def test_converter_detseg2seg__convert_annotation_type(self, fxt_datumaro_dataset_chained_det_seg):
        # Arrange
        dm_dataset: Dataset = fxt_datumaro_dataset_chained_det_seg
        src_def = self._get_ann_definition(dm_dataset)
        convertor = CrossProjectConverterDetSegToSeg()

        # Act
        convertor.convert_annotation_type(dm_dataset=dm_dataset)
        dst_def = self._get_ann_definition(dm_dataset)

        # Assert
        assert set(src_def.keys()) == set(dst_def.keys())
        label_cat: LabelCategories = dm_dataset.categories()[AnnotationType.label]
        det_label_id = label_cat.find("det")[0]
        for id, anns in src_def.items():
            filtered = []
            for src in anns:
                if src.label != det_label_id:
                    filtered.append(src)
            for src, dst in zip(filtered, dst_def[id]):
                assert src == dst

    @pytest.mark.parametrize("calc_label_to_ann_types", [True, False])
    def test_converter_detseg2seg__get_converted_label_info(
        self, fxt_datumaro_dataset_chained_det_seg, calc_label_to_ann_types
    ):
        # Arrange
        dm_dataset: Dataset = fxt_datumaro_dataset_chained_det_seg
        convertor = CrossProjectConverterDetSegToSeg()
        dst_project = GetiProjectType.SEGMENTATION
        labels_map = ImportUtils.get_label_to_ann_types(dm_dataset=dm_dataset)

        # Act
        infos, categories, label_to_ann_types = convertor.get_converted_label_info(
            dm_infos=dm_dataset.infos(),
            dm_categories=dm_dataset.categories(),
            dst=dst_project,
            label_to_ann_types=labels_map if calc_label_to_ann_types else {},
        )

        # Assert
        assert infos["GetiProjectTask"] == ImportUtils.project_type_to_rest_api_string(dst_project)
        self._check_expected_labels(categories, ["label0", "label1", "label2"])
        if calc_label_to_ann_types:
            assert label_to_ann_types == {
                "label0": {AnnotationType.polygon},
                "label1": {AnnotationType.polygon},
                "label2": {AnnotationType.polygon},
            }
        else:
            assert label_to_ann_types == {}

    def test_converter_detseg2det__convert_annotation_type(self, fxt_datumaro_dataset_chained_det_seg):
        # Arrange
        dm_dataset: Dataset = fxt_datumaro_dataset_chained_det_seg
        src_def = self._get_ann_definition(dm_dataset)
        convertor = CrossProjectConverterDetSegToDet()

        # Act
        convertor.convert_annotation_type(dm_dataset=dm_dataset)
        dst_def = self._get_ann_definition(dm_dataset)

        # Assert
        assert set(src_def.keys()) == set(dst_def.keys())
        label_cat: LabelCategories = dm_dataset.categories()[AnnotationType.label]
        det_label_id = label_cat.find("det")[0]
        for id, anns in src_def.items():
            filtered = []
            for src in anns:
                if src.label != det_label_id:
                    filtered.append(src)
            for src, dst in zip(filtered, dst_def[id]):
                if src.type in [AnnotationType.polygon, AnnotationType.mask, AnnotationType.ellipse]:
                    dst.type == AnnotationType.bbox
                assert src.label == dst.label

    def test_converter_detseg2rot__convert_annotation_type(self, fxt_datumaro_dataset_chained_det_seg):
        # Arrange
        dm_dataset: Dataset = fxt_datumaro_dataset_chained_det_seg
        src_def = self._get_ann_definition(dm_dataset)
        convertor = CrossProjectConverterDetSegToRot()

        # Act
        convertor.convert_annotation_type(dm_dataset=dm_dataset)
        dst_def = self._get_ann_definition(dm_dataset)

        # Assert
        assert set(src_def.keys()) == set(dst_def.keys())
        label_cat: LabelCategories = dm_dataset.categories()[AnnotationType.label]
        det_label_id = label_cat.find("det")[0]
        for id, anns in src_def.items():
            filtered = []
            for src in anns:
                if src.label != det_label_id:
                    filtered.append(src)
            for src, dst in zip(filtered, dst_def[id]):
                if src.type in [
                    AnnotationType.polygon,
                    AnnotationType.mask,
                    AnnotationType.ellipse,
                    AnnotationType.bbox,
                ]:
                    dst.type == AnnotationType.polygon
                assert src.label == dst.label

    @staticmethod
    def _get_ann_definition(dm_dataset: Dataset) -> dict[str, list[ANN]]:
        definition = {}
        for item in dm_dataset:
            definition[item.id] = [ANN(ann.type, ann.label) for ann in item.annotations]
        return definition

    @staticmethod
    def _check_expected_labels(categories: CategoriesInfo, expected_labels: list[str]) -> None:
        label_cat: LabelCategories = categories[AnnotationType.label]
        assert len(label_cat) == len(expected_labels)
        for label in expected_labels:
            assert label_cat.find(label)[1] == LabelCategories.Category(name=label, parent="", attributes=set())

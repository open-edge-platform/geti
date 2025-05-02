# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from unittest.mock import patch

import pytest
from geti_types import ID
from iai_core_py.entities.label import Domain
from iai_core_py.entities.project import Project
from iai_core_py.utils.deletion_helpers import DeletionHelpers
from jobs_common.features.feature_flag_provider import FeatureFlag, FeatureFlagProvider
from jobs_common_extras.datumaro_conversion.definitions import CHAINED_PROJECT_TYPES, GetiProjectType

from job.repos.data_repo import ImportDataRepo
from job.tasks.import_tasks.parse_dataset_existing_project import _parse_dataset_for_import_to_existing_project
from job.utils.import_utils import ImportUtils
from tests.fixtures.datasets import DatasetInfo, get_dataset_info, warning_local_annotations_lost, warning_missing_ann
from tests.test_helpers import save_dataset


@pytest.mark.DatasetIEMsComponent
class TestParseDatasetExistingProject:
    """
    Unit test for parse_dataset_existing_project.py
    """

    @staticmethod
    def _get_expected_warnings_for_specific_task(
        project_type: GetiProjectType,
        dataset_info: DatasetInfo,
        expected_labels: set[str],
        possible_domains_from_cross: bool = False,
    ) -> set[tuple]:
        warnings: set[tuple] = set()
        warnings.update(dataset_info.warnings.get(Domain.NULL, set()))
        if possible_domains_from_cross:
            domain = ImportUtils.project_type_to_label_domain(dataset_info.exported_project_type)
            possible_domains = {domain}
            possible_domains.update(
                map(ImportUtils.project_type_to_label_domain, dataset_info.label_names_by_cross_project.keys())
            )
        else:
            possible_domains = set()
            domains = map(
                ImportUtils.project_type_to_label_domain, dataset_info.label_names_by_ann_based_project.keys()
            )
            if domains:
                possible_domains.update(domains)

        domain = ImportUtils.project_type_to_label_domain(project_type=project_type)
        warning = dataset_info.warnings.get(domain, None)
        if warning and (domain in possible_domains or possible_domains_from_cross):
            warnings.update(warning)
        elif domain not in possible_domains:
            warning = warning_missing_ann(domain, dataset_info.num_items)
            if warning is not None:
                warnings.add(tuple(warning))

        if len(expected_labels) == 0:
            warnings.add(
                (
                    "warning",
                    f"The dataset does not contain any valid labels for the task {project_type.name.title()}",
                    "It is possible to import the dataset into the "
                    "project, but the media will need to be labelled "
                    "manually through the annotator page.",
                )
            )
        return warnings

    @staticmethod
    def _parse_dataset_for_import_to_existing_project(
        data_repo: ImportDataRepo, dataset_id: ID, project: Project
    ) -> tuple[list, list]:
        with patch("job.tasks.import_tasks.parse_dataset_existing_project.ImportDataRepo", return_value=data_repo):
            label_names, warnings = _parse_dataset_for_import_to_existing_project(
                import_id=str(dataset_id),
                project_id=str(project.id_),
            )

        return list(label_names), list(warnings)

    def _check_label_names_from_parse_dataset_for_import_to_existing_project(
        self,
        request: pytest.FixtureRequest,
        data_repo: ImportDataRepo,
        dataset_id: ID,
        project: Project,
        expected_labels: set[str],
        expected_warnings: set[tuple],
        project_type: GetiProjectType,
    ):
        request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project.id_))

        try:
            label_names, warnings = self._parse_dataset_for_import_to_existing_project(
                data_repo,
                dataset_id=dataset_id,
                project=project,
            )

            assert set(label_names) == expected_labels, (project_type, label_names)
            assert len(warnings) == len(expected_warnings)
            for w in warnings:
                warning = [w["type"], w["name"], w["description"]]
                if "affected_images" in w:
                    warning.append(w["affected_images"])
                assert tuple(warning) in expected_warnings

        except ValueError as e:
            assert project_type in CHAINED_PROJECT_TYPES
            assert e.args[0] == "Dataset import is not currently supported for task chain projects."

    def _test_parse_dataset_for_import_to_existing_project__datumaro_format(
        self,
        request,
        dataset_id,
        dataset_info,
        project_str,
        project,
        import_data_repo,
    ):
        project_type = ImportUtils.get_project_type(project)

        possible_domains_from_cross = True
        if project_str == dataset_info.fxt_corresponding_project:
            expected_labels = dataset_info.label_names
        elif project_type in dataset_info.label_names_by_cross_project:
            if (
                project_type == GetiProjectType.CLASSIFICATION
                and dataset_info.exported_project_type == GetiProjectType.DETECTION
                and project_str != "fxt_annotated_multi_label_project"
            ):
                # detection -> multi-label classification only (h-cls and s-cls are not supported)
                expected_labels = set()
                possible_domains_from_cross = False
            else:
                expected_labels = dataset_info.label_names_by_cross_project[project_type]
        else:
            expected_labels = set()
        warnings = self._get_expected_warnings_for_specific_task(
            project_type, dataset_info, expected_labels, possible_domains_from_cross=possible_domains_from_cross
        )

        if (
            FeatureFlagProvider.is_enabled(feature_flag=FeatureFlag.FEATURE_FLAG_ANOMALY_REDUCTION)
            and project_type == GetiProjectType.ANOMALY_CLASSIFICATION
            and dataset_info.exported_project_type
            in [
                GetiProjectType.ANOMALY_DETECTION,
                GetiProjectType.ANOMALY_SEGMENTATION,
            ]
        ):
            warnings.add(warning_local_annotations_lost())

        self._check_label_names_from_parse_dataset_for_import_to_existing_project(
            request, import_data_repo, dataset_id, project, expected_labels, warnings, project_type
        )

        # import dataset based on annotation type. (assume the dataset is not exported from Geti)
        with patch(
            "jobs_common_extras.datumaro_conversion.import_utils.ImportUtils.get_exported_project_type",
            return_value=GetiProjectType.UNKNOWN,
        ) as mock_get_exported_project_type:
            if project_type in dataset_info.label_names_by_ann_based_project:
                expected_labels = dataset_info.label_names_by_ann_based_project[project_type]
            else:
                expected_labels = set()
            warnings = self._get_expected_warnings_for_specific_task(project_type, dataset_info, expected_labels)
            self._check_label_names_from_parse_dataset_for_import_to_existing_project(
                request, import_data_repo, dataset_id, project, expected_labels, warnings, project_type
            )

            if project_type not in CHAINED_PROJECT_TYPES:
                mock_get_exported_project_type.assert_called()

    def test_parse_dataset_for_import_to_existing_project__datumaro_format(
        self,
        request,
        fxt_dataset_id__datumaro,
        fxt_project,
        fxt_import_data_repo,
    ):
        fxt_dataset_id, dataset_info = fxt_dataset_id__datumaro
        fxt_project_str, project = fxt_project
        self._test_parse_dataset_for_import_to_existing_project__datumaro_format(
            request, fxt_dataset_id, dataset_info, fxt_project_str, project, fxt_import_data_repo
        )

    @pytest.mark.parametrize(
        "anomaly_dataset_id",
        (
            "fxt_datumaro_dataset_anomaly_cls_id",
            "fxt_datumaro_dataset_anomaly_det_id",
            "fxt_datumaro_dataset_anomaly_seg_id",
        ),
    )
    def test_parse_dataset_for_import_to_existing_project__datumaro_format__anomaly(
        self,
        request,
        anomaly_dataset_id,
        fxt_annotated_anomaly_cls_project,
        fxt_enable_feature_flag_name,
        fxt_import_data_repo,
    ):
        """
        Test if warning is generated for mapping from anomaly det/seg -> anomaly cls.
        if FEATURE_FLAG_ANOMALY_REDUCTION is enabled.
        """
        fxt_enable_feature_flag_name(FeatureFlag.FEATURE_FLAG_ANOMALY_REDUCTION.name)

        dataset_id = request.getfixturevalue(anomaly_dataset_id)
        dataset_info = get_dataset_info(anomaly_dataset_id)
        project_str = "fxt_annotated_anomaly_cls_project"
        project = fxt_annotated_anomaly_cls_project

        self._test_parse_dataset_for_import_to_existing_project__datumaro_format(
            request, dataset_id, dataset_info, project_str, project, fxt_import_data_repo
        )

    def test_parse_dataset_for_import_to_existing_project__public_format(
        self,
        request,
        fxt_dataset_id__public,
        fxt_project,
        fxt_import_data_repo,
    ):
        fxt_dataset_id, dataset_info = fxt_dataset_id__public
        _, project = fxt_project

        project_type = ImportUtils.get_project_type(project)

        if project_type in dataset_info.label_names_by_ann_based_project:
            expected_labels = dataset_info.label_names_by_ann_based_project[project_type]
        else:
            expected_labels = set()
        warnings = self._get_expected_warnings_for_specific_task(project_type, dataset_info, expected_labels)

        self._check_label_names_from_parse_dataset_for_import_to_existing_project(
            request, fxt_import_data_repo, fxt_dataset_id, project, expected_labels, warnings, project_type
        )

    def test_parse_dataset_for_import_to_existing_project__by_annotation_types(
        self,
        request,
        fxt_dataset_definition,
        fxt_dataset_labels,
        fxt_dm_dataset_generator,
        fxt_project,
        fxt_import_data_repo,
    ):
        dm_dataset_definition, dataset_info = fxt_dataset_definition
        label_names = [label["name"] for label in fxt_dataset_labels]
        dm_dataset = fxt_dm_dataset_generator(label_names, dm_dataset_definition)
        dataset_id = save_dataset(fxt_import_data_repo, dm_dataset, "datumaro")

        _, project = fxt_project
        project_type = ImportUtils.get_project_type(project)

        if project_type in dataset_info.label_names_by_ann_based_project:
            expected_labels = dataset_info.label_names_by_ann_based_project[project_type]
        else:
            expected_labels = set()
        warnings = self._get_expected_warnings_for_specific_task(project_type, dataset_info, expected_labels)

        self._check_label_names_from_parse_dataset_for_import_to_existing_project(
            request, fxt_import_data_repo, dataset_id, project, expected_labels, warnings, project_type
        )

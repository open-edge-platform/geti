# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import datetime
import os
from collections.abc import Mapping, Sequence
from enum import Enum, auto
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import datumaro as dm
import pkg_resources
import pytest
from datumaro.components.annotation import GroupType, LabelCategories
from geti_types import CTX_SESSION_VAR, ID, ProjectIdentifier
from jobs_common.features.feature_flag_provider import FeatureFlag, FeatureFlagProvider
from jobs_common.tasks.utils.secrets import JobMetadata
from jobs_common_extras.datumaro_conversion.definitions import (
    ANOMALY_PROJECT_TYPES,
    SUPPORTED_DOMAIN_TO_ANNOTATION_TYPES,
    GetiProjectType,
)
from sc_sdk.algorithms import ModelTemplateList
from sc_sdk.entities.annotation import AnnotationScene
from sc_sdk.entities.label import Label
from sc_sdk.entities.label_schema import LabelSchema, NullLabelSchema
from sc_sdk.entities.media import ImageExtensions
from sc_sdk.entities.model_template import NullModelTemplate, TaskType
from sc_sdk.entities.project import NullProject, Project
from sc_sdk.entities.shapes import Ellipse, Polygon, Rectangle
from sc_sdk.repos import AnnotationSceneRepo, ImageRepo, LabelSchemaRepo, ProjectRepo
from sc_sdk.repos.base import SessionBasedRepo
from sc_sdk.utils.deletion_helpers import DeletionHelpers
from sc_sdk.utils.project_builder import ModelTemplateError

from job.repos.data_repo import ImportDataRepo
from job.repos.object_storage_repo import ObjectStorageRepo
from job.tasks.import_tasks.create_project_from_dataset import create_project_from_dataset
from job.tasks.import_tasks.import_dataset_to_project import import_dataset_to_project
from job.tasks.import_tasks.parse_dataset_existing_project import parse_dataset_for_import_to_existing_project
from job.tasks.import_tasks.parse_dataset_new_project import parse_dataset_for_import_to_new_project
from job.utils.exceptions import (
    DatasetFormatException,
    FileNotFoundException,
    InvalidIDException,
    InvalidLabelException,
    ProjectNotFoundException,
)
from job.utils.import_utils import ImportUtils
from tests.conftest import URL_DATASETS, download_file
from tests.fixtures.datasets import AnnotationDefinition, DatasetDefinition, get_dataset_info
from tests.test_helpers import (
    check_dataset_items,
    check_thumbnails,
    check_video_annotation_ranges,
    convert_dataset_definition_for_cross_project,
    get_dm_dataset_definition,
    get_label_maps,
    get_media_ann_scenes_from_project_id,
    get_project_labels,
    return_none,
    save_dataset,
    save_dataset_with_path,
)

workspace_id = ID("import_workspace")


class BAD_DATASET_FILE_TEST(Enum):
    BAD_FILE_ID = auto()
    DUMMY_DATASET = auto()
    UNSUPPORTED_DATASET = auto()


class IMPORT_EXISTING_ERROR_TEST(Enum):
    INVALID_FILE_ID = auto()
    NON_EXISTING_FILE = auto()
    INVALID_PROJECT_ID = auto()
    NON_EXISTING_PROJECT = auto()
    WRONG_LABEL_NAME = auto()  # not existing label in dataset
    WRONG_LABEl_ID = auto()  # not existing label in project


@pytest.mark.DatasetIEMsComponent
class TestImportDataset:
    """
    Integration test the import dataset
    """

    def _get_dm_dataset_from_definition(
        self,
        request,
        dataset_definition: Mapping[str, Sequence[tuple[str, Any]]],
        label_names: Sequence[str] | dm.CategoriesInfo,
        dm_infos: dict | None = None,
        subsets: Sequence[str] = [dm.DEFAULT_SUBSET_NAME],
    ) -> dm.Dataset:
        """
        Generate dm_datset from definition.
        """
        dm_dataset_generator = request.getfixturevalue("fxt_dm_dataset_generator")
        dm_dataset = dm_dataset_generator(label_names, dataset_definition, subsets=subsets)
        if dm_infos:
            dm_dataset.transform("project_infos", dst_infos=dm_infos, overwrite=False)
        return dm_dataset

    def _create_geti_exported_dataset_from_definition(
        self,
        request,
        project_type: GetiProjectType,
        dataset_definition: Mapping[str, Sequence[tuple[str, Any]]],
        is_multi_label: bool = False,
    ) -> dm.Dataset:
        """
        Generate Geti exported dm_datset from definition.
        """
        if project_type in ANOMALY_PROJECT_TYPES:
            label_names, dm_dataset, _ = self._create_anomaly_dataset(request, project_type, dataset_definition)
        else:
            fxt_dataset_labels = request.getfixturevalue("fxt_dataset_labels")
            label_names = [label["name"] for label in fxt_dataset_labels]
            dm_infos = {"GetiProjectTask": ImportUtils.project_type_to_rest_api_string(project_type)}
            if project_type == GetiProjectType.CLASSIFICATION and is_multi_label:
                label_categories = LabelCategories()
                for label_name in label_names:
                    label_categories.add(label_name, parent="")
                    label_categories.add_label_group(
                        name=f"Classification labels___{label_name}",
                        labels=[label_name],
                        group_type=GroupType.EXCLUSIVE,
                    )
                label_categories = {dm.AnnotationType.label: label_categories}
            else:
                label_categories = None
            dm_dataset = self._get_dm_dataset_from_definition(
                request,
                dataset_definition,
                label_names=label_names if label_categories is None else label_categories,
                dm_infos=dm_infos,
            )

        return label_names, dm_dataset

    def _create_anomaly_dataset(self, request, project_type: GetiProjectType, dm_dataset_definition):
        """
        Generate Geti exported anomaly datset from definition.
        """
        # get fixtures
        fxt_anomaly_dataset_labels = request.getfixturevalue("fxt_anomaly_dataset_labels")
        fxt_dm_categories_generator = request.getfixturevalue("fxt_dm_categories_generator")

        label_names = [label["name"] for label in fxt_anomaly_dataset_labels]
        global_parent_name = ""
        global_group_name = f"default - {project_type.name} task"
        label_categories = fxt_dm_categories_generator(global_parent_name, global_group_name, label_names)
        dm_infos = {
            "GetiProjectTask": ImportUtils.project_type_to_rest_api_string(project_type),
            "GetiAnomalyLabels": [
                label["name"] for label in fxt_anomaly_dataset_labels if label.get("is_anomalous", False)
            ],
        }
        dm_dataset = self._get_dm_dataset_from_definition(
            request, dm_dataset_definition, label_names={dm.AnnotationType.label: label_categories}, dm_infos=dm_infos
        )
        return label_names, dm_dataset, global_group_name

    @staticmethod
    def _prepare_import_new_project_workflow(data_repo: ImportDataRepo, dataset_id: ID) -> tuple[list, list]:
        supported_project_types, warnings = [], []

        def _get_metadata(metadata: dict):
            nonlocal supported_project_types, warnings
            supported_project_types, warnings = metadata["supported_project_types"], metadata["warnings"]

        with (
            patch("job.tasks.import_tasks.parse_dataset_new_project.publish_metadata_update", new=_get_metadata),
            patch("job.tasks.import_tasks.parse_dataset_new_project.ImportDataRepo", return_value=data_repo),
        ):
            parse_dataset_for_import_to_new_project(import_id=str(dataset_id))

        return supported_project_types, warnings

    @staticmethod
    def _create_project_from_dataset_workflow(
        request,
        data_repo: ImportDataRepo,
        dataset_id: ID,
        project_name: str,
        project_type: GetiProjectType,
        label_names: list[str],
        keypoint_structure: dict[str, list[dict]] = {"edges": [], "positions": []},
    ) -> ID:
        project_id = ID("")

        def _get_metadata(metadata: dict):
            nonlocal project_id
            project_id = metadata["project_id"]

        with (
            patch("job.tasks.import_tasks.create_project_from_dataset.publish_metadata_update", new=_get_metadata),
            patch("job.tasks.import_tasks.create_project_from_dataset.ImportDataRepo", return_value=data_repo),
        ):
            colors_by_label = {}
            for label in label_names:
                colors_by_label[label] = "#998f49"
            create_project_from_dataset(
                import_id=str(dataset_id),
                name=project_name,
                project_type_str=project_type.name,
                label_names=label_names,
                color_by_label=colors_by_label,
                keypoint_structure=keypoint_structure,
                user_id="dummy_user",
            )

        if request:
            request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=ID(project_id)))
        return project_id

    @staticmethod
    def _prepare_import_existing_project_workflow(
        data_repo: ImportDataRepo, dataset_id: ID, project: Project
    ) -> tuple[list, list]:
        label_names, warnings = [], []

        def _get_labels_warnings(metadata: dict):
            nonlocal label_names, warnings
            label_names, warnings = metadata["labels"], metadata["warnings"]

        with (
            patch(
                "job.tasks.import_tasks.parse_dataset_existing_project.publish_metadata_update",
                new=_get_labels_warnings,
            ),
            patch("job.tasks.import_tasks.parse_dataset_existing_project.ImportDataRepo", return_value=data_repo),
        ):
            parse_dataset_for_import_to_existing_project(
                import_id=str(dataset_id),
                project_id=str(project.id_),
            )

        return label_names, warnings

    @staticmethod
    def _import_dataset_to_project_workflow(
        data_repo: ImportDataRepo,
        dataset_id: ID,
        project: Project,
        labels_map: dict[str, Label],
        dataset_name: str,
    ) -> None:
        dataset_storage = project.get_training_dataset_storage()
        labels_map_str = {key: str(label.id_) for key, label in labels_map.items()}

        with (
            patch("job.tasks.import_tasks.import_dataset_to_project.ImportDataRepo", return_value=data_repo),
            patch("job.tasks.import_tasks.import_dataset_to_project.publish_metadata_update"),
        ):
            import_dataset_to_project(
                import_id=str(dataset_id),
                project_id=str(project.id_),
                label_ids_map=labels_map_str,
                dataset_storage_id=str(dataset_storage.id_),
                dataset_name=dataset_name,
                user_id="dummy_user",
            )

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @patch("job.repos.data_repo.ObjectStorageRepo")
    def test_import_to_datumaro_no_warnings(
        self,
        mocked_object_storage_repo_init,
        fxt_import_data_repo,
        fxt_dataset_id,
        fxt_datumaro_bbox_polygon_dataset,
    ):
        """
        Test importing dataset to datumaro with no warnings
            - import already-in-filesystem dataset to datumaro format
            - assert no warnings returned
            - assert label_to_domains dict contains the expected labels
        """
        mock_object_storage_repo = MagicMock(spec=ObjectStorageRepo)
        mocked_object_storage_repo_init.return_value = mock_object_storage_repo
        supported_project_types, warnings = self._prepare_import_new_project_workflow(
            data_repo=fxt_import_data_repo, dataset_id=fxt_dataset_id
        )
        dataset_labels = {o.name for o in fxt_datumaro_bbox_polygon_dataset.categories()[dm.AnnotationType.label]}

        assert len(warnings) == 0
        assert len(dataset_labels) == 4  # 4 labels are defined for the dataset

        # fxt_dataset_id has 'fxt_bbox_polygon_dataset_definition'
        # that is, {"item1": {("bbox", 2), ("bbox", 1), ("polygon", 1)}}
        #   DETECTION --> {("bbox", 2), ("bbox", 1)}
        #   SEG/INS_SEG --> {("bbox", 2), ("polygon", 1)}
        project_types = self._get_candidate_project_types(supported_project_types)
        expected_types = {  # bbox -> detection, polygon -> seg, ins-seg.
            GetiProjectType.DETECTION,
            GetiProjectType.SEGMENTATION,
            GetiProjectType.INSTANCE_SEGMENTATION,
        }
        assert set(project_types) == expected_types
        for project_type in project_types:
            label_names = self._get_all_label_names_from_supported_project_types(supported_project_types, project_type)
            assert len(label_names) == 2
            for label_name in label_names:
                assert label_name in dataset_labels

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @patch("job.repos.data_repo.ObjectStorageRepo")
    def test_import_dataset_with_multiple_subsets(
        self,
        mocked_object_storage_repo_init,
        fxt_import_data_repo,
        fxt_coco_dataset_multi_subsets_id,
        request,
    ):
        """
        Test importing dataset to datumaro with no warnings
            - import already-in-filesystem dataset to datumaro format
            - assert no warnings returned
            - assert label_to_domains dict contains the expected labels
        """
        mock_object_storage_repo = MagicMock(spec=ObjectStorageRepo)
        mocked_object_storage_repo_init.return_value = mock_object_storage_repo

        dataset_id = fxt_coco_dataset_multi_subsets_id
        project_type = GetiProjectType.DETECTION

        dataset_dir = fxt_import_data_repo.get_dataset_directory(id_=dataset_id)
        dm_dataset = dm.Dataset.import_from(dataset_dir, "coco")

        supported_project_types, warnings = self._prepare_import_new_project_workflow(
            data_repo=fxt_import_data_repo, dataset_id=dataset_id
        )

        assert len(warnings) == 1
        assert warnings[0]["name"] == "Subset merging"

        candidate_project_types = self._get_candidate_project_types(supported_project_types=supported_project_types)
        assert candidate_project_types == [project_type]

        labels_to_keep = self._get_all_label_names_from_supported_project_types(supported_project_types, project_type)

        project_id = self._create_project_from_dataset_workflow(
            request,
            data_repo=fxt_import_data_repo,
            dataset_id=dataset_id,
            project_name="_test_import_dataset_with_multi_subsets",
            project_type=project_type,
            label_names=labels_to_keep,
        )

        images, _, annotation_scenes = get_media_ann_scenes_from_project_id(project_id=project_id)
        check_thumbnails(ID(project_id), images)

        assert len(dm_dataset) == len(images)
        name_to_anns = {}
        ids = set()
        for item in dm_dataset:
            if item.id in ids:
                sc_image_name = f"{item.id}_{item.subset}"
            else:
                sc_image_name = f"{item.id}"
                ids.add(item.id)
            name_to_anns[sc_image_name] = len(item.annotations)
        id_to_name = {}
        for img in images:
            id_to_name[img.id_] = img.name
        for scene in annotation_scenes:
            assert len(scene.shapes) == name_to_anns[id_to_name[scene.media_identifier.media_id]]

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @patch("job.repos.data_repo.ObjectStorageRepo")
    def test_import_all_annotations(
        self,
        mocked_object_storage_repo_init,
        request,
        fxt_import_data_repo,
        fxt_coco_dataset_id,
    ):
        """
        Test full import of dataset to project
            - import dataset and pick labels and domain compatible with loaded dataset
            - create project with domain, labels, and name
            - assert that images and annotations are successfully committed
        """
        mock_object_storage_repo = MagicMock(spec=ObjectStorageRepo)
        mocked_object_storage_repo_init.return_value = mock_object_storage_repo
        project = self._import_two_labels_project_from_dataset(
            request=request,
            file_id=fxt_coco_dataset_id,
            project_type=GetiProjectType.DETECTION,
            data_repo=fxt_import_data_repo,
        )

        dataset_storage = project.get_training_dataset_storage()
        image_repo = ImageRepo(dataset_storage.identifier)
        ann_scene_repo = AnnotationSceneRepo(dataset_storage.identifier)
        images = list(image_repo.get_all())
        ann_scenes = list(ann_scene_repo.get_all())

        assert len(images) == 11
        assert len(ann_scenes) == 11
        annotations = ann_scenes[0].annotations
        assert len(annotations) > 0
        for ann in annotations:
            assert isinstance(ann.shape, Rectangle)
        for image in images:
            assert image.extension == ImageExtensions.JPG

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @patch("job.repos.data_repo.ObjectStorageRepo")
    @pytest.mark.parametrize(
        "project_type,has_empty_label",
        [
            (GetiProjectType.DETECTION, True),
        ],
        ids=[
            "Detection",
        ],
    )
    def test_import_labels_created(
        self,
        mocked_object_storage_repo_init,
        request,
        project_type,
        has_empty_label,
        fxt_import_data_repo,
        fxt_coco_dataset_id,
    ):
        """
        Test full import of dataset to project
            - import dataset and pick labels and domain compatible with loaded dataset
            - create project with domain, labels, and name
            - assert that created labels are one more than requested (empty label)
              except in the case of binary classification when no empty label is created
        """
        mocked_object_storage_repo_init.return_value = MagicMock()
        project = self._import_two_labels_project_from_dataset(
            request=request, file_id=fxt_coco_dataset_id, project_type=project_type, data_repo=fxt_import_data_repo
        )
        labels = get_latest_labels_for_project(project_id=project.id_, include_empty=True)
        assert not isinstance(project, NullProject)
        assert len(labels) == 2 + int(has_empty_label)

    def _get_all_label_names_from_supported_project_types(
        self,
        supported_project_types: list[dict[str, Any]],
        project_type: GetiProjectType,
    ) -> list[str]:
        """
        Get all label_names of project from the supported_project_types
        which is output of prepare_import_new_project_workflow()

        :param supported_project_types: an output of prepare_import_new_project_workflow()
        :param project_type: the target Geti project type
        :return: A list of all label_names included in the project piplelines
        """
        label_names: set[str] = set()
        project_type_str = ImportUtils.project_type_to_rest_api_string(project_type)
        for project_meta in supported_project_types:
            if project_meta["project_type"] == project_type_str:
                for task in project_meta["pipeline"]["tasks"]:
                    label_names.update(label["name"] for label in task["labels"])
                break
        return list(label_names)

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @patch("job.repos.data_repo.ObjectStorageRepo")
    def test_import_unannotated_dataset(
        self,
        mocked_object_storage_repo_init,
        fxt_import_data_repo,
        request,
    ):
        """
        Test importing dataset to datumaro with no warnings
            - import already-in-filesystem dataset to datumaro format
            - assert no warnings returned
            - assert label_to_domains dict contains the expected labels
        """
        mock_object_storage_repo = MagicMock(spec=ObjectStorageRepo)
        mocked_object_storage_repo_init.return_value = mock_object_storage_repo

        fmt = "datumaro"
        project_type = GetiProjectType.INSTANCE_SEGMENTATION
        unannotated_dataset_definition = {
            "item1": {("polygon", 0)},
            "item2": set(),
            "item3": set(),
        }

        label_names, dm_dataset = self._create_geti_exported_dataset_from_definition(
            request, project_type, unannotated_dataset_definition
        )
        dataset_id = save_dataset(fxt_import_data_repo, dm_dataset, fmt)

        supported_project_types, warnings = self._prepare_import_new_project_workflow(
            data_repo=fxt_import_data_repo, dataset_id=dataset_id
        )

        assert len(warnings) == 2
        for w in warnings:
            assert (
                w["name"] == "Missing expected annotation type for segmentation domain"
                or w["name"] == "Missing expected annotation type for detection domain"
            )
            assert w["affected_images"] == 2

        candidate_project_types = self._get_candidate_project_types(supported_project_types=supported_project_types)
        assert set(candidate_project_types) == {
            GetiProjectType.INSTANCE_SEGMENTATION,
            GetiProjectType.SEGMENTATION,
            GetiProjectType.DETECTION,
            GetiProjectType.CHAINED_DETECTION_SEGMENTATION,
        }

        labels_to_keep = self._get_all_label_names_from_supported_project_types(supported_project_types, project_type)
        assert set(labels_to_keep) == set(label_names)

        project_id = self._create_project_from_dataset_workflow(
            request,
            data_repo=fxt_import_data_repo,
            dataset_id=dataset_id,
            project_name="_test_import_unannotated_dataset",
            project_type=project_type,
            label_names=labels_to_keep,
        )

        images, _, annotation_scenes = get_media_ann_scenes_from_project_id(project_id=project_id)
        assert len(images) == 3

        # since CVS-98893, Geti does no longer require empty annotations to represent unannotated media in the database
        assert len(annotation_scenes) == 1

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @pytest.mark.parametrize(
        "dataset_definition,fmt,n_warnings,project_type,",
        [
            ["fxt_bbox_dataset_definition", "coco", 0, GetiProjectType.DETECTION],
            [
                "fxt_polygon_coco_dataset_definition",
                "coco",
                0,
                GetiProjectType.SEGMENTATION,
            ],
            [
                "fxt_polygon_coco_dataset_definition",
                "coco",
                0,
                GetiProjectType.INSTANCE_SEGMENTATION,
            ],
            ["fxt_bbox_dataset_definition", "voc", 0, GetiProjectType.DETECTION],
            [
                "fxt_polygon_dataset_definition",
                "voc",
                0,
                GetiProjectType.SEGMENTATION,
            ],
            [
                "fxt_polygon_dataset_definition",
                "voc",
                0,
                GetiProjectType.INSTANCE_SEGMENTATION,
            ],
            [
                "fxt_bbox_polygon_dataset_definition",
                "voc",
                0,
                GetiProjectType.DETECTION,
            ],
            [
                "fxt_bbox_polygon_dataset_definition",
                "voc",
                0,
                GetiProjectType.INSTANCE_SEGMENTATION,
            ],  # CVS-126710. Bboxes should be imported, too.
            [
                "fxt_polygon_dataset_definition",
                "voc",
                0,
                GetiProjectType.SEGMENTATION,
            ],
            ["fxt_bbox_dataset_definition", "yolo", 0, GetiProjectType.DETECTION],
            [
                "fxt_global_labels_dataset_definition",
                "voc",
                0,
                GetiProjectType.CLASSIFICATION,
            ],
            [
                "fxt_multi_label_dataset_definition",
                "voc",
                2,
                GetiProjectType.CLASSIFICATION,
            ],
            ["fxt_bbox_dataset_definition", "datumaro", 0, GetiProjectType.DETECTION],
            [
                "fxt_polygon_coco_dataset_definition",
                "datumaro",
                0,
                GetiProjectType.SEGMENTATION,
            ],
            [
                "fxt_polygon_and_ellipse_dataset_definition",
                "datumaro",
                0,
                GetiProjectType.INSTANCE_SEGMENTATION,
            ],
            [
                "fxt_polygon_and_ellipse_dataset_definition",
                "datumaro",
                0,
                GetiProjectType.SEGMENTATION,
            ],
            [
                "fxt_multi_label_dataset_definition",
                "datumaro",
                0,
                GetiProjectType.CLASSIFICATION,
            ],
            [
                "fxt_rotated_detection_dataset_definition",
                "datumaro",
                0,
                GetiProjectType.ROTATED_DETECTION,
            ],
            [
                "fxt_mask_voc_dataset_definition",
                "voc",
                0,
                GetiProjectType.SEGMENTATION,
            ],
            [
                "fxt_single_points_dataset_definition",
                "datumaro",
                0,
                GetiProjectType.KEYPOINT_DETECTION,
            ],
        ],
    )
    def test_import_dataset(
        self,
        dataset_definition,
        fmt,
        n_warnings,
        project_type,
        fxt_import_data_repo,
        fxt_dataset_labels,
        fxt_enable_feature_flag_name,
        request,
    ):
        """
        Test importing datasets of different formats into impt projects of different domains
        - Make a datumaro dataset from a given datumaro dataset definition
        - Save datumaro dataset with given format
        - Import dataset into SC while keeping labels which are compatible with the given domain
        - Assert number of warnings is as expected
        - Create project through import manager
        - Retrieve images and annotations in project
        - Check that annotations in project reflect the annotation structure in the pre-import dm dataset
        """
        dm_dataset_definition = request.getfixturevalue(dataset_definition)
        if project_type == GetiProjectType.KEYPOINT_DETECTION:
            fxt_enable_feature_flag_name(FeatureFlag.FEATURE_FLAG_KEYPOINT_DETECTION.name)
            label_names = [label["name"] for label in request.getfixturevalue("fxt_points_dataset_labels")]
        else:
            label_names = [label["name"] for label in fxt_dataset_labels]
        label_categories = None
        dm_infos = None
        if dataset_definition == "fxt_multi_label_dataset_definition":
            dm_infos = {
                "GetiProjectTask": ImportUtils.project_type_to_rest_api_string(GetiProjectType.CLASSIFICATION),
            }
            label_categories = LabelCategories()
            for label_name in label_names:
                label_categories.add(label_name, parent="")
                label_categories.add_label_group(
                    name=f"Classification labels___{label_name}", labels=[label_name], group_type=GroupType.EXCLUSIVE
                )
            label_categories = {dm.AnnotationType.label: label_categories}
        elif project_type == GetiProjectType.ROTATED_DETECTION:
            dm_infos = {
                "GetiProjectTask": ImportUtils.project_type_to_rest_api_string(GetiProjectType.ROTATED_DETECTION),
            }

        dm_dataset = self._get_dm_dataset_from_definition(
            request,
            dm_dataset_definition,
            label_names=label_names if label_categories is None else label_categories,
            dm_infos=dm_infos,
        )

        dataset_id = save_dataset(fxt_import_data_repo, dm_dataset, fmt)

        target_dataset_definition = dm_dataset_definition
        # special case
        if fmt == "voc":
            if dataset_definition == "fxt_multi_label_dataset_definition":
                target_dataset_definition = {}
                for item, anns in dm_dataset_definition.items():
                    if len(anns) == 1:
                        target_dataset_definition[item] = anns
                    else:
                        target_dataset_definition[item] = []
            elif (
                dataset_definition == "fxt_bbox_polygon_dataset_definition"
                and project_type == GetiProjectType.INSTANCE_SEGMENTATION
            ):
                # This case is added to check if the bboxes in the voc dataset
                # can be imported to the Instance segmentation.
                # Regarding ticket is CVS-126710.
                # It seems that the group information is nor preserved and deterministic
                # when 'save_dataset' is called.
                # So we need to re-calculate detaset_definition.
                dataset_dir = fxt_import_data_repo.get_dataset_directory(id_=dataset_id)
                voc_dataset, _ = ImportUtils.parse_dataset(path=dataset_dir, fmt="voc")
                label_names = [o.name for o in voc_dataset.categories()[dm.AnnotationType.label]]
                target_dataset_definition = get_dm_dataset_definition(dm_dataset=voc_dataset, label_names=label_names)

        supported_project_types, warnings = self._prepare_import_new_project_workflow(
            data_repo=fxt_import_data_repo, dataset_id=dataset_id
        )

        labels_to_keep = self._get_all_label_names_from_supported_project_types(supported_project_types, project_type)

        mock_object_storage_repo = fxt_import_data_repo.object_storage_repo
        mock_object_storage_repo.download_file.assert_called_with(
            target_path=fxt_import_data_repo.get_zipped_file_local_path(dataset_id),
            key=f"{fxt_import_data_repo.get_s3_import_directory(dataset_id)}/{fxt_import_data_repo.zipped_file_name}",
        )

        assert len(warnings) == n_warnings, warnings
        assert len(labels_to_keep) > 0

        project_id = self._create_project_from_dataset_workflow(
            request,
            data_repo=fxt_import_data_repo,
            dataset_id=dataset_id,
            project_name=f"_test_import_{fmt}_{project_type.name.lower()}_project",
            project_type=project_type,
            label_names=labels_to_keep,
        )

        images, _, annotation_scenes = get_media_ann_scenes_from_project_id(project_id=project_id)
        check_thumbnails(ID(project_id), images)

        check_dataset_items(
            project_id=project_id,
            project_type=project_type,
            dm_dataset_definition=target_dataset_definition,
            annotation_scenes=annotation_scenes,
            all_labels=label_names,
            labels_to_keep=labels_to_keep,
            exact_same=False if dataset_definition == "fxt_multi_label_dataset_definition" and fmt == "voc" else True,
        )

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    def test_import_dataset_for_keypoint_detection(
        self, fxt_dataumaro_dataset_keypoint_id, fxt_import_data_repo, fxt_enable_feature_flag_name, request
    ) -> None:
        """
        Is is possible to create a chained projects from chained datasets.
        :param fxt_dm_dataset_id_str: fixture string for dm dataset id
        :param project_type: Geti project type to be created
        :param request: request objec
        """
        fxt_enable_feature_flag_name(FeatureFlag.FEATURE_FLAG_KEYPOINT_DETECTION.name)

        dataset_id = fxt_dataumaro_dataset_keypoint_id
        project_type = GetiProjectType.KEYPOINT_DETECTION
        dataset_info = get_dataset_info("fxt_dataumaro_dataset_keypoint_id")
        expected_labels = dataset_info.label_names

        supported_project_types, _ = self._prepare_import_new_project_workflow(
            data_repo=fxt_import_data_repo, dataset_id=dataset_id
        )
        labels_to_keep = self._get_all_label_names_from_supported_project_types(supported_project_types, project_type)
        labels_to_keep = sorted(labels_to_keep)  # to make sure the order is the same to check visibility
        assert set(labels_to_keep) == expected_labels

        project_id = self._create_project_from_dataset_workflow(
            request,
            data_repo=fxt_import_data_repo,
            dataset_id=dataset_id,
            project_name=f"_test_create_{project_type.name.lower()}_project_from_keypoint_dataset",
            project_type=project_type,
            label_names=labels_to_keep,
        )

        label_schema = get_latest_label_schema_for_project(project_id=project_id)
        label_names_project = {label.name for label in label_schema.get_labels(include_empty=False)}

        assert label_names_project == expected_labels

        images, _, annotation_scenes = get_media_ann_scenes_from_project_id(project_id=project_id)
        check_thumbnails(ID(project_id), images)

        # get dataset definition
        dataset_dir = fxt_import_data_repo.get_dataset_directory(id_=dataset_id)
        dm_dataset, _ = ImportUtils.parse_dataset(path=dataset_dir, fmt="datumaro")
        dataset_definition = get_dm_dataset_definition(dm_dataset=dm_dataset, label_names=labels_to_keep)

        # TODO : bump up datumaro to 1.10.0 or higher and remove this
        version = pkg_resources.get_distribution("datumaro").version
        if pkg_resources.parse_version(version) < pkg_resources.parse_version("1.10.0rc1"):
            assert set(dataset_definition["000000063648_498602"]) == {
                ("points", (2,) * 17),
                ("bbox", 0),
            }
            assert set(dataset_definition["000000392711_2166119"]) == {
                ("points", (2,) * 17),
                ("bbox", 0),
            }
            assert set(dataset_definition["000000329592_465021"]) == {
                ("points", (2,) * 17),
                ("bbox", 0),
            }
            assert set(dataset_definition["000000458992_185727"]) == {
                ("points", (2,) * 17),
                ("bbox", 0),
            }
        else:
            assert set(dataset_definition["000000063648_498602"]) == {
                ("points", (2, 0, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2)),
                ("bbox", 0),
            }
            assert set(dataset_definition["000000392711_2166119"]) == {
                ("points", (1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 2, 2, 2, 2, 2, 2)),
                ("bbox", 0),
            }
            assert set(dataset_definition["000000329592_465021"]) == {
                ("points", (2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 0, 2, 0, 2, 2, 2, 2)),
                ("bbox", 0),
            }
            assert set(dataset_definition["000000458992_185727"]) == {
                ("points", (0, 2, 2, 2, 1, 0, 2, 2, 2, 0, 2, 2, 2, 1, 0, 2, 2)),
                ("bbox", 0),
            }

        check_dataset_items(
            project_id=project_id,
            project_type=project_type,
            dm_dataset_definition=dataset_definition,
            annotation_scenes=annotation_scenes,
            all_labels=labels_to_keep,
            labels_to_keep=labels_to_keep,
            exact_same=True,
        )

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    def test_stage_duplicate_id_but_different_subset_name(
        self,
        request,
        fxt_import_data_repo,
        fxt_export_data_repo,
        fxt_bbox_polygon_dataset_definition,
        fxt_dataset_labels,
    ):
        dm_dataset = self._get_dm_dataset_from_definition(
            request,
            fxt_bbox_polygon_dataset_definition,
            label_names=[label["name"] for label in fxt_dataset_labels],
            subsets=["train", "val", "test"],
        )
        dataset_id = save_dataset(fxt_import_data_repo, dm_dataset, "voc")
        fxt_export_data_repo.zip_dataset(dataset_id)

        _, warnings = self._prepare_import_new_project_workflow(data_repo=fxt_import_data_repo, dataset_id=dataset_id)

        # Warning subset merging
        assert len(warnings) == 1, warnings

    def _test_import_dataset_for_cross_project(
        self,
        dataset_definition,
        project_type_from,
        project_type_to,
        import_data_repo,
        request,
        n_warnings=0,
    ):
        """
        Test importing geti-exported datumaro datasets into impt projects of different domains.
        """
        # prepare dataset
        dm_dataset_definition = request.getfixturevalue(dataset_definition)
        label_names, dm_dataset = self._create_geti_exported_dataset_from_definition(
            request, project_type_from, dm_dataset_definition
        )
        dataset_id = save_dataset(import_data_repo, dm_dataset, "datumaro")

        supported_project_types, warnings = self._prepare_import_new_project_workflow(
            data_repo=import_data_repo, dataset_id=dataset_id
        )

        candidate_projects = self._get_candidate_project_types(supported_project_types)
        assert project_type_to in candidate_projects, candidate_projects
        assert len(warnings) == n_warnings, warnings
        is_anomaly_reduced = FeatureFlagProvider.is_enabled(feature_flag=FeatureFlag.FEATURE_FLAG_ANOMALY_REDUCTION)
        if is_anomaly_reduced:
            # check names in pipeline (need "anomaly" instead of "anomaly_classification")
            for project_meta in supported_project_types:
                ptype = ImportUtils.rest_task_type_to_project_type(project_meta["project_type"])
                assert ptype not in [GetiProjectType.ANOMALY_DETECTION, GetiProjectType.ANOMALY_SEGMENTATION]
                if ptype == GetiProjectType.ANOMALY_CLASSIFICATION:
                    assert project_meta["project_type"] == "anomaly"
                    pipeline = project_meta["pipeline"]
                    assert pipeline["connections"][0]["to"] == "Anomaly"
                    anomaly_task = pipeline["tasks"][1]
                    assert anomaly_task["title"] == "Anomaly"
                    assert anomaly_task["task_type"] == "anomaly"
                    assert anomaly_task["labels"][0]["group"] == "Anomaly Task Labels"
                    assert anomaly_task["labels"][1]["group"] == "Anomaly Task Labels"

        # import dataset
        labels_to_keep = self._get_all_label_names_from_supported_project_types(
            supported_project_types, project_type_to
        )
        assert len(labels_to_keep) > 0

        project_id = self._create_project_from_dataset_workflow(
            request,
            data_repo=import_data_repo,
            dataset_id=dataset_id,
            project_name=f"_test_import_{project_type_to.name.lower()}_project",
            project_type=project_type_to,
            label_names=labels_to_keep,
        )

        label_schema = get_latest_label_schema_for_project(ID(project_id))
        if project_type_from != project_type_to:
            # check if group name is reset(need "<task type> Task Labels")
            trainalbe_task_types = ImportUtils.get_trainable_tasks_of_project_type(project_type=project_type_to)
            task_name = ImportUtils.task_type_to_rest_api_string(trainalbe_task_types[0]).replace("_", " ").title()
            label_groups = label_schema.get_groups()
            if project_type_from == GetiProjectType.DETECTION and project_type_to == GetiProjectType.CLASSIFICATION:
                # multi-label classification
                assert len(label_groups) == len(labels_to_keep)
                expected_groups = [f"{task_name} Task Labels for '{label}'" for label in labels_to_keep]
                actual_groups = [label_group.name for label_group in label_groups]
                assert sorted(actual_groups) == sorted(expected_groups)
            else:
                assert len(label_groups) == 1
                if project_type_to in ANOMALY_PROJECT_TYPES:
                    # default name is decided by project_builder, not dataset-ie
                    domain_name = "anomaly" if is_anomaly_reduced else trainalbe_task_types[0].name.lower()
                    assert label_groups[0].name == f"default - {domain_name}"
                else:
                    assert label_groups[0].name == f"{task_name} Task Labels"

        label_names_project = [label.name for label in label_schema.get_labels(include_empty=False)]
        assert sorted(label_names_project) == sorted(label_names)

        images, _, annotation_scenes = get_media_ann_scenes_from_project_id(project_id=project_id)
        check_thumbnails(ID(project_id), images)

        converted_dataset_definition = convert_dataset_definition_for_cross_project(
            dm_dataset_definition, project_type_from, project_type_to
        )

        check_dataset_items(
            project_id=project_id,
            project_type=project_type_to,
            dm_dataset_definition=converted_dataset_definition,
            annotation_scenes=annotation_scenes,
            all_labels=label_names,
            labels_to_keep=labels_to_keep,
        )

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @pytest.mark.priority_medium
    @pytest.mark.component
    @pytest.mark.parametrize(
        "dataset_definition,project_type_from,project_type_to",
        [
            [
                "fxt_bbox_dataset_definition",
                GetiProjectType.DETECTION,
                GetiProjectType.ROTATED_DETECTION,
            ],
            [
                "fxt_bbox_dataset_definition",
                GetiProjectType.DETECTION,
                GetiProjectType.CLASSIFICATION,
            ],
            [
                "fxt_polygon_dataset_definition",
                GetiProjectType.ROTATED_DETECTION,
                GetiProjectType.DETECTION,
            ],
            [
                "fxt_polygon_dataset_definition",
                GetiProjectType.SEGMENTATION,
                GetiProjectType.INSTANCE_SEGMENTATION,
            ],
            [
                "fxt_polygon_dataset_definition",
                GetiProjectType.INSTANCE_SEGMENTATION,
                GetiProjectType.SEGMENTATION,
            ],
            [
                "fxt_polygon_dataset_definition",
                GetiProjectType.SEGMENTATION,
                GetiProjectType.DETECTION,
            ],
            [
                "fxt_polygon_dataset_definition",
                GetiProjectType.INSTANCE_SEGMENTATION,
                GetiProjectType.DETECTION,
            ],
        ],
    )
    def test_import_dataset_for_cross_project(
        self,
        dataset_definition,
        project_type_from,
        project_type_to,
        fxt_import_data_repo,
        request,
    ):
        """
        Test importing geti-exported datumaro datasets into impt projects of different domains.
        This function test cross-project mappings among detection and segmentation tasks.
        """
        self._test_import_dataset_for_cross_project(
            dataset_definition=dataset_definition,
            project_type_from=project_type_from,
            project_type_to=project_type_to,
            import_data_repo=fxt_import_data_repo,
            request=request,
        )

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @pytest.mark.priority_medium
    @pytest.mark.component
    @pytest.mark.parametrize(
        "dataset_definition,project_type_from,project_type_to",
        [
            [
                "fxt_anomaly_classification_dataset_definition",
                GetiProjectType.ANOMALY_CLASSIFICATION,
                GetiProjectType.ANOMALY_CLASSIFICATION,
            ],
            [
                "fxt_anomaly_detection_dataset_definition",
                GetiProjectType.ANOMALY_DETECTION,
                GetiProjectType.ANOMALY_DETECTION,
            ],
            [
                "fxt_anomaly_segmentation_dataset_definition",
                GetiProjectType.ANOMALY_SEGMENTATION,
                GetiProjectType.ANOMALY_SEGMENTATION,
            ],
            [
                "fxt_anomaly_classification_dataset_definition",
                GetiProjectType.ANOMALY_CLASSIFICATION,
                GetiProjectType.CLASSIFICATION,
            ],
            [
                "fxt_anomaly_detection_dataset_definition",
                GetiProjectType.ANOMALY_DETECTION,
                GetiProjectType.CLASSIFICATION,
            ],
            [
                "fxt_anomaly_detection_dataset_definition",
                GetiProjectType.ANOMALY_DETECTION,
                GetiProjectType.ANOMALY_CLASSIFICATION,
            ],
            [
                "fxt_anomaly_segmentation_dataset_definition",
                GetiProjectType.ANOMALY_SEGMENTATION,
                GetiProjectType.CLASSIFICATION,
            ],
            [
                "fxt_anomaly_segmentation_dataset_definition",
                GetiProjectType.ANOMALY_SEGMENTATION,
                GetiProjectType.ANOMALY_CLASSIFICATION,
            ],
            [
                "fxt_anomaly_segmentation_dataset_definition",
                GetiProjectType.ANOMALY_SEGMENTATION,
                GetiProjectType.ANOMALY_DETECTION,
            ],
        ],
    )
    def test_import_dataset_for_anomaly(
        self,
        dataset_definition,
        project_type_from,
        project_type_to,
        fxt_import_data_repo,
        fxt_anomaly_reduction,
        request,
    ):
        """
        Test importing geti-exported anomaly datasets into impt projects of different domains.
        """
        anomaly_det_seg = [GetiProjectType.ANOMALY_DETECTION, GetiProjectType.ANOMALY_SEGMENTATION]
        if fxt_anomaly_reduction and project_type_to in anomaly_det_seg:
            pytest.skip(
                f"Mapping from '{project_type_from.name}' to '{project_type_to.name}' deosn't exist "
                "when FEATURE_FLAG_ANOMALY_REDUCTION is enabled."
            )
        self._test_import_dataset_for_cross_project(
            dataset_definition=dataset_definition,
            project_type_from=project_type_from,
            project_type_to=project_type_to,
            import_data_repo=fxt_import_data_repo,
            request=request,
            n_warnings=(1 if fxt_anomaly_reduction and project_type_from in anomaly_det_seg else 0),
        )

    @patch.object(
        JobMetadata,
        "from_env_vars",
        return_value=JobMetadata(ID("job_id"), "test_job", "Test jobs", ID("author"), datetime.datetime.now()),
    )
    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @pytest.mark.priority_medium
    @pytest.mark.component
    def test_import_with_no_model_templates(
        self,
        mock_from_env_vars,
        fxt_coco_dataset_id,
        fxt_import_data_repo,
    ):
        """
        Test getting a 500 error when creating a project by importing a dataset
        """
        self._prepare_import_new_project_workflow(data_repo=fxt_import_data_repo, dataset_id=fxt_coco_dataset_id)

        labels = [
            {"name": "car", "color": "#00ff00ff"},
            {"name": "person", "color": "#0000ffff"},
        ]
        with (
            pytest.raises(ModelTemplateError),
            patch.object(ModelTemplateList, "get_by_id", return_value=NullModelTemplate()),
        ):
            self._create_project_from_dataset_workflow(
                None,
                data_repo=fxt_import_data_repo,
                dataset_id=fxt_coco_dataset_id,
                project_name="imported project with error",
                project_type=GetiProjectType.DETECTION,
                label_names=[label["name"] for label in labels],
            )

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @pytest.mark.priority_medium
    @pytest.mark.component
    def test_warning_on_importing_single_label_detection_dataset_to_new_project(
        self,
        request,
        fxt_import_data_repo,
    ):
        """
        For the det->cls case, Users should be warned if the detection dataset contains only one label,
        as this would prevent the creation of a classification project.
        """

        label_names = ["object"]
        dataset_definition = {
            "item1": {("bbox", 0), ("bbox", 0)},
            "item2": {("bbox", 0)},
            "item3": {("bbox", 0)},
        }
        dm_infos = {"GetiProjectTask": ImportUtils.project_type_to_rest_api_string(GetiProjectType.DETECTION)}
        dm_dataset = self._get_dm_dataset_from_definition(
            request,
            dataset_definition,
            label_names=label_names,
            dm_infos=dm_infos,
        )
        dataset_id = save_dataset(fxt_import_data_repo, dm_dataset, "datumaro")
        supported_project_types, warnings = self._prepare_import_new_project_workflow(
            data_repo=fxt_import_data_repo, dataset_id=dataset_id
        )

        candidate_projects = self._get_candidate_project_types(supported_project_types)
        assert GetiProjectType.CLASSIFICATION not in candidate_projects
        found_warning = False
        for warning in warnings:
            if warning["name"] == "At least two labels are required to create a classification project":
                found_warning = True
                break
        assert found_warning

    @staticmethod
    def _save_dummy_dataset(
        file_repo: ImportDataRepo,
    ) -> ID:
        """
        Save a dummy dataset that can't be imported by Datumaro library

        :param file_repo: file repo used to save dataset to filesystem
        :return: ID of the saved dataset
        """
        dataset_id: ID = SessionBasedRepo.generate_id()

        dataset_dir = file_repo.get_dataset_directory(dataset_id)
        if not os.path.exists(dataset_dir):
            os.makedirs(dataset_dir)
        with open(os.path.join(dataset_dir, "dummy.txt"), "w") as f_dummy:
            f_dummy.write("dummy")
        return dataset_id

    def _import_two_labels_project_from_dataset(
        self, request, file_id: ID, project_type: GetiProjectType, data_repo: ImportDataRepo
    ) -> Project:
        """
        Import project with two labels ['car', 'person'] from a given dataset which includes these
        two labels

        :param request: request object
        :param import_manager: ImportManager object
        :param file_id: id of datumaro dataset uploaded to filesystem
        :param project_type: Geti project type
        :param data_repo: directory where to import project
        :return: imported project
        """
        project_repo = ProjectRepo()
        labels = [
            {"name": "car", "color": "#00ff00ff"},
            {"name": "person", "color": "#0000ffff"},
        ]

        self._prepare_import_new_project_workflow(data_repo=data_repo, dataset_id=file_id)
        project_id = self._create_project_from_dataset_workflow(
            request,
            data_repo=data_repo,
            dataset_id=file_id,
            project_name="_test_import_dataset",
            project_type=project_type,
            label_names=[label["name"] for label in labels],
        )

        assert project_id != ""
        project = project_repo.get_by_id(ID(project_id))

        return project

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @patch("job.repos.data_repo.ObjectStorageRepo")
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
    def test_import_dataset_chained_task(
        self,
        mocked_object_storage_repo_init,
        project_type,
        fxt_import_data_repo,
        fxt_export_data_repo,
        fxt_dm_dataset_str,
        request,
    ) -> None:
        """
        Import project anomaly projects from Datumaro datasets.
        :param domain: domain of created project
        :param fxt_dm_dataset_generator: Datumaro dataset generator
        :param fxt_dm_categories_generator: Datumaro label schema generator
        :param fxt_anomaly_dataset_labels: Labels for anomaly project
        :param request: request object
        """
        mocked_object_storage_repo_init.return_value = MagicMock()

        fxt_datumaro_dataset = request.getfixturevalue(fxt_dm_dataset_str)
        fmt = "datumaro"

        dataset_id = save_dataset(fxt_import_data_repo, fxt_datumaro_dataset, fmt)
        fxt_export_data_repo.zip_dataset(dataset_id)

        supported_project_types, _ = self._prepare_import_new_project_workflow(
            data_repo=fxt_import_data_repo, dataset_id=dataset_id
        )

        labels_to_keep = self._get_all_label_names_from_supported_project_types(supported_project_types, project_type)
        assert len(labels_to_keep) > 0

        project_id = self._create_project_from_dataset_workflow(
            request,
            data_repo=fxt_import_data_repo,
            dataset_id=dataset_id,
            project_name=f"_test_import_dataset_categories_{fmt}_{project_type.name.lower()}_project",
            project_type=project_type,
            label_names=labels_to_keep,
        )

        label_schema = get_latest_label_schema_for_project(ID(project_id))

        chained_task_type_with_labels = ImportUtils.parse_chained_task_labels_from_datumaro(
            fxt_datumaro_dataset.infos()
        )

        # exactly 2 task_types should be in chained task project.
        assert len(chained_task_type_with_labels) == 2

        label_names_dataset = set()
        for _, label_names in chained_task_type_with_labels:
            label_names_dataset.update(label_names)

        label_names_project = [label.name for label in label_schema.get_labels(include_empty=False)]

        assert sorted(label_names_project) == sorted(label_names_dataset)

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @pytest.mark.parametrize(
        "fxt_dm_dataset_id_str, project_type",
        [
            [
                "fxt_datumaro_dataset_chained_det_seg_id",
                GetiProjectType.DETECTION,
            ],
            [
                "fxt_datumaro_dataset_chained_det_seg_id",
                GetiProjectType.ROTATED_DETECTION,
            ],
            [
                "fxt_datumaro_dataset_chained_det_seg_id",
                GetiProjectType.SEGMENTATION,
            ],
            [
                "fxt_datumaro_dataset_chained_det_seg_id",
                GetiProjectType.INSTANCE_SEGMENTATION,
            ],
            [
                "fxt_datumaro_dataset_seg_id",
                GetiProjectType.CHAINED_DETECTION_SEGMENTATION,
            ],
            [
                "fxt_datumaro_dataset_ins_seg_id",
                GetiProjectType.CHAINED_DETECTION_SEGMENTATION,
            ],
        ],
    )
    def test_import_dataset_chained_for_cross_project(
        self,
        fxt_dm_dataset_id_str,
        project_type,
        fxt_import_data_repo,
        fxt_export_data_repo,
        request,
    ) -> None:
        """
        Is is possible to create a chained projects from chained datasets.
        :param fxt_dm_dataset_id_str: fixture string for dm dataset id
        :param project_type: Geti project type to be created
        :param request: request objec
        """
        dataset_id = request.getfixturevalue(fxt_dm_dataset_id_str)
        fxt_export_data_repo.zip_dataset(dataset_id)

        supported_project_types, _ = self._prepare_import_new_project_workflow(
            data_repo=fxt_import_data_repo, dataset_id=dataset_id
        )

        candidate_projects = self._get_candidate_project_types(supported_project_types)
        assert project_type in candidate_projects, (
            candidate_projects
        )  ## this is tested @ test_load_and_stage_dataset.py, too

        dataset_info = get_dataset_info(fxt_dm_dataset_id_str)
        expected_labels = dataset_info.label_names_by_cross_project[project_type]
        labels_to_keep = self._get_all_label_names_from_supported_project_types(supported_project_types, project_type)
        assert set(labels_to_keep) == expected_labels  ## this is tested @ test_load_and_stage_dataset.py, too

        project_id = self._create_project_from_dataset_workflow(
            request,
            data_repo=fxt_import_data_repo,
            dataset_id=dataset_id,
            project_name=f"_test_create_{project_type.name.lower()}_project_from_{fxt_dm_dataset_id_str}",
            project_type=project_type,
            label_names=labels_to_keep,
        )

        label_schema = get_latest_label_schema_for_project(project_id=project_id)
        labels = label_schema.get_labels(include_empty=False)
        label_names_project = {label.name for label in labels}

        assert label_names_project == expected_labels

        if project_type == GetiProjectType.CHAINED_DETECTION_SEGMENTATION:
            project_repo = ProjectRepo()
            project = project_repo.get_by_id(ID(project_id))
            dataset_storage = project.get_training_dataset_storage()
            ann_scenes = list(AnnotationSceneRepo(dataset_storage.identifier).get_all())

            find_default_detection_bbox = False
            detection_label_id = next(label.id_ for label in labels if label.name == "detection label")
            for ann_scene in ann_scenes:
                for annotation in ann_scene.annotations:
                    if detection_label_id in annotation.get_label_ids():
                        find_default_detection_bbox = True
                        break
            assert find_default_detection_bbox

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @pytest.mark.parametrize(
        "fxt_project_str",
        [
            "fxt_annotated_detection_project",
            "fxt_annotated_rotated_detection_project",
            "fxt_annotated_segmentation_project",
            "fxt_annotated_instance_segmentation_project",
        ],
    )
    def test_import_chained_dataset_to_project_for_cross_project(
        self,
        fxt_datumaro_dataset_chained_det_seg,
        fxt_project_str,
        fxt_import_data_repo,
        fxt_export_data_repo,
        request,
    ) -> None:
        """
        Is is possible to create a chained projects from chained datasets.
        :param fxt_project_str: fixture string for Geti project which already exists
        :param request: request objec
        """
        # prepare project
        project = request.getfixturevalue(fxt_project_str)
        request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project.workspace_id))
        project_type = ImportUtils.get_project_type(project)

        # prepare dataset
        dm_dataset = fxt_datumaro_dataset_chained_det_seg
        dataset_id = save_dataset(fxt_import_data_repo, dm_dataset, "datumaro")
        fxt_export_data_repo.zip_dataset(dataset_id)

        dataset_info = get_dataset_info("fxt_datumaro_dataset_chained_det_seg_id")
        expected_labels = dataset_info.label_names_by_cross_project[project_type]
        label_names, _ = self._prepare_import_existing_project_workflow(
            data_repo=fxt_import_data_repo, dataset_id=dataset_id, project=project
        )
        assert set(label_names) == expected_labels, (
            project_type,
            label_names,
        )  # also tested @ test_load_and_stage_dataset.py

        # Generate labels_map that maps from datumaro label_name to project Label
        labels_map = get_label_maps(project=project, dm_label_names=label_names)

        dataset_storage = project.get_training_dataset_storage()
        old_images, _, old_ann_scenes = get_media_ann_scenes_from_project_id(
            project_id=project.id_,
            dataset_id=dataset_storage.id_,
        )

        self._import_dataset_to_project_workflow(
            data_repo=fxt_import_data_repo,
            dataset_id=dataset_id,
            project=project,
            labels_map=labels_map,
            dataset_name=f"test import chained_det_seg dataset to '{project_type.name.lower()}' projet",
        )

        new_images, _, new_ann_scenes = get_media_ann_scenes_from_project_id(
            project_id=project.id_,
            dataset_id=dataset_storage.id_,
        )

        num_dataset_items = len(dm_dataset)
        num_annotations = 0
        for item in dm_dataset:
            if item.annotations or item.attributes.get("has_empty_label", False):
                num_annotations += 1

        assert len(new_images) == len(old_images) + num_dataset_items
        assert len(new_ann_scenes) == len(old_ann_scenes) + num_annotations

        ann_scenes_from_dataset: list[AnnotationScene] = []
        for ann_scene in new_ann_scenes:
            if ann_scene not in old_ann_scenes:
                ann_scenes_from_dataset.append(ann_scene)

        label_cat: dm.LabelCategories = dm_dataset.categories()[dm.AnnotationType.label]
        task_labels = ImportUtils.parse_chained_task_labels_from_datumaro(dm_dataset.infos())
        task_type_to_labels = {}
        for task_type, labels in task_labels:
            task_type_to_labels[task_type] = labels

        dm_label_names = list(labels_map.keys())
        dm_dataset_definition: DatasetDefinition = {}
        for item in dm_dataset:
            annotations: AnnotationDefinition = []
            for ann in item.annotations:
                label_name = label_cat.items[ann.label]
                if label_name in task_type_to_labels[TaskType.SEGMENTATION]:  # accept segmentation labels only
                    label_index = dm_label_names.index(label_name)
                    name = ann.type.name
                    assert isinstance(name, str)
                    annotations.append((name, label_index))
            if item.annotations or item.attributes.get("has_empty_label", False):
                dm_dataset_definition[item.id] = annotations

        self._check_mapped_annotations(
            ann_scenes_from_dataset,
            dm_dataset_definition,
            dm_label_names,
            GetiProjectType.CHAINED_DETECTION_SEGMENTATION,
            project_type,
            labels_map,
        )

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @pytest.mark.parametrize(
        "fxt_dm_dataset_str, project_type",
        [
            [
                "fxt_datumaro_dataset_multi_label",
                GetiProjectType.CLASSIFICATION,
            ],
            [
                "fxt_datumaro_dataset_hierarchical",
                GetiProjectType.HIERARCHICAL_CLASSIFICATION,
            ],
        ],
    )
    def test_import_dataset_include_all_labels(
        self,
        fxt_import_data_repo,
        fxt_export_data_repo,
        fxt_dm_dataset_str,
        project_type,
        request,
    ):
        """
        Check if all labels are loaded from the Datumaro dataset label schema
        Eventhough an label isn't be used to annotate any items, all labels should be included

        :param fxt_dm_dataset_str: Datumaro dataset fixture string that will be loaded by request
        :param project_type: Geti project type
        :param request: request objec
        """
        fxt_datumaro_dataset = request.getfixturevalue(fxt_dm_dataset_str)
        fmt = "datumaro"

        # delete all annotations of items
        for dm_item in fxt_datumaro_dataset:
            dm_item.annotations = []

        dataset_id = save_dataset(fxt_import_data_repo, fxt_datumaro_dataset, fmt)
        fxt_export_data_repo.zip_dataset(dataset_id)

        supported_project_types, _ = self._prepare_import_new_project_workflow(
            data_repo=fxt_import_data_repo, dataset_id=dataset_id
        )

        # collect all label_names of the target project_type
        label_names = self._get_all_label_names_from_supported_project_types(supported_project_types, project_type)

        # label_names should be taken from the dm_dataset label structure
        label_cat = fxt_datumaro_dataset.categories()[dm.AnnotationType.label]
        assert sorted([dm_label_item.name for dm_label_item in label_cat.items]) == sorted(label_names)

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @pytest.mark.priority_medium
    @pytest.mark.component
    def test_import_multiple_annotation_cls(
        self,
        fxt_dataset_labels,
        fxt_multi_label_dataset_definition,
        fxt_import_data_repo,
        fxt_export_data_repo,
        request,
    ):
        """
        Check if all labels are loaded from the Datumaro dataset label schema
        Eventhough an label isn't be used to annotate any items, all labels should be included

        :param fxt_dm_dataset_str: Datumaro dataset fixture string that will be loaded by request
        :param fxt_temp_directory: temporal directory for testing that will be deleted after the test
        :param request: request objec
        """
        label_names = [label["name"] for label in fxt_dataset_labels]
        dm_dataset = self._get_dm_dataset_from_definition(
            request,
            fxt_multi_label_dataset_definition,
            label_names,
        )
        dataset_id = save_dataset(fxt_import_data_repo, dm_dataset, "datumaro")
        fxt_export_data_repo.zip_dataset(dataset_id)
        project_type = GetiProjectType.CLASSIFICATION

        # prepare dataset
        supported_project_types, warnings = self._prepare_import_new_project_workflow(
            data_repo=fxt_import_data_repo, dataset_id=dataset_id
        )

        has_multi_label_ann_error = False
        for error in warnings:
            if error["type"] == "error" and error["name"] == "Multi label annotation error":
                has_multi_label_ann_error = True
                break
        assert has_multi_label_ann_error

        # import dataset
        labels_to_keep = self._get_all_label_names_from_supported_project_types(supported_project_types, project_type)
        assert len(labels_to_keep) > 0  # MayFix: actually it should be 2 ['cat', 'dog'] from item2&3,
        # but 4['cat', 'truck', 'dog', 'bus'],
        # because 'get_project_metas_with_labels' is run before validation,
        # which performs 'remove_annotations' transform to remove item1.
        # def fxt_multi_label_dataset_definition():
        #     return {
        #         "item1": {("label", 1), ("label", 3)}, --> removed by transform
        #         "item2": {("label", 0)},               --> keep
        #         "item3": {("label", 2)},               --> keep
        #     }

        project_id = self._create_project_from_dataset_workflow(
            request,
            data_repo=fxt_import_data_repo,
            dataset_id=dataset_id,
            project_name=f"_test_import_{project_type.name.lower()}_project",
            project_type=project_type,
            label_names=labels_to_keep,
        )

        # remove multi-annotation
        target_definition = {}
        for key, anns in fxt_multi_label_dataset_definition.items():
            if len(anns) < 2:
                target_definition[key] = anns
            else:
                target_definition[key] = set()  # empty set

        _, _, annotation_scenes = get_media_ann_scenes_from_project_id(project_id=project_id)
        check_dataset_items(
            project_id=project_id,
            project_type=project_type,
            dm_dataset_definition=target_definition,
            annotation_scenes=annotation_scenes,
            all_labels=label_names,
            labels_to_keep=labels_to_keep,
        )

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @pytest.mark.priority_medium
    @pytest.mark.component
    @pytest.mark.parametrize(
        "fxt_project_str,fxt_dm_dataset_str,project_type,n_warnings",
        [
            [
                "fxt_annotated_classification_project",
                "fxt_datumaro_dataset",
                GetiProjectType.CLASSIFICATION,
                0,
            ],
            [
                "fxt_annotated_hierarchical_classification_project",
                "fxt_datumaro_dataset_hierarchical",
                GetiProjectType.CLASSIFICATION,
                0,
            ],
            [
                "fxt_annotated_hierarchical_classification_with_multi_label_project",
                "fxt_datumaro_dataset_hierarchical",
                GetiProjectType.CLASSIFICATION,
                0,
            ],
            [
                "fxt_annotated_detection_project",
                "fxt_datumaro_dataset_detection",
                GetiProjectType.DETECTION,
                1,
            ],
            [
                "fxt_annotated_rotated_detection_project",
                "fxt_datumaro_dataset_rotated_detection",
                GetiProjectType.ROTATED_DETECTION,
                0,
            ],
            [
                "fxt_annotated_segmentation_project",
                "fxt_datumaro_dataset_segmentation",
                GetiProjectType.SEGMENTATION,
                1,
            ],
            [
                "fxt_annotated_segmentation_project",
                "fxt_voc_dataset_segmentation",
                GetiProjectType.SEGMENTATION,
                1,
            ],
        ],
    )
    def test_import_dataset_to_project(
        self,
        fxt_import_data_repo,
        fxt_export_data_repo,
        fxt_project_str,
        fxt_dm_dataset_str,
        project_type,
        n_warnings,
        request,
    ):
        """
        Test import a dataset to existing project

        :param fxt_enable_feature_flag_name: control feature flags in the test
        :param fxt_project_str: fixture of project where a dataset to be imported
        :param fxt_dm_dataset_str: Datumaro dataset fixture string that will be loaded by request
        :param project_type: Geti project type
        :param request: request objec
        """

        fxt_datumaro_dataset = request.getfixturevalue(fxt_dm_dataset_str)

        project = request.getfixturevalue(fxt_project_str)
        request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project.id_))

        fmt = "datumaro"

        dataset_id = save_dataset(fxt_import_data_repo, fxt_datumaro_dataset, fmt)
        fxt_export_data_repo.zip_dataset(dataset_id)

        trainalbe_task_types = ImportUtils.get_trainable_tasks_of_project_type(project_type=project_type)
        # Current version of Geti doesn't support the feature that importing a dataset to existing project
        assert len(trainalbe_task_types) == 1

        label_names, warnings = self._prepare_import_existing_project_workflow(
            data_repo=fxt_import_data_repo, dataset_id=dataset_id, project=project
        )
        assert len(label_names) > 0
        assert len(warnings) == n_warnings

        # Generate labels_map that maps from datumaro label_name to project Label
        labels_map = get_label_maps(project=project, dm_label_names=label_names)

        dataset_storage = project.get_training_dataset_storage()
        old_images, _, old_ann_scenes = get_media_ann_scenes_from_project_id(
            project_id=project.id_,
            dataset_id=dataset_storage.id_,
        )

        dataset_name = f"test dataset name for {project_type.name.lower()} project"
        self._import_dataset_to_project_workflow(
            data_repo=fxt_import_data_repo,
            dataset_id=dataset_id,
            project=project,
            labels_map=labels_map,
            dataset_name=dataset_name,
        )

        new_images, _, new_ann_scenes = get_media_ann_scenes_from_project_id(
            project_id=project.id_,
            dataset_id=dataset_storage.id_,
        )

        num_dataset_items = len(fxt_datumaro_dataset)
        num_annotations = 0
        for item in fxt_datumaro_dataset:
            if item.annotations or item.attributes.get("has_empty_label", False):
                num_annotations += 1

        assert len(new_images) == len(old_images) + num_dataset_items
        assert len(new_ann_scenes) == len(old_ann_scenes) + num_annotations

    @patch.object(
        JobMetadata,
        "from_env_vars",
        return_value=JobMetadata(ID("job_id"), "test_job", "Test jobs", ID("author"), datetime.datetime.now()),
    )
    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @pytest.mark.priority_medium
    @pytest.mark.component
    @pytest.mark.parametrize(
        "bad_dataset_test_type,expected_exception",
        [
            [BAD_DATASET_FILE_TEST.BAD_FILE_ID, InvalidIDException],
            [BAD_DATASET_FILE_TEST.DUMMY_DATASET, DatasetFormatException],
            [BAD_DATASET_FILE_TEST.UNSUPPORTED_DATASET, DatasetFormatException],
        ],
    )
    def test_prepare_import_existing_project_with_bad_dataset_file(
        self,
        mock_from_env_vars,
        fxt_import_data_repo,
        fxt_export_data_repo,
        fxt_datumaro_dataset,
        fxt_annotated_classification_project,
        bad_dataset_test_type,
        expected_exception,
        request,
    ):
        """
        Test whether the proper Excetpion raise or not when wrong file_id / storage are passed

        :param fxt_enable_feature_flag_name: control feature flags in the test
        :param fxt_annotated_classification_project: fixture of project where a dataset to be imported
        :param bad_dataset_test_type: BAD_DATASET_FILE_TEST variable to identify the test type
        :param expected_exception: an exception expected to raise when importing a dataset to an existing project
        :param request: request object
        """

        project = fxt_annotated_classification_project
        request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project.id_))

        if bad_dataset_test_type == BAD_DATASET_FILE_TEST.DUMMY_DATASET:
            dataset_id = self._save_dummy_dataset(fxt_import_data_repo)
            fxt_export_data_repo.zip_dataset(dataset_id)
        elif bad_dataset_test_type == BAD_DATASET_FILE_TEST.UNSUPPORTED_DATASET:
            dataset_id = save_dataset(
                fxt_import_data_repo,
                fxt_datumaro_dataset,
                "mnist",
            )
            fxt_export_data_repo.zip_dataset(dataset_id)
        elif bad_dataset_test_type == BAD_DATASET_FILE_TEST.BAD_FILE_ID:
            dataset_id = ID("aaaabbbbccccdddd")

        with pytest.raises(expected_exception):
            self._prepare_import_existing_project_workflow(
                data_repo=fxt_import_data_repo, dataset_id=dataset_id, project=project
            )

    @patch.object(
        JobMetadata,
        "from_env_vars",
        return_value=JobMetadata(ID("job_id"), "test_job", "Test jobs", ID("author"), datetime.datetime.now()),
    )
    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @pytest.mark.priority_medium
    @pytest.mark.component
    @pytest.mark.parametrize(
        "test_type, expected_exception",
        [
            (IMPORT_EXISTING_ERROR_TEST.INVALID_FILE_ID, InvalidIDException),
            (IMPORT_EXISTING_ERROR_TEST.NON_EXISTING_FILE, FileNotFoundException),
            (IMPORT_EXISTING_ERROR_TEST.INVALID_PROJECT_ID, InvalidIDException),
            (IMPORT_EXISTING_ERROR_TEST.NON_EXISTING_PROJECT, ProjectNotFoundException),
            (IMPORT_EXISTING_ERROR_TEST.WRONG_LABEL_NAME, InvalidLabelException),
            (IMPORT_EXISTING_ERROR_TEST.WRONG_LABEl_ID, InvalidLabelException),
        ],
    )
    def test_import_dataset_to_project_with_error(
        self,
        mock_from_env_vars,
        test_type,
        expected_exception,
        fxt_import_data_repo,
        fxt_export_data_repo,
        fxt_annotated_detection_project,
        fxt_datumaro_dataset_detection,
        fxt_mongo_id,
        request,
    ):
        # prepare project & dataset first
        project: Project = fxt_annotated_detection_project
        request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project.id_))

        dataset_id = save_dataset(fxt_import_data_repo, fxt_datumaro_dataset_detection, "datumaro")
        fxt_export_data_repo.zip_dataset(dataset_id)

        label_names, _ = self._prepare_import_existing_project_workflow(
            data_repo=fxt_import_data_repo, dataset_id=dataset_id, project=project
        )

        # Generate labels_map that maps from datumaro label_name to project Label
        labels_map = get_label_maps(project=project, dm_label_names=label_names)
        dm_label_names = list(labels_map.keys())  # dataset labels
        sc_labels = list(set(labels_map.values()))  # project labels
        WRONG_ID = ID("aaaabbbbccccdddd")
        VALID_BUT_NON_EXIST_ID = fxt_mongo_id(2000)

        if test_type == IMPORT_EXISTING_ERROR_TEST.INVALID_FILE_ID:
            dataset_id = WRONG_ID
        elif test_type == IMPORT_EXISTING_ERROR_TEST.NON_EXISTING_FILE:
            dataset_id = VALID_BUT_NON_EXIST_ID
        elif test_type == IMPORT_EXISTING_ERROR_TEST.INVALID_PROJECT_ID:
            project.id_ = WRONG_ID
        elif test_type == IMPORT_EXISTING_ERROR_TEST.NON_EXISTING_PROJECT:
            project.id_ = VALID_BUT_NON_EXIST_ID
        elif test_type == IMPORT_EXISTING_ERROR_TEST.WRONG_LABEL_NAME:
            labels_map["dummy_label_name"] = sc_labels[0]
        elif test_type == IMPORT_EXISTING_ERROR_TEST.WRONG_LABEl_ID:
            labels_map[dm_label_names[0]].id_ = WRONG_ID

        with pytest.raises(expected_exception):
            self._import_dataset_to_project_workflow(
                data_repo=fxt_import_data_repo,
                dataset_id=dataset_id,
                project=project,
                labels_map=labels_map,
                dataset_name="test dataset",
            )

    def _test_import_dataset_to_project_for_cross_project(
        self,
        project_str,
        dataset_definition,
        project_type_from,
        project_type_to,
        import_data_repo,
        request,
        n_warnings=0,
        map_empty_label=False,
        is_multi_label_dataset=False,
    ):
        """
        Test import a dataset to existing project for the cross-project mapping case.

        :param project_str: fixture name of project where a dataset to be imported
        :param dataset_definition: dataset definition
        :param project_type_from: Exported Geti project type
        :param project_type_to: Geti project type to import
        :param request: request object
        """
        project = request.getfixturevalue(project_str)
        request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project.id_))

        trainalbe_task_types = ImportUtils.get_trainable_tasks_of_project_type(project_type=project_type_to)
        # Current version of Geti doesn't support the feature that importing a dataset to existing project
        assert len(trainalbe_task_types) == 1
        assert project_type_to == ImportUtils.get_project_type(project)

        # prepare dataset
        if isinstance(dataset_definition, str):
            dm_dataset_definition = request.getfixturevalue(dataset_definition)
        else:
            dm_dataset_definition = dataset_definition

        dm_label_names, dm_dataset = self._create_geti_exported_dataset_from_definition(
            request, project_type_from, dm_dataset_definition, is_multi_label=is_multi_label_dataset
        )
        dataset_id = save_dataset(import_data_repo, dm_dataset, "datumaro")

        label_names, warnings = self._prepare_import_existing_project_workflow(
            data_repo=import_data_repo, dataset_id=dataset_id, project=project
        )

        assert len(label_names) > 0
        assert len(warnings) == n_warnings, warnings

        # Generate labels_map that maps from datumaro label_name to project Label
        labels_map = get_label_maps(project=project, dm_label_names=label_names, map_empty_label=map_empty_label)

        dataset_storage = project.get_training_dataset_storage()
        old_images, _, old_ann_scenes = get_media_ann_scenes_from_project_id(
            project_id=project.id_,
            dataset_id=dataset_storage.id_,
        )

        dataset_name = f"test dataset name for {project_type_to.name.lower()} project"
        self._import_dataset_to_project_workflow(
            data_repo=import_data_repo,
            dataset_id=dataset_id,
            project=project,
            labels_map=labels_map,
            dataset_name=dataset_name,
        )

        new_images, _, new_ann_scenes = get_media_ann_scenes_from_project_id(
            project_id=project.id_,
            dataset_id=dataset_storage.id_,
        )

        num_dataset_items = len(dm_dataset)
        num_annotations = 0
        for item in dm_dataset:
            if item.annotations or item.attributes.get("has_empty_label", False):
                num_annotations += 1

        assert len(new_images) == len(old_images) + num_dataset_items
        assert len(new_ann_scenes) == len(old_ann_scenes) + num_annotations

        ann_scenes_from_dataset: list[AnnotationScene] = []
        for ann_scene in new_ann_scenes:
            if ann_scene not in old_ann_scenes:
                ann_scenes_from_dataset.append(ann_scene)

        self._check_mapped_annotations(
            ann_scenes_from_dataset,
            dm_dataset_definition,
            dm_label_names,
            project_type_from,
            project_type_to,
            labels_map,
        )

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @pytest.mark.priority_medium
    @pytest.mark.component
    @pytest.mark.parametrize(
        "fxt_project_str,dataset_definition,project_type_from,project_type_to",
        [
            [
                "fxt_annotated_rotated_detection_project",
                "fxt_bbox_dataset_definition",
                GetiProjectType.DETECTION,
                GetiProjectType.ROTATED_DETECTION,
            ],
            [
                "fxt_annotated_multi_label_project",
                "fxt_bbox_dataset_definition",
                GetiProjectType.DETECTION,
                GetiProjectType.CLASSIFICATION,
            ],
            [
                "fxt_annotated_detection_project",
                "fxt_polygon_dataset_definition",
                GetiProjectType.ROTATED_DETECTION,
                GetiProjectType.DETECTION,
            ],
            [
                "fxt_annotated_instance_segmentation_project",
                "fxt_polygon_dataset_definition",
                GetiProjectType.SEGMENTATION,
                GetiProjectType.INSTANCE_SEGMENTATION,
            ],
            [
                "fxt_annotated_segmentation_project",
                "fxt_polygon_dataset_definition",
                GetiProjectType.INSTANCE_SEGMENTATION,
                GetiProjectType.SEGMENTATION,
            ],
            [
                "fxt_annotated_detection_project",
                "fxt_polygon_dataset_definition",
                GetiProjectType.SEGMENTATION,
                GetiProjectType.DETECTION,
            ],
            [
                "fxt_annotated_detection_project",
                "fxt_polygon_dataset_definition",
                GetiProjectType.INSTANCE_SEGMENTATION,
                GetiProjectType.DETECTION,
            ],
        ],
    )
    def test_import_dataset_to_project_for_cross_project(
        self,
        fxt_project_str,
        dataset_definition,
        project_type_from,
        project_type_to,
        fxt_import_data_repo,
        request,
    ):
        """
        Test import a dataset to existing project for the cross-project mapping case.
        This function tests cross-project mapping among cls., det., and seg. projects.
        """
        self._test_import_dataset_to_project_for_cross_project(
            project_str=fxt_project_str,
            dataset_definition=dataset_definition,
            project_type_from=project_type_from,
            project_type_to=project_type_to,
            import_data_repo=fxt_import_data_repo,
            request=request,
        )

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @pytest.mark.priority_medium
    @pytest.mark.component
    @pytest.mark.parametrize(
        "fxt_project_str,dataset_definition,project_type_from,project_type_to",
        [
            [
                "fxt_annotated_multi_label_project",
                "fxt_multi_label_dataset_definition",
                GetiProjectType.CLASSIFICATION,
                GetiProjectType.CLASSIFICATION,
            ],
            [
                "fxt_annotated_detection_project",
                "fxt_bbox_dataset_definition",
                GetiProjectType.DETECTION,
                GetiProjectType.DETECTION,
            ],
            [
                "fxt_annotated_rotated_detection_project",
                "fxt_polygon_dataset_definition",
                GetiProjectType.ROTATED_DETECTION,
                GetiProjectType.ROTATED_DETECTION,
            ],
            [
                "fxt_annotated_segmentation_project",
                "fxt_polygon_dataset_definition",
                GetiProjectType.SEGMENTATION,
                GetiProjectType.SEGMENTATION,
            ],
            [
                "fxt_annotated_instance_segmentation_project",
                "fxt_polygon_dataset_definition",
                GetiProjectType.INSTANCE_SEGMENTATION,
                GetiProjectType.INSTANCE_SEGMENTATION,
            ],
            [
                "fxt_annotated_rotated_detection_project",
                "fxt_bbox_dataset_definition",
                GetiProjectType.DETECTION,
                GetiProjectType.ROTATED_DETECTION,
            ],
            [
                "fxt_annotated_multi_label_project",
                "fxt_bbox_dataset_definition",
                GetiProjectType.DETECTION,
                GetiProjectType.CLASSIFICATION,
            ],
            [
                "fxt_annotated_detection_project",
                "fxt_polygon_dataset_definition",
                GetiProjectType.ROTATED_DETECTION,
                GetiProjectType.DETECTION,
            ],
            [
                "fxt_annotated_instance_segmentation_project",
                "fxt_polygon_dataset_definition",
                GetiProjectType.SEGMENTATION,
                GetiProjectType.INSTANCE_SEGMENTATION,
            ],
            [
                "fxt_annotated_segmentation_project",
                "fxt_polygon_dataset_definition",
                GetiProjectType.INSTANCE_SEGMENTATION,
                GetiProjectType.SEGMENTATION,
            ],
            [
                "fxt_annotated_detection_project",
                "fxt_polygon_dataset_definition",
                GetiProjectType.SEGMENTATION,
                GetiProjectType.DETECTION,
            ],
            [
                "fxt_annotated_detection_project",
                "fxt_polygon_dataset_definition",
                GetiProjectType.INSTANCE_SEGMENTATION,
                GetiProjectType.DETECTION,
            ],
        ],
    )
    def test_import_dataset_to_project_with_mapping_to_empty_label(
        self,
        fxt_project_str,
        dataset_definition,
        project_type_from,
        project_type_to,
        fxt_import_data_repo,
        request,
    ):
        """
        Test import a dataset to existing project for the cross-project mapping case.
        This function tests cross-project mapping among cls., det., and seg. projects.
        """
        is_multi_label_dataset = False
        if dataset_definition == "fxt_multi_label_dataset_definition":
            ann_type = "label"
            is_multi_label_dataset = True
        elif dataset_definition == "fxt_bbox_dataset_definition":
            ann_type = "bbox"
        else:
            ann_type = "polygon"
        dataset_definition = {
            "item0": {(ann_type, 0)},
            "item1": {(ann_type, 1)},
            "item2": {(ann_type, 2)},
            "item3": {(ann_type, 3)},
            "item4": {(ann_type, 0), (ann_type, 1)},
            "item5": {(ann_type, 2), (ann_type, 3)},
        }
        self._test_import_dataset_to_project_for_cross_project(
            project_str=fxt_project_str,
            dataset_definition=dataset_definition,
            project_type_from=project_type_from,
            project_type_to=project_type_to,
            import_data_repo=fxt_import_data_repo,
            request=request,
            map_empty_label=True,
            is_multi_label_dataset=is_multi_label_dataset,
        )

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @pytest.mark.priority_medium
    @pytest.mark.component
    @pytest.mark.parametrize(
        "fxt_project_str,dataset_definition,project_type_from,project_type_to",
        [
            [
                "fxt_annotated_anomaly_cls_project",
                "fxt_anomaly_classification_dataset_definition",
                GetiProjectType.ANOMALY_CLASSIFICATION,
                GetiProjectType.ANOMALY_CLASSIFICATION,
            ],
            [
                "fxt_annotated_anomaly_det_project",
                "fxt_anomaly_detection_dataset_definition",
                GetiProjectType.ANOMALY_DETECTION,
                GetiProjectType.ANOMALY_DETECTION,
            ],
            [
                "fxt_annotated_anomaly_seg_project",
                "fxt_anomaly_segmentation_dataset_definition",
                GetiProjectType.ANOMALY_SEGMENTATION,
                GetiProjectType.ANOMALY_SEGMENTATION,
            ],
            [
                "fxt_annotated_classification_project",
                "fxt_anomaly_classification_dataset_definition",
                GetiProjectType.ANOMALY_CLASSIFICATION,
                GetiProjectType.CLASSIFICATION,
            ],
            [
                "fxt_annotated_classification_project",
                "fxt_anomaly_detection_dataset_definition",
                GetiProjectType.ANOMALY_DETECTION,
                GetiProjectType.CLASSIFICATION,
            ],
            [
                "fxt_annotated_anomaly_cls_project",
                "fxt_anomaly_detection_dataset_definition",
                GetiProjectType.ANOMALY_DETECTION,
                GetiProjectType.ANOMALY_CLASSIFICATION,
            ],
            [
                "fxt_annotated_classification_project",
                "fxt_anomaly_segmentation_dataset_definition",
                GetiProjectType.ANOMALY_SEGMENTATION,
                GetiProjectType.CLASSIFICATION,
            ],
            [
                "fxt_annotated_anomaly_cls_project",
                "fxt_anomaly_segmentation_dataset_definition",
                GetiProjectType.ANOMALY_SEGMENTATION,
                GetiProjectType.ANOMALY_CLASSIFICATION,
            ],
            [
                "fxt_annotated_anomaly_det_project",
                "fxt_anomaly_segmentation_dataset_definition",
                GetiProjectType.ANOMALY_SEGMENTATION,
                GetiProjectType.ANOMALY_DETECTION,
            ],
        ],
    )
    def test_import_dataset_to_project_for_anomaly(
        self,
        fxt_project_str,
        dataset_definition,
        project_type_from,
        project_type_to,
        fxt_import_data_repo,
        fxt_anomaly_reduction,
        request,
    ):
        """
        Test import a dataset to existing project for the cross-project mapping case.
        This function tests cross-project mapping among anomaly projects.
        """
        if (
            fxt_anomaly_reduction
            and project_type_from in [GetiProjectType.ANOMALY_DETECTION, GetiProjectType.ANOMALY_SEGMENTATION]
            and project_type_to == GetiProjectType.ANOMALY_CLASSIFICATION
        ):
            n_warnings = 1
        else:
            n_warnings = 0

        self._test_import_dataset_to_project_for_cross_project(
            project_str=fxt_project_str,
            dataset_definition=dataset_definition,
            project_type_from=project_type_from,
            project_type_to=project_type_to,
            import_data_repo=fxt_import_data_repo,
            request=request,
            n_warnings=n_warnings,
        )

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    def test_import_dataset_with_warnings(
        self,
        request,
        fxt_broken_coco_dataset_id,
        fxt_import_data_repo,
    ):
        """
        Test dataset import through endpoints
            - prepare dataset through endpoint
            - assert preparation gives expected result
            - create project through endpoint
            - assert project is created successfully
        """
        supported_project_types, warnings = self._prepare_import_new_project_workflow(
            data_repo=fxt_import_data_repo, dataset_id=fxt_broken_coco_dataset_id
        )

        candidate_projects = self._get_candidate_project_types(supported_project_types)
        expected_project_type = GetiProjectType.DETECTION
        assert candidate_projects == [expected_project_type]
        label_names = self._get_all_label_names_from_supported_project_types(
            supported_project_types, expected_project_type
        )
        assert set(label_names) == {"car", "person"}
        assert warnings == [
            {
                "type": "error",
                "name": "Annotation parsing error",
                "description": "Could not parse annotation in uploaded dataset",
                "resolve_strategy": "Skip annotation",
                "affected_images": 1,
            }
        ]

        project_id = self._create_project_from_dataset_workflow(
            request,
            data_repo=fxt_import_data_repo,
            dataset_id=fxt_broken_coco_dataset_id,
            project_name="_test_import_detection_project",
            project_type=expected_project_type,
            label_names=label_names,
        )

        project_repo = ProjectRepo()
        project = project_repo.get_by_id(ID(project_id))
        assert not isinstance(project, NullProject)
        project_repo.delete_by_id(project.id_)

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @patch("job.repos.data_repo.ObjectStorageRepo")
    @pytest.mark.parametrize(
        ("video_dataset_path", "project_type"),
        [
            ("fxt_datumaro_video_dataset_path", GetiProjectType.DETECTION),
            ("fxt_datumaro_video_dataset_with_ranges_path", GetiProjectType.CLASSIFICATION),
        ],
    )
    def test_import_video_dataset(
        self,
        mocked_object_storage_repo_init,
        fxt_import_data_repo,
        fxt_temp_directory,
        video_dataset_path,
        project_type,
        request,
    ) -> None:
        """
        Test if Dataset I/E could create a project from a video dataset.
        """
        mocked_object_storage_repo_init.return_value = MagicMock()

        video_dataset_path_value = request.getfixturevalue(video_dataset_path)
        fxt_datumaro_dataset_path = download_file(
            URL_DATASETS + video_dataset_path_value, Path(fxt_temp_directory) / video_dataset_path_value
        )
        dataset_id = save_dataset_with_path(fxt_import_data_repo, str(fxt_datumaro_dataset_path))
        fmt = "datumaro"

        # get dataset definition
        dataset_dir = fxt_import_data_repo.get_dataset_directory(id_=dataset_id)
        dm_dataset, _ = ImportUtils.parse_dataset(path=dataset_dir, fmt=fmt)
        label_names = [o.name for o in dm_dataset.categories()[dm.AnnotationType.label]]
        dataset_definition = get_dm_dataset_definition(dm_dataset=dm_dataset, label_names=label_names)

        supported_project_types, _ = self._prepare_import_new_project_workflow(
            data_repo=fxt_import_data_repo, dataset_id=dataset_id
        )

        labels_to_keep = self._get_all_label_names_from_supported_project_types(supported_project_types, project_type)
        assert len(labels_to_keep) > 0

        project_id = self._create_project_from_dataset_workflow(
            request,
            data_repo=fxt_import_data_repo,
            dataset_id=dataset_id,
            project_name="_test_project",
            project_type=project_type,
            label_names=labels_to_keep,
        )

        images, videos, annotation_scenes = get_media_ann_scenes_from_project_id(project_id=project_id)
        check_thumbnails(ID(project_id), images, videos)
        assert not images
        assert len(videos) == 4

        check_dataset_items(
            project_id=project_id,
            project_type=project_type,
            dm_dataset_definition=dataset_definition,
            annotation_scenes=annotation_scenes,
            all_labels=label_names,
            labels_to_keep=labels_to_keep,
        )

        dataset_storage = ProjectRepo().get_by_id(project_id).get_training_dataset_storage()
        check_video_annotation_ranges(dm_dataset=dm_dataset, dataset_storage=dataset_storage, label_names=label_names)

        # import a dataset again (import to exising project)
        request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project_id))
        project = ProjectRepo().get_by_id(project_id)

        dataset_id = save_dataset_with_path(fxt_import_data_repo, str(fxt_datumaro_dataset_path))
        new_label_names, _ = self._prepare_import_existing_project_workflow(
            data_repo=fxt_import_data_repo, dataset_id=dataset_id, project=project
        )
        assert len(new_label_names) == len(label_names)
        sc_labels = get_project_labels(project=project, include_empty=False)
        labels_map: dict[str, Label] = {sc_label.name: sc_label for sc_label in sc_labels}

        self._import_dataset_to_project_workflow(
            data_repo=fxt_import_data_repo,
            dataset_id=dataset_id,
            project=project,
            labels_map=labels_map,
            dataset_name="",
        )

        new_images, new_videos, new_annotation_scenes = get_media_ann_scenes_from_project_id(project_id=project_id)
        check_thumbnails(ID(project_id), new_images, new_videos)
        assert not new_images
        assert len(new_videos) == 8

        new_dataset_definition = {}
        for key, val in dataset_definition.items():
            new_dataset_definition[key] = val
            new_dataset_definition[key + ".copy"] = val
        check_dataset_items(
            project_id=project_id,
            project_type=project_type,
            dm_dataset_definition=new_dataset_definition,
            annotation_scenes=new_annotation_scenes,
            all_labels=label_names,
            labels_to_keep=labels_to_keep,
        )

        new_dataset = []
        for dm_item in dm_dataset:
            if isinstance(dm_item.media, dm.Video) and not ImportUtils.is_video_unannotated(dm_item):
                new_dataset.append(dm_item)
                # dm_item.id is from ScExtractorFromDatasetStorage._convert_video_annotation_range(/...)
                splits = str(dm_item.id).split("_range_")
                fn, ext = os.path.splitext(dm_item.media.path)
                new_video_path = fn + "__1" + ext
                new_dataset.append(
                    dm_item.wrap(
                        id=f"{splits[0]}__1_range_{splits[1]}",
                        media=dm.Video(
                            new_video_path, start_frame=dm_item.media._start_frame, end_frame=dm_item.media._end_frame
                        ),
                    )
                )

        check_video_annotation_ranges(
            dm_dataset=dm.Dataset.from_iterable(
                new_dataset,
                infos=dm_dataset.infos(),
                categories=dm_dataset.categories(),
                media_type=dm_dataset.media_type(),
            ),
            dataset_storage=dataset_storage,
            label_names=label_names,
        )

    @patch("jobs_common.tasks.utils.secrets.set_env_vars", new=return_none)
    @patch("jobs_common.tasks.utils.secrets.setup_session_from_env", new=return_none)
    @patch("job.repos.data_repo.ObjectStorageRepo")
    def test_import_video_dataset_and_create_video_annotation_range(
        self,
        mocked_object_storage_repo_init,
        fxt_import_data_repo,
        fxt_datumaro_video_dataset_shape_classification_path,
        fxt_temp_directory,
        request,
    ) -> None:
        """
        Test if Dataset I/E could create a project from a video dataset and create video annotation range.
        """
        mocked_object_storage_repo_init.return_value = MagicMock()

        project_type = GetiProjectType.CLASSIFICATION
        fxt_datumaro_dataset_path = download_file(
            URL_DATASETS + fxt_datumaro_video_dataset_shape_classification_path,
            Path(fxt_temp_directory) / fxt_datumaro_video_dataset_shape_classification_path,
        )
        dataset_id = save_dataset_with_path(fxt_import_data_repo, str(fxt_datumaro_dataset_path))
        fmt = "datumaro"

        # get dataset definition
        dataset_dir = fxt_import_data_repo.get_dataset_directory(id_=dataset_id)
        dm_dataset, _ = ImportUtils.parse_dataset(path=dataset_dir, fmt=fmt)
        label_names = [o.name for o in dm_dataset.categories()[dm.AnnotationType.label]]
        dataset_definition = get_dm_dataset_definition(dm_dataset=dm_dataset, label_names=label_names)

        supported_project_types, _ = self._prepare_import_new_project_workflow(
            data_repo=fxt_import_data_repo, dataset_id=dataset_id
        )

        assert len(supported_project_types) == 1
        assert supported_project_types[0]["project_type"] == "classification"
        labels_to_keep = self._get_all_label_names_from_supported_project_types(supported_project_types, project_type)
        assert set(labels_to_keep) == {"triangle", "rectangle", "circle"}

        project_id = self._create_project_from_dataset_workflow(
            request,
            data_repo=fxt_import_data_repo,
            dataset_id=dataset_id,
            project_name="test_project",
            project_type=project_type,
            label_names=labels_to_keep,
        )

        images, videos, annotation_scenes = get_media_ann_scenes_from_project_id(project_id=project_id)
        assert len(images) == 0
        assert len(videos) == 1
        assert len(annotation_scenes) == 11

        check_dataset_items(
            project_id=project_id,
            project_type=project_type,
            dm_dataset_definition=dataset_definition,
            annotation_scenes=annotation_scenes,
            all_labels=label_names,
            labels_to_keep=labels_to_keep,
        )

        dataset_storage = ProjectRepo().get_by_id(project_id).get_training_dataset_storage()
        check_video_annotation_ranges(
            dm_dataset=dm_dataset, dataset_storage=dataset_storage, label_names=label_names, restored=False
        )

        # import a dataset again (import to exising project)
        request.addfinalizer(lambda: DeletionHelpers.delete_project_by_id(project_id=project_id))
        project = ProjectRepo().get_by_id(project_id)

        # dataset is deleted when the previous import process is done.
        # we need to save(==upload) this dataset again.
        dataset_id = save_dataset_with_path(fxt_import_data_repo, str(fxt_datumaro_dataset_path))
        new_label_names, _ = self._prepare_import_existing_project_workflow(
            data_repo=fxt_import_data_repo, dataset_id=dataset_id, project=project
        )
        assert len(new_label_names) == len(label_names)
        sc_labels = get_project_labels(project=project, include_empty=False)
        labels_map: dict[str, Label] = {sc_label.name: sc_label for sc_label in sc_labels}

        self._import_dataset_to_project_workflow(
            data_repo=fxt_import_data_repo,
            dataset_id=dataset_id,
            project=project,
            labels_map=labels_map,
            dataset_name="",
        )

        new_images, new_videos, new_annotation_scenes = get_media_ann_scenes_from_project_id(project_id=project_id)
        check_thumbnails(ID(project_id), new_images, new_videos)

        new_dataset_definition = {}
        for key, val in dataset_definition.items():
            new_dataset_definition[key] = val
            new_dataset_definition[key + ".copy"] = val
        check_dataset_items(
            project_id=project_id,
            project_type=project_type,
            dm_dataset_definition=new_dataset_definition,
            annotation_scenes=new_annotation_scenes,
            all_labels=label_names,
            labels_to_keep=labels_to_keep,
        )

        new_dataset = []
        for dm_item in dm_dataset:
            if isinstance(dm_item.media, dm.VideoFrame):
                new_dataset.append(dm_item)
                # dm_item.id is from ScExtractorFromDatasetStorage._convert_video_annotation_range(/...)
                fn, ext = os.path.splitext(dm_item.media.path)
                new_video_path = fn + "__1" + ext
                new_dataset.append(
                    dm_item.wrap(
                        id=f"{new_video_path}-frame_{dm_item.media.index}",
                        media=dm.VideoFrame(dm.Video(new_video_path), dm_item.media.index),
                    )
                )
        check_video_annotation_ranges(
            dm_dataset=dm.Dataset.from_iterable(
                new_dataset,
                infos=dm_dataset.infos(),
                categories=dm_dataset.categories(),
                media_type=dm_dataset.media_type(),
            ),
            dataset_storage=dataset_storage,
            label_names=label_names,
            restored=False,
        )

    @staticmethod
    def _get_sc_dataset_definition_as_sorted_list(
        annotation_scenes: list[AnnotationScene],
        label_ids: list[ID],
        include_empty: bool = False,
    ) -> dict[str, list[tuple[str, int]]]:
        """
        Convert list of SC annotation scenes to a dataset definition of the SC dataset.
        For examples of dataset definitions, see dataset definition fixtures.
        Note that dataset definition in this function is different to dataset definition fixtures.
        This function defines annotations as a sorted list, not a set.

        :param annotation_scenes: list of the annotation scenes
        :param label_ids: list of label IDs in the SC dataset
        :param include_empty: Whether to include empty labels or not
        :return: dataset definition as a sorted list representing SC annotation scenes
        """

        sc_dataset_definition = {}
        for ann_scene in annotation_scenes:
            dataset_item_definition = []
            for annotation in ann_scene.annotations:
                shape = annotation.shape
                ann_label_ids = [label.id_ for label in annotation.get_labels(include_empty=include_empty)]
                for label in ann_label_ids:
                    label_idx = label_ids.index(label)
                    if isinstance(shape, Rectangle) and Rectangle.is_full_box(shape):
                        dataset_item_definition.append(("label", label_idx))
                    elif isinstance(shape, Rectangle):
                        dataset_item_definition.append(("bbox", label_idx))
                    elif isinstance(shape, Polygon):
                        dataset_item_definition.append(("polygon", label_idx))
                    elif isinstance(shape, Ellipse):
                        dataset_item_definition.append(("ellipse", label_idx))
            sc_dataset_definition[str(ann_scene.id_)] = sorted(dataset_item_definition)
        return sc_dataset_definition

    def _check_mapped_annotations(
        self,
        annotation_scenes: list[AnnotationScene],
        dm_dataset_definition: DatasetDefinition,
        dm_label_names: list[str],
        project_type_from: GetiProjectType,
        project_type_to: GetiProjectType,
        labels_map: dict[str, Label],
    ):
        """
        Compare annotation items in sc project and dm_dataset for cross-project case.

        :param annotation_scenes: annotation scenes from dm_dataset.
        :param dm_dataset_definition: Datumaro dataset definition keeping item information with annotation
        :param dm_label_names: label names in dm_dataset_definition
        :param project_type_from: project type of dm_dataset (original project type)
        :param project_type_to: project type of sc project. (target project type)
        :param labels_map: labels mapping between dm_dataset and sc project. keys should be selected labels.
        """
        selected_labels = list(labels_map.keys())
        sc_labels = list(set(labels_map.values()))
        empty_indice = []
        for label_name, sc_label in labels_map.items():
            if sc_label.is_empty:
                empty_indice.append(dm_label_names.index(label_name))

        # get dataset definition from the project
        sc_label_ids = [label.id_ for label in sc_labels]
        sc_definition = self._get_sc_dataset_definition_as_sorted_list(
            annotation_scenes, sc_label_ids, include_empty=len(empty_indice) > 0
        )
        sc_items = list(sc_definition.values())

        # get dataset definition from dataset (need label mapping)
        converted_dataset_definition = convert_dataset_definition_for_cross_project(
            dm_dataset_definition, project_type_from, project_type_to
        )
        # filter dm items to remove labels not kept when loading
        domain_to_valid_types = {
            domain: [ann_type.name for ann_type in ann_types]
            for domain, ann_types in SUPPORTED_DOMAIN_TO_ANNOTATION_TYPES.items()
        }
        labels_to_keep_indices = [dm_label_names.index(label_name) for label_name in selected_labels]
        label_domain = ImportUtils.project_type_to_label_domain(project_type_to)

        dm_items = []
        for definition in list(converted_dataset_definition.values()):
            valid_anns = set()
            empty_anns = set()
            for ann_type, label in definition:
                assert isinstance(label, int)
                if label in empty_indice:
                    empty_anns.add((ann_type, label))
                elif label in labels_to_keep_indices and ann_type in domain_to_valid_types[label_domain]:
                    valid_anns.add((ann_type, label))
            if empty_anns and not valid_anns:
                valid_anns = {("label", empty_indice[0])}  # empty label
            dm_items.append(valid_anns)

        # assert all SC item definitions are identical to a DM datumaro definition
        assert len(sc_items) == len(dm_items)
        for dm_item in dm_items:
            # label mapping
            anns = []
            for ann in dm_item:
                dm_label_name = dm_label_names[ann[1]]
                sc_label_id = labels_map[dm_label_name].id_
                sc_label_index = sc_label_ids.index(sc_label_id)
                anns.append((ann[0], sc_label_index))
            anns = sorted(anns)
            assert anns in sc_items

    @staticmethod
    def _get_candidate_project_types(supported_project_types):
        return [
            ImportUtils.rest_task_type_to_project_type(project_meta["project_type"])
            for project_meta in supported_project_types
        ]


def get_latest_labels_for_project(project_id: ID, include_empty: bool = False) -> list[Label]:
    """
    Get the labels from the latest label schema of the given project.

    :param project_id: ID of the project from which to get the labels
    :param include_empty: bool indicating whether the empty labels should be included in the result
    :raises: LabelSchemaNotFoundException if no schema view is found in the repo for the project
    :return: List of Label objects
    """
    latest_schema = get_latest_label_schema_for_project(project_id=project_id)
    return latest_schema.get_labels(include_empty=include_empty)  # type: ignore[return-value]


def get_latest_label_schema_for_project(project_id: ID) -> LabelSchema:
    """
    Get the latest LabelSchema for a given project.

    The schema is loaded from the repo.

    :param project_id: ID of the project linked with the label schema to retrieve
    :raises: LabelSchemaNotFoundException if no schema is found in the repo for the project
    :return: LabelSchema object
    """
    workspace_id = CTX_SESSION_VAR.get().workspace_id
    project_identifier = ProjectIdentifier(workspace_id=workspace_id, project_id=project_id)
    label_schema_repo: LabelSchemaRepo = LabelSchemaRepo(project_identifier)
    latest_schema = label_schema_repo.get_latest()
    if isinstance(latest_schema, NullLabelSchema):
        raise ValueError("Label Schema not found")
    return latest_schema

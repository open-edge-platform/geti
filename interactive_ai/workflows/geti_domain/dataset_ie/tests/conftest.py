# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module defines the test configuration
"""

import os
import pathlib
import shutil
import tempfile
import zipfile
from typing import IO
from unittest.mock import MagicMock, patch

import requests

# ruff: noqa: E402
# Note: the session needs to be .set() before the repos .get()
from geti_types import CTX_SESSION_VAR, make_session
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

CTX_SESSION_VAR.set(make_session())

import datumaro as dm
import iai_core.configuration.helper as otx_config_helper
import pytest
from _pytest.fixtures import FixtureRequest
from geti_types import ID
from iai_core.algorithms import ModelTemplateList
from iai_core.configuration.elements.default_model_parameters import DefaultModelParameters
from iai_core.entities.label import Domain
from iai_core.entities.model_template import (
    DatasetRequirements,
    HyperParameterData,
    InstantiationType,
    ModelTemplate,
    TaskFamily,
    TaskType,
)
from jobs_common.features.feature_flag_provider import FeatureFlag
from jobs_common_extras.datumaro_conversion.definitions import GetiProjectType

from job.repos.data_repo import ExportDataRepo, ImportDataRepo
from tests.features.test_feature_flag_provider import TestFeatureFlagProvider

DEFAULT_MODEL_TEMPLATES = {
    str(TaskType.DATASET).lower(): "dataset",
    str(TaskType.CROP).lower(): "crop",
    str(TaskType.CLASSIFICATION).lower(): "Custom_Image_Classification_EfficinetNet-B0",
    str(TaskType.DETECTION).lower(): "Custom_Object_Detection_Gen3_ATSS",
    str(TaskType.SEGMENTATION).lower(): "Custom_Semantic_Segmentation_Lite-HRNet-18-mod2_OCR",
    str(TaskType.ANOMALY_CLASSIFICATION).lower(): "ote_anomaly_classification_padim",
    str(TaskType.ANOMALY_DETECTION).lower(): "ote_anomaly_detection_padim",
    str(TaskType.ANOMALY_SEGMENTATION).lower(): "ote_anomaly_segmentation_padim",
    str(TaskType.ROTATED_DETECTION).lower(): "Custom_Rotated_Detection_via_Instance_Segmentation_MaskRCNN_ResNet50",
    str(TaskType.INSTANCE_SEGMENTATION).lower(): "Custom_Counting_Instance_Segmentation_MaskRCNN_ResNet50",
}


def detect_fixtures(module_name: str) -> list:
    """
    Searches for fixtures at given path provided in python module notation,
    starting on current working directory.
    :param module_name: name of module where fixtures folder is located
    :return: list of string representing fixture modules/plugins
    """
    fixtures: set = set()
    fixtures_path = pathlib.Path(os.path.dirname(__file__)) / "fixtures"
    for fixture_path in fixtures_path.iterdir():
        if not fixture_path.stem.endswith("__"):
            fixtures.add(".".join([module_name, "fixtures", fixture_path.stem]))
    return list(fixtures)


pytest_plugins = detect_fixtures("tests")


@pytest.fixture(scope="package")
def fxt_temp_file(request: FixtureRequest):
    """
    This fixture creates a temporary file and writes data to it
    """

    def _temp_file_factory(data: bytes) -> IO:
        file = tempfile.TemporaryFile()
        file.write(data)
        file.seek(0)
        request.addfinalizer(lambda: file.close())
        return file

    yield _temp_file_factory


@pytest.fixture
def fxt_temp_directory(request: FixtureRequest):
    """
    This fixture creates temporary directory
    """

    dir_path = tempfile.mkdtemp()
    request.addfinalizer(lambda: shutil.rmtree(dir_path))
    yield dir_path


@pytest.fixture
def fxt_coco_dataset_dir(
    fxt_dm_dataset_generator,
    fxt_bbox_polygon_dataset_definition,
    fxt_temp_directory,
    fxt_dataset_labels,
):
    path = os.path.join(fxt_temp_directory, "dataset")
    label_names = [label["name"] for label in fxt_dataset_labels]
    dataset = fxt_dm_dataset_generator(label_names, fxt_bbox_polygon_dataset_definition)
    dataset.export(path, "coco", save_media=True)
    return path


@pytest.fixture
def fxt_dataset_id(fxt_temp_directory, fxt_zipped_coco_dataset_path, fxt_import_data_repo):
    id_ = ID("000000000000000000000001")
    with open(fxt_zipped_coco_dataset_path, "rb") as file:
        data = file.read()
    fxt_import_data_repo._save_file(id_, data)
    fxt_import_data_repo.unzip_dataset(id_)
    return id_


@pytest.fixture
def fxt_test_dataset_id_generator(fxt_temp_directory, fxt_import_data_repo):
    def _test_dataset_id_generator(dataset_zip_path: str):
        id_ = ID("000000000000000000000001")
        path = download_file(
            URL_DATASETS + dataset_zip_path,
            pathlib.Path(fxt_temp_directory) / dataset_zip_path,
        )
        with open(path, "rb") as file:
            data = file.read()
        fxt_import_data_repo._save_file(id_, data)
        fxt_import_data_repo.unzip_dataset(id_)
        return id_

    return _test_dataset_id_generator


@pytest.fixture
def fxt_zipped_coco_dataset_path(fxt_coco_dataset_dir):
    path = shutil.make_archive(fxt_coco_dataset_dir, "zip", fxt_coco_dataset_dir)
    return path


@pytest.fixture
@patch("job.repos.data_repo.ObjectStorageRepo")
def fxt_import_data_repo(mocked_object_storage_repo_init, fxt_temp_directory):
    mocked_object_storage_repo_init.return_value = MagicMock()
    return ImportDataRepo(root_path=fxt_temp_directory)


@pytest.fixture
@patch("job.repos.data_repo.ObjectStorageRepo")
def fxt_export_data_repo(mocked_object_storage_repo_init, fxt_temp_directory):
    mocked_object_storage_repo_init.return_value = MagicMock()
    return ExportDataRepo(root_path=fxt_temp_directory)


URL_IAI_UNITTESTS = "http://s3.toolbox.iotg.sclab.intel.com/test/data/iai-unittests/"
URL_DATASETS = URL_IAI_UNITTESTS + "datasets/"


def download_file(url: str, file_path: pathlib.Path) -> pathlib.Path:
    response = requests.get(url=url)
    with open(file_path, "wb") as f:
        f.write(response.content)
    return file_path


@pytest.fixture
def fxt_test_dataset_generator(fxt_temp_directory):
    def _test_dataset_generator(dataset_zip_path: str, format: str):
        path = download_file(
            URL_DATASETS + dataset_zip_path,
            pathlib.Path(fxt_temp_directory) / dataset_zip_path,
        )
        with zipfile.ZipFile(path, "r") as zip_ref:
            zip_ref.extractall(fxt_temp_directory)
        return dm.Dataset.import_from(fxt_temp_directory, format=format)

    return _test_dataset_generator


@pytest.fixture
def fxt_datumaro_dataset_detection_path() -> str:
    return "datumaro_mini_det.zip"


@pytest.fixture
def fxt_datumaro_dataset_segmentation_path() -> str:
    # TODO: Geti can export bbox, polygon, ellipses for segmentation task.
    #      However, this dataset has only polygons. We need to enrich annotation types.
    return "datumaro_mini_seg.zip"


@pytest.fixture
def fxt_datumaro_dataset_instance_segmentation_path() -> str:
    # TODO: Geti can export bbox, polygon, ellipses for segmentation task.
    #      However, this dataset has only polygons. We need to enrich annotation types.
    return "datumaro_mini_ins_seg.zip"


@pytest.fixture
def fxt_voc_dataset_segmentation_path() -> str:
    return "voc_mini_seg.zip"


@pytest.fixture
def fxt_datumaro_dataset_chained_det_cls_path() -> str:
    return "datumaro_mini_chained_det_cls.zip"


@pytest.fixture
def fxt_datumaro_dataset_chained_det_seg_path() -> str:
    return "datumaro_mini_chained_det_seg.zip"


@pytest.fixture
def fxt_coco_dataset_id(fxt_test_dataset_id_generator):
    return fxt_test_dataset_id_generator("coco_mini.zip")


@pytest.fixture
def fxt_coco_dataset_multi_subsets_id(fxt_test_dataset_id_generator):
    return fxt_test_dataset_id_generator("coco_multi_subset.zip")


@pytest.fixture
def fxt_voc_dataset_id(fxt_test_dataset_id_generator):
    return fxt_test_dataset_id_generator("voc_mini.zip")


@pytest.fixture
def fxt_roboflow_coco_dataset_id(fxt_test_dataset_id_generator):
    return fxt_test_dataset_id_generator("roboflow_coco_mini.zip")


@pytest.fixture
def fxt_roboflow_voc_dataset_id(fxt_test_dataset_id_generator):
    return fxt_test_dataset_id_generator("roboflow_voc_mini.zip")


@pytest.fixture
def fxt_roboflow_yolo_dataset_id(fxt_test_dataset_id_generator):
    return fxt_test_dataset_id_generator("roboflow_yolov8_mini.zip")


@pytest.fixture
def fxt_datumaro_dataset_id(fxt_test_dataset_id_generator):
    return fxt_test_dataset_id_generator("datumaro_mini.zip")


@pytest.fixture
def fxt_datumaro_dataset_det_id(fxt_test_dataset_id_generator, fxt_datumaro_dataset_detection_path):
    return fxt_test_dataset_id_generator(fxt_datumaro_dataset_detection_path)


@pytest.fixture
def fxt_datumaro_dataset_seg_id(fxt_test_dataset_id_generator, fxt_datumaro_dataset_segmentation_path):
    # dataset for instance segmentation and segmentation.
    # TODO: enrich seg. dataset to also include bbox, elipse annotations.
    return fxt_test_dataset_id_generator(fxt_datumaro_dataset_segmentation_path)


@pytest.fixture
def fxt_datumaro_dataset_ins_seg_id(fxt_test_dataset_id_generator, fxt_datumaro_dataset_instance_segmentation_path):
    # dataset for instance segmentation and segmentation.
    # TODO: enrich seg. dataset to also include bbox, elipse annotations.
    return fxt_test_dataset_id_generator(fxt_datumaro_dataset_instance_segmentation_path)


@pytest.fixture
def fxt_datumaro_dataset_single_cls_id(fxt_test_dataset_id_generator):
    return fxt_test_dataset_id_generator("datumaro_mini_single_cls.zip")


@pytest.fixture
def fxt_datumaro_dataset_hierarchical_id(fxt_test_dataset_id_generator):
    return fxt_test_dataset_id_generator("datumaro_mini_hierarchical.zip")


@pytest.fixture
def fxt_datumaro_dataset_multi_label_id(fxt_test_dataset_id_generator):
    return fxt_test_dataset_id_generator("datumaro_mini_multi_label_cls.zip")


@pytest.fixture
def fxt_datumaro_dataset_rotated_detection_id(fxt_test_dataset_id_generator):
    return fxt_test_dataset_id_generator("datumaro_mini_rotated_detection.zip")


@pytest.fixture
def fxt_datumaro_dataset_anomaly_cls_id(fxt_test_dataset_id_generator):
    return fxt_test_dataset_id_generator("datumaro_mini_anomaly_cls.zip")


@pytest.fixture
def fxt_datumaro_dataset_anomaly_det_id(fxt_test_dataset_id_generator):
    return fxt_test_dataset_id_generator("datumaro_mini_anomaly_det.zip")


@pytest.fixture
def fxt_datumaro_dataset_anomaly_seg_id(fxt_test_dataset_id_generator):
    return fxt_test_dataset_id_generator("datumaro_mini_anomaly_seg.zip")


@pytest.fixture
def fxt_datumaro_dataset_chained_det_cls_id(fxt_test_dataset_id_generator, fxt_datumaro_dataset_chained_det_cls_path):
    return fxt_test_dataset_id_generator(fxt_datumaro_dataset_chained_det_cls_path)


@pytest.fixture
def fxt_datumaro_dataset_chained_det_seg_id(fxt_test_dataset_id_generator, fxt_datumaro_dataset_chained_det_seg_path):
    return fxt_test_dataset_id_generator(fxt_datumaro_dataset_chained_det_seg_path)


@pytest.fixture
def fxt_datumaro_dataset_no_labels_id(fxt_test_dataset_id_generator):
    return fxt_test_dataset_id_generator("datumaro_no_label_dataset.zip")


@pytest.fixture
def fxt_dataumaro_dataset_keypoint_id(fxt_test_dataset_id_generator):
    return fxt_test_dataset_id_generator("datumaro_mini_keypoint_detection.zip")


@pytest.fixture
def fxt_datumaro_dataset(fxt_test_dataset_generator) -> dm.Dataset:
    return fxt_test_dataset_generator("datumaro_mini.zip", "datumaro")


@pytest.fixture
def fxt_datumaro_dataset_hierarchical(fxt_test_dataset_generator) -> dm.Dataset:
    return fxt_test_dataset_generator("datumaro_mini_hierarchical.zip", "datumaro")


@pytest.fixture
def fxt_datumaro_dataset_detection(fxt_test_dataset_generator, fxt_datumaro_dataset_detection_path) -> dm.Dataset:
    return fxt_test_dataset_generator(fxt_datumaro_dataset_detection_path, "datumaro")


@pytest.fixture
def fxt_datumaro_dataset_segmentation(fxt_test_dataset_generator, fxt_datumaro_dataset_segmentation_path) -> dm.Dataset:
    return fxt_test_dataset_generator(fxt_datumaro_dataset_segmentation_path, "datumaro")


@pytest.fixture
def fxt_datumaro_dataset_instances_segmentation(
    fxt_test_dataset_generator, fxt_datumaro_dataset_instance_segmentation_path
) -> dm.Dataset:
    return fxt_test_dataset_generator(fxt_datumaro_dataset_instance_segmentation_path, "datumaro")


@pytest.fixture
def fxt_voc_dataset_segmentation(fxt_test_dataset_generator, fxt_voc_dataset_segmentation_path) -> dm.Dataset:
    return fxt_test_dataset_generator(fxt_voc_dataset_segmentation_path, "voc")


@pytest.fixture
def fxt_datumaro_dataset_rotated_detection(fxt_test_dataset_generator) -> dm.Dataset:
    return fxt_test_dataset_generator("datumaro_mini_rotated_detection.zip", "datumaro")


@pytest.fixture
def fxt_datumaro_dataset_multi_label(fxt_test_dataset_generator) -> dm.Dataset:
    return fxt_test_dataset_generator("datumaro_mini_multi_label_cls.zip", "datumaro")


@pytest.fixture
def fxt_datumaro_dataset_anomaly_cls(fxt_test_dataset_generator) -> dm.Dataset:
    return fxt_test_dataset_generator("datumaro_mini_anomaly_cls.zip", "datumaro")


@pytest.fixture
def fxt_datumaro_dataset_anomaly_det(fxt_test_dataset_generator) -> dm.Dataset:
    return fxt_test_dataset_generator("datumaro_mini_anomaly_det.zip", "datumaro")


@pytest.fixture
def fxt_datumaro_dataset_anomaly_seg(fxt_test_dataset_generator) -> dm.Dataset:
    return fxt_test_dataset_generator("datumaro_mini_anomaly_seg.zip", "datumaro")


@pytest.fixture
def fxt_datumaro_dataset_chained_det_cls(
    fxt_test_dataset_generator, fxt_datumaro_dataset_chained_det_cls_path
) -> dm.Dataset:
    return fxt_test_dataset_generator(fxt_datumaro_dataset_chained_det_cls_path, "datumaro")


@pytest.fixture
def fxt_datumaro_dataset_chained_det_seg(
    fxt_test_dataset_generator, fxt_datumaro_dataset_chained_det_seg_path
) -> dm.Dataset:
    return fxt_test_dataset_generator(fxt_datumaro_dataset_chained_det_seg_path, "datumaro")


@pytest.fixture
def fxt_datumaro_video_dataset_path() -> str:
    return "dice_detection_video_with_subset_dir.zip"


@pytest.fixture
def fxt_datumaro_video_dataset_with_ranges_path() -> str:
    return "dice_classification_with_video_annotation_ranges.zip"


@pytest.fixture
def fxt_datumaro_video_dataset_shape_classification_path() -> str:
    return "shape_classification.zip"


@pytest.fixture
def fxt_broken_coco_dataset_id(fxt_test_dataset_id_generator):
    return fxt_test_dataset_id_generator("coco_mini_broken.zip")


@pytest.fixture(scope="class", autouse=True)
def fxt_register_dataset_ie_model_templates(request: FixtureRequest):
    """
    This fixture provides dummy model templates (including hyper parameters) for
    default templates for import
    """
    domain_to_task_type = {
        Domain.CLASSIFICATION: TaskType.CLASSIFICATION,
        Domain.DETECTION: TaskType.DETECTION,
        Domain.SEGMENTATION: TaskType.SEGMENTATION,
        Domain.ROTATED_DETECTION: TaskType.ROTATED_DETECTION,
        Domain.ANOMALY_CLASSIFICATION: TaskType.ANOMALY_CLASSIFICATION,
        Domain.ANOMALY_DETECTION: TaskType.ANOMALY_DETECTION,
        Domain.ANOMALY_SEGMENTATION: TaskType.ANOMALY_SEGMENTATION,
    }

    model_template_list = ModelTemplateList()
    hyper_parameters = HyperParameterData(base_path="")
    hyper_parameters.manually_set_data_and_validate(otx_config_helper.convert(DefaultModelParameters(), target=dict))
    for domain in [
        Domain.CLASSIFICATION,
        Domain.DETECTION,
        Domain.SEGMENTATION,
        Domain.ROTATED_DETECTION,
        Domain.ANOMALY_CLASSIFICATION,
        Domain.ANOMALY_DETECTION,
        Domain.ANOMALY_SEGMENTATION,
    ]:
        model_template_id = DEFAULT_MODEL_TEMPLATES[domain.name.lower()]
        task_type = domain_to_task_type[domain]
        dataset_requirements = DatasetRequirements()
        model_template = ModelTemplate(
            model_template_id=model_template_id,
            model_template_path="",
            name=f"dummy_{model_template_id}",
            task_type=task_type,
            task_family=TaskFamily.VISION,
            instantiation=InstantiationType.NONE,
            hyper_parameters=hyper_parameters,
            dataset_requirements=dataset_requirements,
        )
        model_template_list.register_model_template(model_template)
        request.addfinalizer(lambda: model_template_list.unregister_model_template(model_template_id))


@pytest.fixture
def fxt_expected_pipeline_by_project_parser():
    """
    expected parsed pipeline results by project_parser for each fxt_datumaro_dataset_* and project_type

    :return: dictionary to map [string of fxt_datumaro_dataset_*][GetiProjectType] to expected pipeline result
    """

    return {
        "fxt_datumaro_dataset": {
            GetiProjectType.CLASSIFICATION: {
                "connections": [{"from": "Dataset", "to": "Classification"}],
                "tasks": [
                    {"title": "Dataset", "task_type": "dataset", "labels": []},
                    {
                        "title": "Classification",
                        "task_type": "classification",
                        "labels": [
                            {"name": "person", "group": "Classification Task Labels"},
                            {"name": "car", "group": "Classification Task Labels"},
                            {"name": "bicycle", "group": "Classification Task Labels"},
                        ],
                    },
                ],
            },
            GetiProjectType.DETECTION: {
                "connections": [{"from": "Dataset", "to": "Detection"}],
                "tasks": [
                    {"title": "Dataset", "task_type": "dataset", "labels": []},
                    {
                        "title": "Detection",
                        "task_type": "detection",
                        "labels": [
                            {"name": "person", "group": "Detection Task Labels"},
                            {"name": "car", "group": "Detection Task Labels"},
                            {"name": "bicycle", "group": "Detection Task Labels"},
                        ],
                    },
                ],
            },
        },
        "fxt_datumaro_dataset_segmentation": {
            GetiProjectType.SEGMENTATION: {
                "connections": [{"from": "Dataset", "to": "Segmentation"}],
                "tasks": [
                    {"title": "Dataset", "task_type": "dataset", "labels": []},
                    {
                        "title": "Segmentation",
                        "task_type": "segmentation",
                        "labels": [
                            {
                                "name": "label0",
                                "group": "Segmentation Task Labels",
                            },
                            {
                                "name": "label1",
                                "group": "Segmentation Task Labels",
                            },
                        ],
                    },
                ],
            },
        },
        "fxt_datumaro_dataset_instances_segmentation": {
            GetiProjectType.INSTANCE_SEGMENTATION: {
                "connections": [{"from": "Dataset", "to": "Instance Segmentation"}],
                "tasks": [
                    {"title": "Dataset", "task_type": "dataset", "labels": []},
                    {
                        "title": "Instance Segmentation",
                        "task_type": "instance_segmentation",
                        "labels": [
                            {
                                "name": "label0",
                                "group": "Instance Segmentation Task Labels",
                            },
                            {
                                "name": "label1",
                                "group": "Instance Segmentation Task Labels",
                            },
                        ],
                    },
                ],
            },
        },
        "fxt_datumaro_dataset_multi_label": {
            GetiProjectType.CLASSIFICATION: {
                "connections": [{"from": "Dataset", "to": "Classification"}],
                "tasks": [
                    {"title": "Dataset", "task_type": "dataset", "labels": []},
                    {
                        "title": "Classification",
                        "task_type": "classification",
                        "labels": [
                            {"name": "label0", "group": "label0"},
                            {"name": "label1", "group": "label1"},
                        ],
                    },
                ],
            },
        },
        "fxt_datumaro_dataset_hierarchical": {
            GetiProjectType.CLASSIFICATION: {
                "connections": [{"from": "Dataset", "to": "Classification"}],
                "tasks": [
                    {"title": "Dataset", "task_type": "dataset", "labels": []},
                    {
                        "title": "Classification",
                        "task_type": "classification",
                        "labels": [
                            {
                                "name": "non_square",
                                "group": "rectangle default",
                                "parent": "rectangle",
                            },
                            {
                                "name": "equilateral",
                                "group": "triangle default",
                                "parent": "triangle",
                            },
                            {
                                "name": "right",
                                "group": "triangle default",
                                "parent": "triangle",
                            },
                            {"name": "rectangle", "group": "shape"},
                            {"name": "triangle", "group": "shape"},
                            {
                                "name": "square",
                                "group": "rectangle default",
                                "parent": "rectangle",
                            },
                        ],
                    },
                ],
            },
        },
        "fxt_datumaro_dataset_rotated_detection": {
            GetiProjectType.ROTATED_DETECTION: {
                "connections": [{"from": "Dataset", "to": "Detection Oriented"}],
                "tasks": [
                    {"title": "Dataset", "task_type": "dataset", "labels": []},
                    {
                        "title": "Detection Oriented",
                        "task_type": "rotated_detection",
                        "labels": [
                            {"name": "person", "group": "Detection oriented labels"},
                            {"name": "ball", "group": "Detection oriented labels"},
                        ],
                    },
                ],
            },
        },
        "fxt_datumaro_dataset_anomaly_cls": {
            GetiProjectType.ANOMALY_CLASSIFICATION: {
                "connections": [{"from": "Dataset", "to": "Anomaly Classification"}],
                "tasks": [
                    {"title": "Dataset", "task_type": "dataset", "labels": []},
                    {
                        "title": "Anomaly Classification",
                        "task_type": "anomaly_classification",
                        "labels": [
                            {
                                "name": "Normal",
                                "group": "default - Anomaly classification task",
                            },
                            {
                                "name": "Anomalous",
                                "group": "default - Anomaly classification task",
                            },
                        ],
                    },
                ],
            },
        },
        "fxt_datumaro_dataset_anomaly_det": {
            GetiProjectType.ANOMALY_DETECTION: {
                "connections": [{"from": "Dataset", "to": "Anomaly Detection"}],
                "tasks": [
                    {"title": "Dataset", "task_type": "dataset", "labels": []},
                    {
                        "title": "Anomaly Detection",
                        "task_type": "anomaly_detection",
                        "labels": [
                            {
                                "name": "Normal",
                                "group": "default - Anomaly detection task",
                            },
                            {
                                "name": "Anomalous",
                                "group": "default - Anomaly detection task",
                            },
                        ],
                    },
                ],
            },
        },
        "fxt_datumaro_dataset_anomaly_seg": {
            GetiProjectType.ANOMALY_SEGMENTATION: {
                "connections": [{"from": "Dataset", "to": "Anomaly Segmentation"}],
                "tasks": [
                    {"title": "Dataset", "task_type": "dataset", "labels": []},
                    {
                        "title": "Anomaly Segmentation",
                        "task_type": "anomaly_segmentation",
                        "labels": [
                            {
                                "name": "Normal",
                                "group": "default - Anomaly segmentation task",
                            },
                            {
                                "name": "Anomalous",
                                "group": "default - Anomaly segmentation task",
                            },
                        ],
                    },
                ],
            },
        },
        "fxt_datumaro_dataset_chained_det_cls": {
            GetiProjectType.CHAINED_DETECTION_CLASSIFICATION: {
                "connections": [
                    {"from": "Dataset", "to": "Detection"},
                    {"from": "Detection", "to": "Crop"},
                    {"from": "Crop", "to": "Classification"},
                ],
                "tasks": [
                    {"title": "Dataset", "task_type": "dataset", "labels": []},
                    {
                        "title": "Detection",
                        "task_type": "detection",
                        "labels": [{"name": "det", "group": "Detection labels"}],
                    },
                    {"title": "Crop", "task_type": "crop", "labels": []},
                    {
                        "title": "Classification",
                        "task_type": "classification",
                        "labels": [
                            {"name": "a", "group": "grp_top"},
                            {"name": "b", "group": "grp_top"},
                        ],
                    },
                ],
            },
        },
        "fxt_datumaro_dataset_chained_det_seg": {
            GetiProjectType.CHAINED_DETECTION_SEGMENTATION: {
                "connections": [
                    {"from": "Dataset", "to": "Detection"},
                    {"from": "Detection", "to": "Crop"},
                    {"from": "Crop", "to": "Segmentation"},
                ],
                "tasks": [
                    {"title": "Dataset", "task_type": "dataset", "labels": []},
                    {
                        "title": "Detection",
                        "task_type": "detection",
                        "labels": [{"name": "det", "group": "Detection labels"}],
                    },
                    {"title": "Crop", "task_type": "crop", "labels": []},
                    {
                        "title": "Segmentation",
                        "task_type": "segmentation",
                        "labels": [
                            {"name": "label0", "group": "Segmentation labels"},
                            {"name": "label1", "group": "Segmentation labels"},
                            {"name": "label2", "group": "Segmentation labels"},
                        ],
                    },
                ],
            },
        },
    }


@pytest.fixture(scope="function", params=[True, False])
def fxt_anomaly_reduction(request: pytest.FixtureRequest) -> bool:
    """Parameterize FEATURE_FLAG_ANOMALY_REDUCTION"""
    TestFeatureFlagProvider.set_flag(FeatureFlag.FEATURE_FLAG_ANOMALY_REDUCTION, request.param)
    return request.param


@pytest.fixture(scope="function", params=[True, False])
def fxt_keypoint_detection(request: pytest.FixtureRequest) -> bool:
    """Parameterize FEATURE_FLAG_KEYPOINT_DETECTION"""
    TestFeatureFlagProvider.set_flag(FeatureFlag.FEATURE_FLAG_KEYPOINT_DETECTION, request.param)
    return request.param


@pytest.fixture(scope="session", autouse=True)
def fxt_spicedb_server(request: FixtureRequest):
    container = DockerContainer("ghcr.io/authzed/spicedb:v1.34.0")
    container.with_bind_ports(50051, 50051)
    test_dir = pathlib.Path(__file__).parent
    container.with_volume_mapping((test_dir / "configs/spicedb.zaml").resolve(), "/schema/spicedb.zaml", "ro")
    container.with_env("SPICEDB_GRPC_PRESHARED_KEY", "test")
    container.with_command(
        [
            "serve-testing",
            "--skip-release-check",
            "--load-configs",
            "/schema/spicedb.zaml",
        ]
    )
    container.start()

    wait_for_logs(container, "grpc server started serving", timeout=30)

    yield container

    container.stop()

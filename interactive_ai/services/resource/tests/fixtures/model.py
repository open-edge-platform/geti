# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import datetime
import io
import os
import tempfile
from copy import copy, deepcopy
from zipfile import ZipFile, ZipInfo

import pytest

from tests.fixtures.values import DummyValues

from iai_core_py.adapters.model_adapter import ExportableCodeAdapter
from iai_core_py.configuration.elements.hyper_parameters import NullHyperParameters
from iai_core_py.entities.active_model_state import ActiveModelState
from iai_core_py.entities.metrics import NullPerformance, Performance, ScoreMetric
from iai_core_py.entities.model import (
    Model,
    ModelConfiguration,
    ModelOptimizationType,
    ModelPrecision,
    ModelStatus,
    NullModel,
    OptimizationMethod,
    TrainingFramework,
    TrainingFrameworkType,
)
from iai_core_py.entities.model_storage import ModelStorage, NullModelStorage
from iai_core_py.entities.model_template import (
    DatasetRequirements,
    HyperParameterData,
    InstantiationType,
    ModelTemplate,
    ModelTemplateDeprecationStatus,
    TargetDevice,
    TaskFamily,
    TaskType,
)
from iai_core_py.repos import ModelRepo

os.environ["DEFAULT_TRAINER_VERSION"] = "2.2.0"


@pytest.fixture
def fxt_dataset_requirements():
    yield DatasetRequirements(classes=["ClassX", "ClassY"])


@pytest.fixture
def fxt_dataset_requirements_rest():
    yield {"classes": ["ClassX", "ClassY"]}


@pytest.fixture
def fxt_model_template_dataset():
    yield ModelTemplate(
        model_template_id="test_template_dataset",
        model_template_path="",
        name="Sample Dataset Template",
        task_family=TaskFamily.DATASET,
        task_type=TaskType.DATASET,
        is_trainable=False,
        instantiation=InstantiationType.NONE,
        gigaflops=5,
        size=200.5,
        framework="dummy framework",
        summary="dummy summary",
    )


@pytest.fixture
def fxt_model_template_crop():
    yield ModelTemplate(
        model_template_id="test_template_crop",
        model_template_path="",
        name="Sample Crop Template",
        task_family=TaskFamily.FLOW_CONTROL,
        task_type=TaskType.CROP,
        is_trainable=False,
        instantiation=InstantiationType.NONE,
        framework="dummy framework",
        summary="dummy summary",
    )


@pytest.fixture
def fxt_model_template_classification():
    yield ModelTemplate(
        model_template_id="test_template_classification",
        model_template_path="",
        name="Sample Classification Template",
        task_family=TaskFamily.VISION,
        task_type=TaskType.CLASSIFICATION,
        is_trainable=True,
        hyper_parameters=HyperParameterData(base_path=""),
        instantiation=InstantiationType.NONE,
        gigaflops=10,
        size=12.8,
        framework="dummy framework",
        capabilities=["compute_representations"],
        is_default_for_task=True,
    )


@pytest.fixture
def fxt_model_template_detection():
    yield ModelTemplate(
        model_template_id="test_template_detection",
        model_template_path="",
        name="Sample Detection Template",
        task_family=TaskFamily.VISION,
        task_type=TaskType.DETECTION,
        is_trainable=True,
        hyper_parameters=HyperParameterData(base_path=""),
        instantiation=InstantiationType.NONE,
        gigaflops=13,
        size=150.8,
        framework="dummy framework",
        capabilities=["compute_representations"],
    )


@pytest.fixture
def fxt_model_template_segmentation():
    yield ModelTemplate(
        model_template_id="test_template_segmentation",
        model_template_path="",
        name="Sample Segmentation Template",
        task_family=TaskFamily.VISION,
        task_type=TaskType.SEGMENTATION,
        is_trainable=True,
        hyper_parameters=HyperParameterData(base_path=""),
        instantiation=InstantiationType.NONE,
        gigaflops=24,
        size=88.8,
        framework="dummy framework",
        capabilities=["compute_representations"],
    )


@pytest.fixture
def fxt_model_template_anomaly_classification():
    yield ModelTemplate(
        model_template_id="test_template_anomaly_classification",
        model_template_path="",
        name="Sample Anomaly Classification Template",
        task_family=TaskFamily.VISION,
        task_type=TaskType.ANOMALY_CLASSIFICATION,
        is_trainable=True,
        hyper_parameters=HyperParameterData(base_path=""),
        instantiation=InstantiationType.NONE,
        gigaflops=24,
        size=88.8,
        framework="dummy framework",
        dataset_requirements=DatasetRequirements(classes=["Normal", "Anomalous"]),
    )


@pytest.fixture
def fxt_model_template_anomaly_detection():
    yield ModelTemplate(
        model_template_id="test_template_anomaly_detection",
        model_template_path="",
        name="Sample Anomaly Detection Template",
        task_family=TaskFamily.VISION,
        task_type=TaskType.ANOMALY_DETECTION,
        is_trainable=True,
        hyper_parameters=HyperParameterData(base_path=""),
        instantiation=InstantiationType.NONE,
        gigaflops=24,
        size=88.8,
        framework="dummy framework",
        dataset_requirements=DatasetRequirements(classes=["Normal", "Anomalous"]),
    )


@pytest.fixture
def fxt_model_template_keypoint_detection():
    yield ModelTemplate(
        model_template_id="test_template_keypoint_detection",
        model_template_path="",
        name="Sample Keypoint Detection Template",
        task_family=TaskFamily.VISION,
        task_type=TaskType.KEYPOINT_DETECTION,
        is_trainable=True,
        hyper_parameters=HyperParameterData(base_path=""),
        instantiation=InstantiationType.NONE,
        gigaflops=24,
        size=88.8,
        framework="dummy framework",
    )


@pytest.fixture
def fxt_model_template_obsolete():
    yield ModelTemplate(
        model_template_id="test_template_obsolete",
        model_template_path="",
        name="Sample Obsolete Template",
        task_family=TaskFamily.VISION,
        task_type=TaskType.SEGMENTATION,
        is_trainable=True,
        hyper_parameters=HyperParameterData(base_path=""),
        instantiation=InstantiationType.NONE,
        gigaflops=10,
        size=12.8,
        framework="dummy framework",
        capabilities=["compute_representations"],
        is_default_for_task=True,
        model_status=ModelTemplateDeprecationStatus.OBSOLETE,
    )


@pytest.fixture
def fxt_model_template_1(fxt_model_template_dataset):
    yield fxt_model_template_dataset


@pytest.fixture
def fxt_model_template_2(fxt_model_template_crop):
    yield fxt_model_template_crop


@pytest.fixture
def fxt_model_template(fxt_model_template_1):
    yield fxt_model_template_1


@pytest.fixture
def fxt_model_template_rest_1(fxt_model_template_1):
    yield {
        "model_template_id": fxt_model_template_1.model_template_id,
        "name": fxt_model_template_1.name,
        "task_family": fxt_model_template_1.task_family.name,
        "task_type": fxt_model_template_1.task_type.name,
        "summary": "dummy summary",
        "framework": fxt_model_template_1.framework,
        "max_nodes": fxt_model_template_1.max_nodes,
        "dataset_requirments": {"classes": None},
        "application": None,
        "is_trainable": False,
        "capabilities": [],
        "task_type_sort_priority": -1,
        "model_optimization_methods": [],
    }


@pytest.fixture
def fxt_model_template_rest_2(fxt_model_template_2):
    yield {
        "model_template_id": fxt_model_template_2.model_template_id,
        "name": fxt_model_template_2.name,
        "task_family": fxt_model_template_2.task_family.name,
        "task_type": fxt_model_template_2.task_type.name,
        "summary": "dummy summary",
        "framework": fxt_model_template_2.framework,
        "max_nodes": fxt_model_template_2.max_nodes,
        "dataset_requirments": {"classes": None},
        "application": None,
        "is_trainable": False,
        "capabilities": [],
        "task_type_sort_priority": -1,
        "model_optimization_methods": [],
    }


@pytest.fixture
def fxt_model_template_rest(fxt_model_template_rest_1):
    yield fxt_model_template_rest_1


@pytest.fixture
def fxt_model_storage(fxt_model_template, fxt_mongo_id):
    yield ModelStorage(
        id_=fxt_mongo_id(1),
        project_id=fxt_mongo_id(1),
        task_node_id=fxt_mongo_id(10),
        model_template=fxt_model_template,
    )


@pytest.fixture
def fxt_model_storage_detection(fxt_model_template_detection, fxt_mongo_id):
    yield ModelStorage(
        id_=fxt_mongo_id(5),
        project_id=fxt_mongo_id(1),
        task_node_id=fxt_mongo_id(11),
        model_template=fxt_model_template_detection,
    )


@pytest.fixture
def fxt_model_storage_detection_2(fxt_model_template_detection, fxt_mongo_id):
    yield ModelStorage(
        id_=fxt_mongo_id(6),
        project_id=fxt_mongo_id(1),
        task_node_id=fxt_mongo_id(12),
        model_template=fxt_model_template_detection,
    )


@pytest.fixture
def fxt_model_storage_segmentation(fxt_model_template_segmentation, fxt_mongo_id):
    yield ModelStorage(
        id_=fxt_mongo_id(5),
        project_id=fxt_mongo_id(1),
        task_node_id=fxt_mongo_id(13),
        model_template=fxt_model_template_segmentation,
    )


@pytest.fixture
def fxt_model_storage_anomaly_classification(fxt_model_template_anomaly_classification, fxt_mongo_id):
    yield ModelStorage(
        id_=fxt_mongo_id(5),
        project_id=fxt_mongo_id(1),
        task_node_id=fxt_mongo_id(14),
        model_template=fxt_model_template_anomaly_classification,
    )


@pytest.fixture
def fxt_model_storage_anomaly_detection(fxt_model_template_anomaly_detection, fxt_mongo_id):
    yield ModelStorage(
        id_=fxt_mongo_id(5),
        project_id=fxt_mongo_id(1),
        task_node_id=fxt_mongo_id(14),
        model_template=fxt_model_template_anomaly_detection,
    )


@pytest.fixture
def fxt_null_model_storage():
    yield NullModelStorage()


@pytest.fixture
def fxt_null_model_configuration():
    yield NullHyperParameters()


@pytest.fixture
def fxt_null_model():
    yield NullModel()


@pytest.fixture
def fxt_model(
    fxt_project,
    fxt_dataset_non_empty,
    fxt_model_storage,
    fxt_configuration,
    fxt_label_schema,
    fxt_mongo_id,
):
    yield Model(
        project=fxt_project,
        model_storage=fxt_model_storage,
        train_dataset=fxt_dataset_non_empty,
        configuration=ModelConfiguration(fxt_configuration.data, fxt_label_schema),
        id_=fxt_mongo_id(1),
        creation_date=datetime.datetime(
            2020,
            1,
            1,
            0,
            0,
            0,
            tzinfo=datetime.timezone.utc,
        ),
        data_source_dict={"dummy.file": b"DUMMY_DATA"},
        model_status=ModelStatus.NOT_IMPROVED,
    )


@pytest.fixture
def fxt_obsolete_model(
    fxt_project,
    fxt_dataset_non_empty,
    fxt_model_storage,
    fxt_configuration,
    fxt_label_schema,
    fxt_mongo_id,
):
    yield Model(
        project=fxt_project,
        model_storage=fxt_model_storage,
        train_dataset=fxt_dataset_non_empty,
        configuration=ModelConfiguration(fxt_configuration.data, fxt_label_schema),
        id_=fxt_mongo_id(1),
        creation_date=datetime.datetime(
            2020,
            1,
            1,
            0,
            0,
            0,
            tzinfo=datetime.timezone.utc,
        ),
        data_source_dict={"dummy.file": b"DUMMY_DATA"},
        model_status=ModelStatus.NOT_IMPROVED,
        training_framework=TrainingFramework(type=TrainingFrameworkType.OTX, version="1.6.0"),
    )


@pytest.fixture
def fxt_model_2(
    fxt_project,
    fxt_dataset_non_empty_2,
    fxt_model_storage,
    fxt_configuration,
    fxt_label_schema,
    fxt_mongo_id,
):
    yield Model(
        project=fxt_project,
        model_storage=fxt_model_storage,
        train_dataset=fxt_dataset_non_empty_2,
        configuration=ModelConfiguration(fxt_configuration, fxt_label_schema),
        id_=fxt_mongo_id(2),
        model_status=ModelStatus.NOT_IMPROVED,
        version=2,
    )


@pytest.fixture
def fxt_model_empty_dataset(
    fxt_project,
    fxt_empty_dataset,
    fxt_model_storage,
    fxt_configuration,
    fxt_label_schema,
    fxt_mongo_id,
):
    yield Model(
        project=fxt_project,
        model_storage=fxt_model_storage,
        train_dataset=fxt_empty_dataset,
        configuration=ModelConfiguration(fxt_configuration.data, fxt_label_schema),
        id_=fxt_mongo_id(1),
        data_source_dict={"dummy.file": b"DUMMY_DATA"},
        model_status=ModelStatus.NOT_IMPROVED,
    )


@pytest.fixture
def fxt_model_group_rest(fxt_model, fxt_mongo_id):
    yield {
        "id": fxt_mongo_id(0),
        "name": "Sample Detection Template",
        "task_id": fxt_mongo_id(1),
        "model_template_id": "test_template_detection",
        "models": [
            {
                "id": fxt_model.id_,
                "name": fxt_model.model_storage.name,
                "creation_date": "2020-01-01T00:00:00+00:00",
                "performance": {"score": get_performance_score(fxt_model.performance)},
                "label_schema_in_sync": True,
                "size": fxt_model.size,
                "score_up_to_date": True,
                "active_model": True,
                "version": 1,
                "purge_info": {
                    "is_purged": False,
                    "purge_time": None,
                    "user_uid": None,
                },
                "lifecycle_stage": "active",
            }
        ],
        "learning_approach": "fully_supervised",
        "lifecycle_stage": "active",
    }


@pytest.fixture()
def fxt_model_info_rest(fxt_model, fxt_dataset_counts):
    yield {
        "id": fxt_model.id_,
        "name": fxt_model.model_storage.name,
        "architecture": fxt_model.model_storage.model_template.name,
        "creation_date": "2020-01-01T00:00:00+00:00",
        "size": fxt_model.size,
        "performance": {"score": get_performance_score(fxt_model.performance)},
        "label_schema_in_sync": True,
        "score_up_to_date": True,
        "fps_throughput": fxt_model.fps_throughput,
        "latency": fxt_model.latency,
        "precision": [p.name for p in fxt_model.precision],
        "target_device": fxt_model.target_device.name,
        "target_device_type": fxt_model.target_device_type,
        "optimized_models": [],
        "version": 1,
        "total_disk_size": 1,
        "previous_trained_revision_id": "",
        "previous_revision_id": "",
        "labels": [
            {
                "color": "#ff0000ff",
                "group": "from_label_list",
                "hotkey": "ctrl+V",
                "id": "60d31793d5f1fb7e6e3c1a50",
                "is_empty": False,
                "is_anomalous": False,
                "name": "dog",
                "parent_id": None,
            }
        ],
        "training_dataset_info": fxt_dataset_counts,
        "training_framework": {"type": "otx", "version": "2.2.0"},
        "purge_info": {"is_purged": False, "purge_time": None, "user_uid": None},
        "learning_approach": "fully_supervised",
        "lifecycle_stage": "active",
    }


@pytest.fixture()
def fxt_obsolete_model_info_rest(fxt_obsolete_model, fxt_dataset_counts):
    yield {
        "id": fxt_obsolete_model.id_,
        "name": fxt_obsolete_model.model_storage.name,
        "architecture": fxt_obsolete_model.model_storage.model_template.name,
        "creation_date": "2020-01-01T00:00:00+00:00",
        "size": fxt_obsolete_model.size,
        "performance": {"score": get_performance_score(fxt_obsolete_model.performance)},
        "label_schema_in_sync": True,
        "score_up_to_date": True,
        "fps_throughput": fxt_obsolete_model.fps_throughput,
        "latency": fxt_obsolete_model.latency,
        "precision": [p.name for p in fxt_obsolete_model.precision],
        "target_device": fxt_obsolete_model.target_device.name,
        "target_device_type": fxt_obsolete_model.target_device_type,
        "optimized_models": [],
        "version": 1,
        "total_disk_size": 1,
        "previous_trained_revision_id": "",
        "previous_revision_id": "",
        "labels": [
            {
                "color": "#ff0000ff",
                "group": "from_label_list",
                "hotkey": "ctrl+V",
                "id": "60d31793d5f1fb7e6e3c1a50",
                "is_empty": False,
                "is_anomalous": False,
                "name": "dog",
                "parent_id": None,
            }
        ],
        "training_dataset_info": fxt_dataset_counts,
        "training_framework": {"type": "otx", "version": "1.6.0"},
        "purge_info": {"is_purged": False, "purge_time": None, "user_uid": None},
        "learning_approach": "fully_supervised",
        "lifecycle_stage": "obsolete",
    }


@pytest.fixture
def fxt_optimized_model_1(
    fxt_project,
    fxt_empty_dataset,
    fxt_model_storage,
    fxt_pot_hyperparameters,
    fxt_model_template,
    fxt_model,
):
    yield Model(
        project=fxt_project,
        model_storage=fxt_model_storage,
        train_dataset=fxt_empty_dataset,
        configuration=ModelConfiguration(fxt_pot_hyperparameters, fxt_model_template),
        id_=ModelRepo.generate_id(),
        creation_date=DummyValues.DATE_METRIC_AS_DATETIME,
        previous_trained_revision=fxt_model,
        previous_revision=fxt_model,
        data_source_dict={"openvino.xml": b"data1", "openvino.bin": b"data2"},
        model_status=ModelStatus.SUCCESS,
        precision=[ModelPrecision.FP16],
        latency=100,
        fps_throughput=10,
        target_device=TargetDevice.GPU,
        optimization_type=ModelOptimizationType.POT,
        optimization_methods=[OptimizationMethod.FILTER_PRUNING],
        optimization_objectives={"bit_complexity_ratio": "0.3"},
        performance_improvement={"some improvement": 0.55},
        model_size_reduction=0.3,
        exportable_code_adapter=ExportableCodeAdapter(data_source=b"DUMMY_DATA"),
        size=10,
    )


@pytest.fixture
def fxt_optimized_openvino_model(
    fxt_project,
    fxt_dataset_non_empty,
    fxt_model_storage,
    fxt_configuration,
    fxt_label_schema,
):
    yield Model(
        project=fxt_project,
        model_storage=fxt_model_storage,
        train_dataset=fxt_dataset_non_empty,
        configuration=ModelConfiguration(fxt_configuration.data, fxt_label_schema),
        id_=ModelRepo.generate_id(),
        data_source_dict={"dummy.file": b"DUMMY_DATA"},
        exportable_code_adapter=ExportableCodeAdapter(data_source=b"DUMMY_EXPORTABLE_CODE_DATA"),
    )


@pytest.fixture
def fxt_optimized_model_1_with_exportable_code(fxt_optimized_model_1, fxt_zip_file_binary_stream):
    fxt_optimized_model_1_with_exportable_code = deepcopy(fxt_optimized_model_1)
    fxt_optimized_model_1_with_exportable_code.exportable_code = fxt_zip_file_binary_stream
    yield fxt_optimized_model_1_with_exportable_code


@pytest.fixture
def fxt_optimized_model_2(
    fxt_project,
    fxt_empty_dataset,
    fxt_model_storage,
    fxt_pot_hyperparameters,
    fxt_model_template,
    fxt_model,
):
    yield Model(
        project=fxt_project,
        model_storage=fxt_model_storage,
        train_dataset=fxt_empty_dataset,
        configuration=ModelConfiguration(fxt_pot_hyperparameters, fxt_model_template),
        id_=ModelRepo.generate_id(),
        creation_date=DummyValues.DATE_METRIC_AS_DATETIME,
        previous_trained_revision=fxt_model,
        previous_revision=fxt_model,
        data_source_dict={"openvino.xml": b"data1", "openvino.bin": b"data2"},
        model_status=ModelStatus.SUCCESS,
        precision=[ModelPrecision.INT8],
        latency=100,
        fps_throughput=10,
        target_device=TargetDevice.GPU,
        optimization_type=ModelOptimizationType.POT,
        optimization_methods=[OptimizationMethod.QUANTIZATION],
        optimization_objectives={"num_bits": "8"},
        performance_improvement={"some improvement": 0.4},
        model_size_reduction=0.8,
    )


@pytest.fixture
def fxt_optimized_model_2_with_exportable_code(fxt_optimized_model_2, fxt_zip_file_binary_stream):
    fxt_optimized_model_2_with_exportable_code = deepcopy(fxt_optimized_model_2)
    fxt_optimized_model_2_with_exportable_code.exportable_code = fxt_zip_file_binary_stream
    yield fxt_optimized_model_2_with_exportable_code


@pytest.fixture
def fxt_optimized_model(fxt_optimized_model_1):
    yield fxt_optimized_model_1


@pytest.fixture
def fxt_optimized_model_intermediate(fxt_optimized_model):
    yield fxt_optimized_model


@pytest.fixture
def fxt_optimized_model_leaf(
    fxt_project,
    fxt_empty_dataset,
    fxt_model_storage,
    fxt_null_model_configuration,
    fxt_model_template,
    fxt_model,
    fxt_optimized_model_intermediate,
):
    # note: previous_revision points to the intermediate model
    yield Model(
        project=fxt_project,
        model_storage=fxt_model_storage,
        train_dataset=fxt_empty_dataset,
        configuration=ModelConfiguration(fxt_null_model_configuration, fxt_model_template),
        id_=ModelRepo.generate_id(),
        creation_date=DummyValues.DATE_METRIC_AS_DATETIME,
        previous_trained_revision=fxt_model,
        previous_revision=fxt_optimized_model_intermediate,
        data_source_dict={"openvino.xml": b"data1", "openvino.bin": b"data2"},
        model_status=ModelStatus.SUCCESS,
        precision=[ModelPrecision.FP16],
        latency=100,
        fps_throughput=10,
        target_device=TargetDevice.GPU,
        optimization_type=ModelOptimizationType.MO,
        optimization_methods=[OptimizationMethod.FILTER_PRUNING],
        optimization_objectives={"bit_complexity_ratio": "0.3"},
        performance_improvement={"some improvement": 0.55},
        model_size_reduction=0.3,
    )


@pytest.fixture
def fxt_optimized_model_rest(fxt_optimized_model):
    yield {
        "id": fxt_optimized_model.id_,
        "name": fxt_optimized_model.model_storage.name + " OpenVINO FP16",
        "precision": [p.name for p in fxt_optimized_model.precision],
        "has_xai_head": False,
        "model_format": "OpenVINO",
        "target_device": fxt_optimized_model.target_device.name,
        "target_device_type": fxt_optimized_model.target_device_type,
        "size": fxt_optimized_model.size,
        "performance": {"score": get_performance_score(fxt_optimized_model.performance)},
        "latency": fxt_optimized_model.latency,
        "fps_throughput": fxt_optimized_model.fps_throughput,
        "optimization_type": fxt_optimized_model.optimization_type.name,
        "optimization_methods": [m.name for m in fxt_optimized_model.optimization_methods],
        "optimization_objectives": fxt_optimized_model.optimization_objectives,
        "model_status": fxt_optimized_model.model_status.name,
        "version": 1,
        "previous_trained_revision_id": fxt_optimized_model.previous_trained_revision_id,
        "previous_revision_id": fxt_optimized_model.previous_revision_id,
        "creation_date": DummyValues.DATE_METRIC_AS_STRING,
        "configurations": [],
        "lifecycle_stage": "active",
    }


@pytest.fixture
def fxt_optimized_model_rest_2(fxt_optimized_model_2):
    rest_view = {
        "id": fxt_optimized_model_2.id_,
        "name": fxt_optimized_model_2.model_storage.name + " OpenVINO INT8",
        "precision": [p.name for p in fxt_optimized_model_2.precision],
        "has_xai_head": False,
        "model_format": "OpenVINO",
        "target_device": fxt_optimized_model_2.target_device.name,
        "target_device_type": fxt_optimized_model_2.target_device_type,
        "size": fxt_optimized_model_2.size,
        "performance": {"score": get_performance_score(fxt_optimized_model_2.performance)},
        "latency": fxt_optimized_model_2.latency,
        "fps_throughput": fxt_optimized_model_2.fps_throughput,
        "optimization_type": fxt_optimized_model_2.optimization_type.name,
        "optimization_methods": [m.name for m in fxt_optimized_model_2.optimization_methods],
        "optimization_objectives": fxt_optimized_model_2.optimization_objectives,
        "model_status": fxt_optimized_model_2.model_status.name,
        "version": 1,
        "previous_trained_revision_id": fxt_optimized_model_2.previous_trained_revision_id,
        "previous_revision_id": fxt_optimized_model_2.previous_revision_id,
        "creation_date": DummyValues.DATE_METRIC_AS_STRING,
        "configurations": [],
        "lifecycle_stage": "active",
    }
    if fxt_optimized_model_2.optimization_type == ModelOptimizationType.POT:
        pot_settings = fxt_optimized_model_2.configuration.configurable_parameters.pot_parameters
        sample_size = {
            "name": "sample_size",
            "value": pot_settings.stat_subset_size,
        }
        rest_view["configurations"].append(sample_size)
    yield rest_view


@pytest.fixture
def fxt_model_not_ready(fxt_model):
    model = copy(fxt_model)
    model.model_status = ModelStatus.NOT_READY
    yield model


@pytest.fixture
def fxt_model_improved(fxt_model):
    model = copy(fxt_model)
    model.model_status = ModelStatus.SUCCESS
    model.performance = Performance(score=ScoreMetric(value=0.8, name="accuracy"))
    yield model


@pytest.fixture
def fxt_model_failed(fxt_model):
    model = copy(fxt_model)
    model.model_status = ModelStatus.FAILED
    yield model


@pytest.fixture
def fxt_model_trained_no_stats(fxt_model):
    model = copy(fxt_model)
    model.model_status = ModelStatus.TRAINED_NO_STATS
    yield model


@pytest.fixture
def fxt_model_not_improved(fxt_model):
    model = copy(fxt_model)
    model.model_status = ModelStatus.NOT_IMPROVED
    yield model


@pytest.fixture
def fxt_active_model_state(fxt_mongo_id, fxt_model_storage):
    return ActiveModelState(
        task_node_id=fxt_mongo_id(0),
        active_model_storage=fxt_model_storage,
    )


@pytest.fixture
def fxt_zip_file_data():
    output_bytes = io.BytesIO()
    with ZipFile(output_bytes, "w") as zf:
        info = ZipInfo("dummy.file")
        zf.writestr(info, b"DUMMY_DATA")
    output_bytes.seek(0)
    return output_bytes


@pytest.fixture
def fxt_zip_file_binary_stream(fxt_zip_file):
    """
    returns: binary representation of zip file
    """
    yield fxt_zip_file.getvalue()


@pytest.fixture()
def fxt_zip_file():
    """
    returns: zip archive
    """
    archive = io.BytesIO()

    with ZipFile(archive, mode="w") as zf, tempfile.NamedTemporaryFile(prefix="temp_file_in_zip") as temp_file:
        zf.write(temp_file.name)

    yield archive


def get_performance_score(performance: Performance) -> float | None:
    if isinstance(performance, NullPerformance):
        return None
    return performance.score.value

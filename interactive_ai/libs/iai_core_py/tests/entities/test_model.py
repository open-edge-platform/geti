# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module tests the Model class"""

import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

import iai_core.configuration.helper as cfg_helper
from iai_core.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core.entities.annotation import NullAnnotationScene
from iai_core.entities.dataset_item import DatasetItem
from iai_core.entities.datasets import Dataset, NullDataset
from iai_core.entities.image import Image
from iai_core.entities.label import Domain, Label
from iai_core.entities.label_schema import LabelSchema
from iai_core.entities.metrics import NullPerformance, Performance, ScoreMetric
from iai_core.entities.model import (
    Model,
    ModelConfiguration,
    ModelDeprecationStatus,
    ModelFormat,
    ModelOptimizationType,
    ModelPrecision,
    ModelStatus,
    NullModel,
    OptimizationMethod,
    TrainingFramework,
    TrainingFrameworkType,
)
from iai_core.entities.model_storage import NullModelStorage
from iai_core.entities.model_template import TargetDevice, parse_model_template
from iai_core.entities.project import NullProject
from iai_core.entities.task_environment import TaskEnvironment
from iai_core.utils.time_utils import now
from tests.entities.test_dataset_item import DatasetItemParameters
from tests.test_helpers import empty_model_configuration, generate_random_single_image

from geti_types import ID


class TestModelConfiguration:
    def test_model_configuration(self):
        """
        <b>Description:</b>
        Check that ModelConfiguration correctly returns the configuration

        <b>Input data:</b>
        ConfigurableParameters, LabelSchema

        <b>Expected results:</b>
        Test passes if ModelConfiguration correctly returns the configuration

        <b>Steps</b>
        1. Check configuration params in the ModelConfiguration
        """
        parameters = ConfigurableParameters(header="Test header")
        label_schema = LabelSchema(id_=ID("label_schema_id"))
        model_configuration = ModelConfiguration(configurable_parameters=parameters, label_schema=label_schema)
        assert model_configuration.configurable_parameters == parameters
        assert model_configuration.get_label_schema() == label_schema


class TestModel:
    creation_date = now()

    @staticmethod
    def generate_random_image():
        image = DatasetItemParameters.generate_random_image()
        return DatasetItem(ID("some_image"), media=image, annotation_scene=NullAnnotationScene())

    def generate_random_image_old(self):
        with generate_random_single_image() as path:
            image = Image(name="test_image", id=ID("test_image"), uploader_id="uploader", file_path=path)
            return DatasetItem(ID("some_image"), media=image, annotation_scene=NullAnnotationScene())

    def dataset(self):
        return Dataset(id=ID("dataset"), items=[self.generate_random_image()])

    def configuration(self):
        parameters = ConfigurableParameters(header="Test header")
        label_schema = LabelSchema(id_=ID("label_schema_id"))
        return ModelConfiguration(configurable_parameters=parameters, label_schema=label_schema)

    def other_configuration(self):
        parameters = ConfigurableParameters(header="Other test header")
        label_schema = LabelSchema(id_=ID("other_label_schema_id"))
        return ModelConfiguration(configurable_parameters=parameters, label_schema=label_schema)

    def test_model_entity_default_values(self):
        """
        <b>Description:</b>
        Check that Model correctly returns the default values

        <b>Expected results:</b>
        Test passes if Model correctly returns the default values

        <b>Steps</b>
        1. Check default values in the Model
        """

        model_entity = Model(
            project=None,
            model_storage=None,
            train_dataset=self.dataset(),
            configuration=self.configuration(),
            id_=ID("model"),
        )

        assert isinstance(model_entity.configuration, ModelConfiguration)
        assert isinstance(model_entity.creation_date, datetime)
        assert isinstance(model_entity.train_dataset, Dataset)
        assert model_entity.version == 1
        assert model_entity.model_format == ModelFormat.OPENVINO
        assert model_entity.precision == [ModelPrecision.FP32]
        assert model_entity.target_device == TargetDevice.CPU
        assert model_entity.optimization_type == ModelOptimizationType.NONE
        assert model_entity.performance == NullPerformance()

        for default_val_none in [
            "previous_trained_revision",
            "previous_revision",
            "target_device_type",
        ]:
            assert getattr(model_entity, default_val_none) is None

        for default_val_0_0 in ["training_duration", "model_size_reduction"]:
            assert getattr(model_entity, default_val_0_0) == 0.0

        for default_val_empty_list in ["tags", "optimization_methods"]:
            assert getattr(model_entity, default_val_empty_list) == []

        for default_val_empty_dict in [
            "model_adapters",
            "optimization_objectives",
            "performance_improvement",
        ]:
            assert getattr(model_entity, default_val_empty_dict) == {}

        for default_val_zero in ["latency", "fps_throughput"]:
            assert getattr(model_entity, default_val_zero) == 0

        assert model_entity.is_optimized() is False

    def test_model_entity_sets_values(self):
        """
        <b>Description:</b>
        Check that Model correctly returns the set values

        <b>Expected results:</b>
        Test passes if Model correctly returns the set values

        <b>Steps</b>
        1. Check set values in the Model
        """

        def __get_path_to_file(filename: str):
            """
            Return the path to the file named 'filename', which lives in the tests/entities directory
            """
            return str(Path(__file__).parent / Path(filename))

        car = Label(id_=ID("car"), name="car", domain=Domain.DETECTION)
        labels_list = [car]
        dummy_template = __get_path_to_file("./dummy_template.yaml")
        model_template = parse_model_template(dummy_template)
        hyper_parameters = model_template.hyper_parameters.data
        params = cfg_helper.create(hyper_parameters)
        labels_schema = LabelSchema.from_labels(labels_list)
        environment = TaskEnvironment(
            model=None,
            hyper_parameters=params,
            label_schema=labels_schema,
            model_template=model_template,
        )

        item = self.generate_random_image()
        dataset = Dataset(id=ID("dataset_id"), items=[item])
        score_metric = ScoreMetric(name="Model accuracy", value=0.5)

        model_entity = Model(
            project=None,
            model_storage=None,
            train_dataset=self.dataset(),
            configuration=self.configuration(),
            id_=ID("model"),
        )

        set_params = {
            "configuration": environment.get_model_configuration(),
            "train_dataset": dataset,
            "id": ID(1234567890),
            "creation_date": self.creation_date,
            "previous_trained_revision": 5,
            "previous_revision": 2,
            "version": 2,
            "tags": ["tree", "person"],
            "model_format": ModelFormat.BASE_FRAMEWORK,
            "performance": Performance(score_metric),
            "training_duration": 5.8,
            "precision": [ModelPrecision.INT8],
            "latency": 328,
            "fps_throughput": 20,
            "target_device": TargetDevice.GPU,
            "target_device_type": "notebook",
            "optimization_methods": [OptimizationMethod.QUANTIZATION],
            "optimization_type": ModelOptimizationType.MO,
            "optimization_objectives": {"param": "Test param"},
            "performance_improvement": {"speed", 0.5},
            "model_size_reduction": 1.0,
        }

        for key, value in set_params.items():
            setattr(model_entity, key, value)
            assert getattr(model_entity, key) == value

        assert model_entity.is_optimized() is True

    def test_model_entity_model_adapters(self):
        """
        <b>Description:</b>
        Check that Model correctly returns the adapters

        <b>Expected results:</b>
        Test passes if Model correctly returns the adapters

        <b>Steps</b>
        1. Create a Model with adapters
        2. Change data source for an adapter
        3. Remove an adapter
        """

        data_source_0 = b"{0: binaryrepo://localhost/repo/data_source/0}"
        data_source_1 = b"binaryrepo://localhost/repo/data_source/1"
        data_source_2 = b"binaryrepo://localhost/repo/data_source/2"
        data_source_3 = b"binaryrepo://localhost/repo/data_source/3"

        temp_dir = tempfile.TemporaryDirectory()
        temp_file = os.path.join(temp_dir.name, "data_source_0")

        with open(temp_file, "wb") as tmp:
            tmp.write(data_source_0)

        data_source_dict = {
            "0": data_source_0,
            "1": data_source_1,
            "2": data_source_2,
        }

        model_entity = Model(
            project=None,
            model_storage=None,
            train_dataset=self.dataset(),
            configuration=self.configuration(),
            id_=ID("model"),
            data_source_dict=data_source_dict,
        )

        # Adapter with key 0 not from file
        assert model_entity.model_adapters["0"].from_file_storage is False

        model_entity.set_data("0", temp_file)

        for adapter in model_entity.model_adapters:
            if adapter == "0":
                # Adapter with key 0 from file
                assert model_entity.model_adapters[adapter].from_file_storage is True
            else:
                assert model_entity.model_adapters[adapter].from_file_storage is False

        assert model_entity.get_data("1") == data_source_1

        model_entity.set_data("2", data_source_1)
        assert model_entity.get_data("2") == data_source_1
        assert len(model_entity.model_adapters) == 3

        model_entity.set_data("3", data_source_3)
        assert model_entity.get_data("3") == data_source_3
        assert len(model_entity.model_adapters) == 4

        model_entity.delete_data("3")
        assert len(model_entity.model_adapters) == 3

        # Attempt to retrieve a missing and deleted key
        with pytest.raises(KeyError):
            model_entity.get_data("5")

        with pytest.raises(KeyError):
            model_entity.get_data("3")

    def test_models_with_no_data(self, fxt_ote_id, fxt_training_framework) -> None:
        """
        <b>Description:</b>
        Check if no data is returned for a failed model

        <b>Input data:</b>
            A Model with Data

        <b>Expected results:</b>
        If a model is created that failed training without data, the data should be equal to empty bytes

        <b>Steps</b>
        1. Test failed model without data
        """

        # Test creating failed model with no data then calling the data property, should return empty bytes
        failed_model = Model(
            project=NullProject(),
            model_storage=NullModelStorage(),
            train_dataset=NullDataset(),
            configuration=empty_model_configuration(),
            id_=fxt_ote_id(1),
            data_source_dict={"test": b""},
            training_framework=fxt_training_framework,
            model_status=ModelStatus.NOT_IMPROVED,
        )
        data = failed_model.get_data("test")
        assert data == b""
        assert failed_model.size == 0

    def test_model_equality(self, fxt_model, fxt_training_framework) -> None:
        """
        <b>Description:</b>
        Check that Model equality works correctly

        <b>Input data:</b>
        Model instances

        <b>Expected results:</b>
        == and != operations work correctly for various inputs

        <b>Steps</b>
        1. Test Model equality
        2. Test NullModel equality
        """
        identical_model = Model(
            project=fxt_model.get_project(),
            model_storage=fxt_model.model_storage,
            train_dataset=fxt_model.train_dataset,
            configuration=fxt_model.configuration,
            id_=fxt_model.id_,
            performance=fxt_model.performance,
            data_source_dict={"test": b"data"},
            training_framework=fxt_training_framework,
        )
        assert identical_model == fxt_model

        assert NullModel() == NullModel()
        assert identical_model != NullModel()

    def test_model_is_optimized(self, fxt_model) -> None:
        """
        <b>Description:</b>
        Check that Model is_optimized method works correctly

        <b>Input data:</b>
        Model instances

        <b>Expected results:</b>
        is_optimized works correctly for various inputs

        <b>Steps</b>
        1. Test base model
        2. Test openvino optimized model
        3. Test onnx optimized model
        """
        assert fxt_model.is_optimized() is False

        fxt_model.model_format = ModelFormat.OPENVINO
        fxt_model.optimization_type = ModelOptimizationType.MO

        assert fxt_model.is_optimized() is True

        fxt_model.model_format = ModelFormat.ONNX
        fxt_model.optimization_type = ModelOptimizationType.ONNX

        assert fxt_model.is_optimized() is True

    def test_get_base_model(self, fxt_model) -> None:
        """
        <b>Description:</b>
        Check that the correct base framework model is returned

        <b>Input data:</b>
        Base framework and optimized models

        <b>Expected results:</b>
        The correct base framework model is returned

        <b>Steps</b>
        1. Test base model can be retrieved from optimized model
        2. Test model is returned if it is already the base model
        """
        base_model = Model(
            project=fxt_model.get_project(),
            model_storage=fxt_model.model_storage,
            train_dataset=fxt_model.train_dataset,
            configuration=fxt_model.configuration,
            id_=ID("base_model"),
            performance=fxt_model.performance,
            data_source_dict={"test": b"data"},
            training_framework=fxt_model.training_framework,
            model_format=ModelFormat.BASE_FRAMEWORK,
            optimization_type=ModelOptimizationType.NONE,
        )
        optimized_model = Model(
            project=fxt_model.get_project(),
            model_storage=fxt_model.model_storage,
            train_dataset=fxt_model.train_dataset,
            configuration=fxt_model.configuration,
            id_=ID("mo_model"),
            performance=fxt_model.performance,
            previous_trained_revision=base_model,
            data_source_dict={"test": b"data"},
            training_framework=fxt_model.training_framework,
            model_format=ModelFormat.OPENVINO,
            optimization_type=ModelOptimizationType.MO,
        )

        assert optimized_model.get_base_model() == base_model
        assert base_model.get_base_model() == base_model

    def test_model_deprecation_status(self, fxt_model) -> None:
        """
        <b>Description:</b>
        Check the model deprecation status depends on the training framework version.

        <b>Input data:</b>
        Model

        <b>Expected results:</b>
        The correct deprecation status is returned

        <b>Steps</b>
        1. Check with a OTX 1.6 model
        2. Check with an OTX 2.2 model
        """
        model_16 = Model(
            project=fxt_model.get_project(),
            model_storage=fxt_model.model_storage,
            train_dataset=fxt_model.train_dataset,
            configuration=fxt_model.configuration,
            id_=ID("base_model"),
            performance=fxt_model.performance,
            data_source_dict={"test": b"data"},
            training_framework=TrainingFramework(type=TrainingFrameworkType.OTX, version="1.6.0"),
            model_format=ModelFormat.BASE_FRAMEWORK,
            optimization_type=ModelOptimizationType.NONE,
        )

        assert model_16.model_deprecation_status == ModelDeprecationStatus.OBSOLETE

        model_22 = Model(
            project=fxt_model.get_project(),
            model_storage=fxt_model.model_storage,
            train_dataset=fxt_model.train_dataset,
            configuration=fxt_model.configuration,
            id_=ID("base_model"),
            performance=fxt_model.performance,
            data_source_dict={"test": b"data"},
            training_framework=TrainingFramework(type=TrainingFrameworkType.OTX, version="2.2.0"),
            model_format=ModelFormat.BASE_FRAMEWORK,
            optimization_type=ModelOptimizationType.NONE,
        )

        assert model_22.model_deprecation_status == ModelDeprecationStatus.ACTIVE

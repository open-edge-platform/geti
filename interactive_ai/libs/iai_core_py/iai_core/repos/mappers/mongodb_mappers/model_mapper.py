#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the MongoDB mapper for model related entities"""

import logging
from enum import IntEnum, auto

import iai_core.configuration.helper as otx_config_helper
from iai_core.adapters.adapter import ProxyAdapter
from iai_core.adapters.model_adapter import DataSource, ExportableCodeAdapter
from iai_core.entities.model import (
    Model,
    ModelConfiguration,
    ModelFormat,
    ModelOptimizationType,
    ModelPrecision,
    ModelPurgeInfo,
    ModelStatus,
    OptimizationMethod,
    TrainingFramework,
    TrainingFrameworkType,
)
from iai_core.entities.model_storage import ModelStorageIdentifier
from iai_core.entities.model_template import TargetDevice
from iai_core.repos.mappers.mongodb_mapper_interface import (
    IMapperForward,
    IMapperProjectIdentifierBackward,
    IMapperSimple,
)

from .id_mapper import IDToMongo
from .label_mapper import LabelSchemaToMongo
from .metrics_mapper import PerformanceToMongo
from .primitive_mapper import DatetimeToMongo
from geti_types import ProjectIdentifier

logger = logging.getLogger(__name__)


class ModelType(IntEnum):
    """
    This class enumerates the model type, used as a label inside the model document in
    the MongoDB collection of a Model. The model type is needed to translate a model document back to the
    correct model entity.
    """

    ORIGINAL_MODEL = auto()
    OPTIMIZED_MODEL = auto()


class ModelConfigurationToMongo(
    IMapperForward[ModelConfiguration, dict],
    IMapperProjectIdentifierBackward[ModelConfiguration, dict],
):
    """MongoDB mapper for `ModelConfiguration` entities"""

    @staticmethod
    def forward(instance: ModelConfiguration) -> dict:
        if instance.configurable_parameters is not None:
            serialized_params = otx_config_helper.convert(
                instance.configurable_parameters,
                target=dict,
                enum_to_str=True,
                id_to_str=True,
            )
        else:
            serialized_params = {}
        return {
            "configurable_parameters": serialized_params,
            "label_schema": LabelSchemaToMongo.forward(instance.get_label_schema()),
        }

    @staticmethod
    def backward(instance: dict, parameters: ProjectIdentifier) -> ModelConfiguration:
        project_identifier = parameters

        configurable_parameters_dict = instance["configurable_parameters"]
        if configurable_parameters_dict:
            configurable_parameters = otx_config_helper.create(configurable_parameters_dict)
        else:
            configurable_parameters = None

        # note: the label schema documents nested inside the model doc do not have
        # the 'workspace_id' and 'project_id' fields, unlike the first-class label
        # schema docs which have it because injected by the session-based repo.
        label_schema_id = IDToMongo.backward(instance["label_schema"]["_id"])
        instance["label_schema"]["workspace_id"] = str(project_identifier.workspace_id)
        instance["label_schema"]["project_id"] = str(project_identifier.project_id)
        label_schema_adapter = ProxyAdapter(
            proxy=lambda: LabelSchemaToMongo.backward(instance["label_schema"]),
            id=label_schema_id,
        )

        return ModelConfiguration.with_adapters(
            configurable_parameters=configurable_parameters,  # type: ignore
            label_schema_adapter=label_schema_adapter,
        )


class TrainingFrameworkToMongo(IMapperSimple[TrainingFramework, dict]):
    @staticmethod
    def forward(instance: TrainingFramework) -> dict:
        return {
            "type": instance.type.name,
            "version": instance.version,
        }

    @staticmethod
    def backward(instance: dict) -> TrainingFramework:
        return TrainingFramework(
            type=TrainingFrameworkType[instance["type"]],
            version=instance["version"],
        )


class ModelPurgeInfoToMongo(IMapperSimple[ModelPurgeInfo, dict]):
    @staticmethod
    def forward(instance: ModelPurgeInfo) -> dict:
        if not instance.is_purged:
            return {"is_purged": False}
        return {
            "is_purged": instance.is_purged,
            "purge_time": DatetimeToMongo.forward(instance.purge_time) if instance.purge_time is not None else None,
            "user_uid": instance.user_uid,
        }

    @staticmethod
    def backward(instance: dict) -> ModelPurgeInfo:
        if not instance:
            return ModelPurgeInfo()
        purge_time = instance.get("purge_time")
        if purge_time is not None:
            purge_time = DatetimeToMongo.backward(purge_time)
        return ModelPurgeInfo(
            is_purged=instance["is_purged"],
            purge_time=purge_time,
            user_uid=instance.get("user_uid"),
        )


class ModelToMongo(IMapperSimple[Model, dict]):
    """MongoDB mapper for 'Model' entities"""

    @staticmethod
    def forward(instance: Model) -> dict:
        # A check is done on the model adapters which is created from the data_source_dict
        if (
            instance.model_status == ModelStatus.SUCCESS
            and len(instance.model_adapters) == 0
            and not instance.purge_info.is_purged
        ):
            logger.error(
                f"Cannot save a trained model without adapters (id='{instance.id_}', "
                f"format='{instance.model_format.name}', optimization_type='{instance.optimization_type.name}')"
            )
            raise ValueError("Invalid model: successfully trained but missing adapters")

        performance_improvement = {}
        for key, value in instance.performance_improvement.items():
            performance_improvement[key] = str(value)

        # We store the list of weights as a list of [(key, filename)] rather than a
        # dict {key: val} because MongoDB does not support arbitrary strings as keys.
        weight_paths_data = list(instance.weight_paths.items())

        if instance.exportable_code_adapter is not None and isinstance(
            instance.exportable_code_adapter.data_source, DataSource
        ):
            exportable_code_filename = instance.exportable_code_adapter.data_source.binary_filename
        else:
            exportable_code_filename = ""
        return {
            "_id": IDToMongo.forward(instance.id_),
            "tags": instance.tags,
            "creation_date": DatetimeToMongo.forward(instance.creation_date),
            "train_dataset_id": IDToMongo.forward(instance.train_dataset_id),
            "previous_trained_revision_id": IDToMongo.forward(instance.previous_trained_revision_id),
            "previous_revision_id": IDToMongo.forward(instance.previous_revision_id),
            "training_framework": TrainingFrameworkToMongo.forward(instance.training_framework),
            "model_status": instance.model_status.name,
            "model_format": instance.model_format.name,
            "performance": PerformanceToMongo.forward(instance.performance),
            "training_duration": instance.training_duration,
            "training_job_duration": instance.training_job_duration,
            "configuration": ModelConfigurationToMongo.forward(instance.configuration),
            "precision": [precision.name for precision in instance.precision],
            "has_xai_head": instance.has_xai_head,
            "target_device": instance.target_device.name,
            "target_device_type": instance.target_device_type,
            "latency": instance.latency,
            "fps_throughput": instance.fps_throughput,
            "weight_paths": weight_paths_data,
            "optimization_methods": [optimization_method.name for optimization_method in instance.optimization_methods],
            "optimization_objectives": instance.optimization_objectives,
            "optimization_type": instance.optimization_type.name,
            "performance_improvement": performance_improvement,
            "model_size_reduction": str(instance.model_size_reduction),
            "exportable_code_path": exportable_code_filename,
            "size": instance.size,
            "version": instance.version,
            "purge_info": ModelPurgeInfoToMongo.forward(instance.purge_info),
        }

    @staticmethod
    def backward(instance: dict) -> Model:
        performance_improvement_data = instance.get("performance_improvement", {})
        performance_improvement = {}

        for key, value in performance_improvement_data.items():
            performance_improvement[key] = float(value)
        model = ModelToMongo.map_model_backward(instance=instance)
        model.model_size_reduction = float(instance["model_size_reduction"])
        model.performance_improvement = performance_improvement
        model.optimization_objectives = instance.get("optimization_objectives", {})
        model.optimization_methods = [
            OptimizationMethod[optimization_method] for optimization_method in instance.get("optimization_methods", [])
        ]
        model.target_device = TargetDevice[instance.get("target_device", TargetDevice.UNSPECIFIED.name)]
        model.precision = [ModelPrecision[model_precision] for model_precision in instance.get("precision", [])]
        model.has_xai_head = bool(instance.get("has_xai_head", 1))
        model.optimization_type = ModelOptimizationType[instance["optimization_type"]]
        model.purge_info = ModelPurgeInfoToMongo.backward(instance.get("purge_info", {}))
        return model

    @staticmethod
    def map_model_backward(instance: dict) -> Model:
        """
        Maps the model part of the instance backward to reduce code duplication between Model/OptimizedModel.
        """
        from iai_core.repos import DatasetRepo, ModelRepo, ModelStorageRepo, ProjectRepo
        from iai_core.repos.storage.binary_repos import ModelBinaryRepo

        workspace_id = IDToMongo.backward(instance["workspace_id"])
        project_id = IDToMongo.backward(instance["project_id"])
        model_storage_id = IDToMongo.backward(instance["model_storage_id"])
        project_identifier = ProjectIdentifier(workspace_id=workspace_id, project_id=project_id)
        model_storage_identifier = ModelStorageIdentifier(
            workspace_id=workspace_id, project_id=project_id, model_storage_id=model_storage_id
        )
        project_repo = ProjectRepo()
        model_repo = ModelRepo(model_storage_identifier)

        model_storage = ModelStorageRepo(project_identifier).get_by_id(model_storage_id)
        project_adapter = ProxyAdapter(proxy=lambda: project_repo.get_by_id(project_id), id=project_id)

        train_dataset_id = IDToMongo.backward(instance.get("train_dataset_id", ""))

        def get_train_dataset():
            dataset_storage = project_repo.get_by_id(project_id).get_training_dataset_storage()
            return DatasetRepo(dataset_storage.identifier).get_by_id(train_dataset_id)

        train_dataset_adapter = ProxyAdapter(proxy=get_train_dataset, id=train_dataset_id)

        previous_trained_revision_id = IDToMongo.backward(instance.get("previous_trained_revision_id", ""))
        previous_trained_revision_adapter = ProxyAdapter(
            proxy=lambda: model_repo.get_by_id(previous_trained_revision_id),
            id=previous_trained_revision_id,
        )

        previous_revision_id = IDToMongo.backward(instance.get("previous_revision_id", ""))
        previous_revision_adapter = ProxyAdapter(
            proxy=lambda: model_repo.get_by_id(previous_revision_id),
            id=previous_revision_id,
        )

        training_framework = TrainingFrameworkToMongo.backward(instance["training_framework"])

        model_binary_repo = ModelBinaryRepo(model_storage.identifier)
        weight_paths_data = instance.get("weight_paths", [])
        data_sources = {
            key: DataSource(repository=model_binary_repo, binary_filename=value) for key, value in weight_paths_data
        }
        if not instance.get("exportable_code_path", ""):
            exportable_code_adapter = None
        else:
            exportable_code_adapter = ExportableCodeAdapter(
                data_source=DataSource(
                    repository=model_binary_repo,
                    binary_filename=instance["exportable_code_path"],
                )
            )
        return Model.with_adapters(
            project_adapter=project_adapter,
            train_dataset_adapter=train_dataset_adapter,
            previous_trained_revision_adapter=previous_trained_revision_adapter,
            previous_revision_adapter=previous_revision_adapter,
            model_storage=model_storage,
            configuration=ModelConfigurationToMongo.backward(instance["configuration"], parameters=project_identifier),
            _id=IDToMongo.backward(instance["_id"]),
            creation_date=DatetimeToMongo.backward(instance["creation_date"]),
            performance=PerformanceToMongo.backward(instance.get("performance")),  # type: ignore[arg-type]
            tags=instance.get("tags", []),
            data_source_dict=data_sources,
            training_framework=training_framework,
            model_status=ModelStatus[instance.get("model_status", "SUCCESS")],
            model_format=ModelFormat[instance.get("model_format", "OPENVINO")],
            training_duration=instance.get("training_duration", 0.0),
            training_job_duration=instance.get("training_job_duration", 0.0),
            precision=[ModelPrecision[model_precision] for model_precision in instance.get("precision", [])],
            latency=instance.get("latency", 0),
            fps_throughput=instance.get("fps_throughput", 0),
            target_device=TargetDevice[instance.get("target_device", TargetDevice.UNSPECIFIED.name)],
            target_device_type=instance.get("target_device_type", "N/A"),
            exportable_code_adapter=exportable_code_adapter,
            size=instance.get("size"),
            version=instance.get("version", 1),
            ephemeral=False,
        )

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from iai_core_py.entities.evaluation_result import EvaluationPurpose, EvaluationResult
from iai_core_py.repos.mappers.mongodb_mapper_interface import IMapperSimple
from iai_core_py.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from iai_core_py.repos.mappers.mongodb_mappers.metrics_mapper import PerformanceToMongo
from iai_core_py.repos.mappers.mongodb_mappers.primitive_mapper import DatetimeToMongo

from geti_types import ProjectIdentifier


class EvaluationResultToMongo(IMapperSimple[EvaluationResult, dict]):
    """MongoDB mapper for `EvaluationResult` entities"""

    @staticmethod
    def forward(instance: EvaluationResult) -> dict:
        return {
            "_id": IDToMongo.forward(instance.id_),
            "model_storage_id": IDToMongo.forward(instance.model_storage_id),
            "model_id": IDToMongo.forward(instance.model_id),
            "dataset_storage_id": IDToMongo.forward(instance.dataset_storage_id),
            "ground_truth_dataset_id": IDToMongo.forward(instance.ground_truth_dataset_id),
            "prediction_dataset_id": IDToMongo.forward(instance.prediction_dataset_id),
            "creation_date": DatetimeToMongo.forward(instance.creation_date),
            "performance": PerformanceToMongo.forward(instance.performance),  # type: ignore
            "purpose": instance.purpose.name,
        }

    @staticmethod
    def backward(instance: dict) -> EvaluationResult:
        purpose = EvaluationPurpose[instance["purpose"].upper()]
        project_identifier = ProjectIdentifier(
            workspace_id=IDToMongo.backward(instance["workspace_id"]),
            project_id=IDToMongo.backward(instance["project_id"]),
        )
        return EvaluationResult(
            id_=IDToMongo.backward(instance["_id"]),
            project_identifier=project_identifier,
            model_storage_id=IDToMongo.backward(instance["model_storage_id"]),
            model_id=IDToMongo.backward(instance["model_id"]),
            dataset_storage_id=IDToMongo.backward(instance["dataset_storage_id"]),
            ground_truth_dataset=IDToMongo.backward(instance["ground_truth_dataset_id"]),
            prediction_dataset=IDToMongo.backward(instance["prediction_dataset_id"]),
            performance=PerformanceToMongo.backward(instance.get("performance")),  # type: ignore
            creation_date=DatetimeToMongo.backward(instance.get("creation_date")),
            purpose=purpose,
        )

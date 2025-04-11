# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.
from sc_sdk.entities.evaluation_result import EvaluationPurpose, EvaluationResult
from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperSimple
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from sc_sdk.repos.mappers.mongodb_mappers.metrics_mapper import PerformanceToMongo
from sc_sdk.repos.mappers.mongodb_mappers.primitive_mapper import DatetimeToMongo

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

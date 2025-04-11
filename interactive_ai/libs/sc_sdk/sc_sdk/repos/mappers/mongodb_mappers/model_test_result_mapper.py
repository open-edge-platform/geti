# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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

"""This module contains the MongoDB mapper for model test result related entities"""

from sc_sdk.entities.model_test_result import ModelTestResult, TestState
from sc_sdk.repos.mappers import IMapperSimple
from sc_sdk.repos.mappers.mongodb_mappers.evaluation_result_mapper import EvaluationResultToMongo
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from sc_sdk.repos.mappers.mongodb_mappers.metrics_mapper import PerformanceToMongo
from sc_sdk.repos.mappers.mongodb_mappers.primitive_mapper import DatetimeToMongo

from geti_types import ProjectIdentifier


class ModelTestResultToMongo(IMapperSimple[ModelTestResult, dict]):
    """MongoDB mapper for `ModelTestResultToMongo` entities"""

    @staticmethod
    def forward(instance: ModelTestResult) -> dict:
        mongo_dict = EvaluationResultToMongo.forward(instance)
        if instance.job_id is not None:
            mongo_dict["job_id"] = IDToMongo.forward(instance.job_id)
        mongo_dict["name"] = instance.name
        mongo_dict["state"] = instance.state.name
        mongo_dict["dataset_storage_ids"] = [IDToMongo.forward(ds_id) for ds_id in instance.dataset_storage_ids]
        return mongo_dict

    @staticmethod
    def backward(instance: dict) -> ModelTestResult:
        # Get reference ids
        model_storage_id = IDToMongo.backward(instance["model_storage_id"])
        model_id = IDToMongo.backward(instance["model_id"])
        dataset_storage_ids = [IDToMongo.backward(id_) for id_ in instance["dataset_storage_ids"]]
        workspace_id = IDToMongo.backward(instance["workspace_id"])
        project_id = IDToMongo.backward(instance["project_id"])

        project_identifier = ProjectIdentifier(workspace_id=workspace_id, project_id=project_id)

        # Set optional ids
        job_id_ = instance.get("job_id", None)
        job_id = IDToMongo.backward(job_id_) if job_id_ is not None else None

        ground_truth_dataset_id_ = instance.get("ground_truth_dataset_id", None)
        ground_truth_dataset_id = (
            IDToMongo.backward(ground_truth_dataset_id_) if ground_truth_dataset_id_ is not None else None
        )

        prediction_dataset_id_ = instance.get("prediction_dataset_id", None)
        prediction_dataset_id = (
            IDToMongo.backward(prediction_dataset_id_) if prediction_dataset_id_ is not None else None
        )

        return ModelTestResult(
            id_=IDToMongo.backward(instance["_id"]),
            name=instance["name"],
            project_identifier=project_identifier,
            model_storage_id=model_storage_id,
            model_id=model_id,
            dataset_storage_ids=dataset_storage_ids,
            state=TestState[instance["state"]],
            job_id=job_id,
            performance=PerformanceToMongo.backward(instance.get("performance")),  # type: ignore
            ground_truth_dataset=ground_truth_dataset_id,
            prediction_dataset=prediction_dataset_id,
            creation_date=DatetimeToMongo.backward(instance["creation_date"]),
        )

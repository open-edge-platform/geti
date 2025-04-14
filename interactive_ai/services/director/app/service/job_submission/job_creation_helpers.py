# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains dataclasses and helper functions to easily create metadata and payloads for the jobs client"""

import json
import logging
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum, auto

from communication.exceptions import JobCreationFailedException

from geti_types import ID, ProjectIdentifier
from sc_sdk.entities.dataset_storage import DatasetStorage
from sc_sdk.entities.model import Model, ModelOptimizationType
from sc_sdk.entities.model_storage import ModelStorage
from sc_sdk.entities.model_test_result import ModelTestResult
from sc_sdk.entities.project import Project
from sc_sdk.entities.task_node import TaskNode
from sc_sdk.services import ModelService

logger = logging.getLogger(__name__)

TRAIN_JOB_PRIORITY = 1
OPTIMIZE_JOB_PRIORITY = 1
MODEL_TEST_JOB_PRIORITY = 1

TRAIN_JOB_REQUIRED_GPUS = 1


class JobDuplicatePolicy(str, Enum):
    REPLACE = auto()
    OMIT = auto()
    REJECT = auto()


class JobType(str, Enum):
    TRAIN = "train"
    OPTIMIZE_POT = "optimize_pot"
    MODEL_TEST = "test"


class JobName(str, Enum):
    TRAIN = "Training"
    OPTIMIZE = "Optimization"
    MODEL_TEST = "Model testing"


def get_model_storage_for_task(
    project_identifier: ProjectIdentifier,
    task_node_id: ID,
    model_storage: ModelStorage | None = None,
) -> ModelStorage:
    """
    Returns the model storage to be used for training the task.

    If `model_storage` = None (the default), the active model storage for the task
    node to be trained is returned.
    If a `model_storage` is passed, this method validates that the model storage
    belongs to the task node

    :param project_identifier: Identifier of the project containing the task node
    :param task_node_id: ID of the task node relative to the model storage
    :param model_storage: Optional ModelStorage instance to validate
    :raises JobCreationFailedException: if the model_storage passed does not belong to
        the task_node
    :return: ModelStorage instance to use for training the task
    """
    if model_storage is None:
        model_storage = ModelService.get_active_model_storage(
            project_identifier=project_identifier,
            task_node_id=task_node_id,
        )
    if model_storage.task_node_id != task_node_id:
        raise JobCreationFailedException(
            f"The task node of the model storage and the task node for which the train "
            f"job was requested do not match. "
            f"Model Storage ID: `{model_storage.id_}`, "
            f"Model Storage's Task Node ID: `{model_storage.task_node_id}`, "
            f"Request's Task Node ID: `{task_node_id}`."
        )
    return model_storage


def _serialize_job_key(job_key: dict) -> str:
    """
    Returns the job's key (represented as a dictionary) to a serialized string.

    :param job_key: dict instance to serialize
    :returns: string representation of the dict
    """
    return json.dumps(OrderedDict(sorted(job_key.items())))


@dataclass
class TrainTaskJobData:
    """
    Helper dataclass to generate payload and metadata for a training job.
    """

    model_storage: ModelStorage
    project: Project
    task_node: TaskNode
    activate_model_storage: bool
    from_scratch: bool
    workspace_id: ID
    max_training_dataset_size: int | None
    dataset_storage: DatasetStorage
    hyper_parameters_id: ID | None
    min_annotation_size: int | None = None
    max_number_of_annotations: int | None = None
    reshuffle_subsets: bool = False
    keep_mlflow_artifacts: bool = False

    @property
    def job_type(self) -> str:
        return JobType.TRAIN.value

    @property
    def job_name(self) -> str:
        return JobName.TRAIN.value

    def create_key(self) -> str:
        job_key = {
            "workspace_id": self.workspace_id,
            "project_id": self.project.id_,
            "type": self.job_type,
            "task_id": self.task_node.id_,
        }
        if self.model_storage is not None:
            job_key["model_storage_id"] = self.model_storage.id_
        return _serialize_job_key(job_key)

    def create_payload(self) -> dict:
        """
        Return the payload for the training job.

        :returns: a dict representing the job payload
        """
        return {
            "project_id": str(self.project.id_),
            "task_id": str(self.task_node.id_),
            "from_scratch": self.from_scratch,
            "should_activate_model": self.activate_model_storage,
            "infer_on_pipeline": True,
            "model_storage_id": str(self.model_storage.id_),
            "hyper_parameters_id": (str(self.hyper_parameters_id) if self.hyper_parameters_id else ""),
            # NOTE: By CVS-147120, we fix this value to true always to remove feature flag.
            # However, leaving this flag itself can make it easier to debug the future problem (e.g., CVS-142877).
            # You can still launch the job with `enable_training_from_dataset_shard=False` from Flyte console.
            "enable_training_from_dataset_shard": True,
            "max_training_dataset_size": self.max_training_dataset_size,
            "min_annotation_size": self.min_annotation_size,
            "max_number_of_annotations": self.max_number_of_annotations,
            "reshuffle_subsets": self.reshuffle_subsets,
            "keep_mlflow_artifacts": self.keep_mlflow_artifacts,
        }

    def create_metadata(self) -> dict:
        """
        Returns a dictionary representing the metadata for a training job.

        :return: dict with the job's metadata
        """
        model_template = self.model_storage.model_template
        metadata: dict = {
            "project": {
                "id": self.project.id_,
                "name": self.project.name,
            },
            "task": {
                "task_id": self.task_node.id_,
                "name": self.task_node.title,
                "model_template_id": model_template.model_template_id,
                "model_architecture": model_template.name,
                "dataset_storage_id": self.dataset_storage.id_,
            },
        }
        return metadata


@dataclass
class ModelTestJobData:
    """
    Helper dataclass to generate payload and metadata for a model testing job.
    """

    workspace_id: ID
    project: Project
    dataset_storage: DatasetStorage
    model_test_result: ModelTestResult
    model: Model
    model_storage: ModelStorage
    is_local_anomaly_test: bool
    task_node: TaskNode
    min_annotation_size: int | None = None
    max_number_of_annotations: int | None = None

    @property
    def job_type(self) -> str:
        return JobType.MODEL_TEST.value

    @property
    def job_name(self) -> str:
        return JobName.MODEL_TEST.value

    def create_key(self) -> str:
        job_key = {
            "workspace_id": self.workspace_id,
            "project_id": self.project.id_,
            "type": self.job_type,
            "model_id": self.model.id_,
            "dataset_storage_id": self.dataset_storage.id_,
        }
        if self.model_storage is not None:
            job_key["model_storage_id"] = self.model_storage.id_
        return _serialize_job_key(job_key)

    def create_payload(
        self,
    ) -> dict:
        """
        Return the payload for the model testing job.

        :returns: a dict representing the job payload
        """
        return {
            "project_id": self.project.id_,
            "model_test_result_id": self.model_test_result.id_,
            "is_local_anomaly_test": self.is_local_anomaly_test,
            "min_annotation_size": self.min_annotation_size,
            "max_number_of_annotations": self.max_number_of_annotations,
        }

    def create_metadata(self) -> dict:
        """
        Returns a dictionary representing the metadata for a model test job.

        :return: dict with the job's metadata
        """
        dataset_storage = self.dataset_storage
        model_template = self.model.model_storage.model_template
        return {
            "project": {
                "id": self.project.id_,
                "name": self.project.name,
            },
            "task": {
                "task_id": self.task_node.id_,
            },
            "test": {
                "model_template_id": model_template.model_template_id,
                "model_architecture": model_template.name,
                "datasets": [{"id": dataset_storage.id_, "name": dataset_storage.name}],
                "model": {
                    "architecture": model_template.name,
                    "template_id": model_template.model_template_id,
                    "id": self.model.id_,
                    "optimization_type": self.model.optimization_type.name,
                    "precision": [p.name for p in self.model.precision],
                    "has_xai_head": self.model.has_xai_head,
                },
            },
        }


@dataclass
class OptimizationJobData:
    workspace_id: ID
    project: Project
    training_dataset_storage: DatasetStorage
    model: Model
    optimization_type: ModelOptimizationType
    optimization_parameters: dict
    min_annotation_size: int | None = None
    max_number_of_annotations: int | None = None

    @property
    def job_type(self) -> str:
        return JobType.OPTIMIZE_POT.value

    @property
    def job_name(self) -> str:
        return JobName.OPTIMIZE.value

    @property
    def gpu_num_required(self) -> int | None:
        return None

    def create_key(self) -> str:
        job_key = {
            "workspace_id": self.workspace_id,
            "project_id": self.project.id_,
            "dataset_storage_id": self.training_dataset_storage.id_,
            "model_storage_id": self.model.model_storage.id_,
            "type": self.job_type,
            "optimization_parameters": self.optimization_parameters,
        }
        return _serialize_job_key(job_key)

    def create_payload(self) -> dict:
        """
        Returns a dictionary representing the payload for a model test job.

        :return: dict with the job's metadata
        """
        return {
            "project_id": self.project.id_,
            "dataset_storage_id": self.training_dataset_storage.id_,
            "model_storage_id": self.model.model_storage.id_,
            "model_id": self.model.id_,
            # NOTE: By CVS-147120, we fix this value to true always to remove feature flag.
            # However, leaving this flag itself can make it easier to debug the future problem (e.g., CVS-142877).
            # You can still launch the job with `enable_optimize_from_dataset_shard=False` from Flyte console.
            "enable_optimize_from_dataset_shard": True,
            "min_annotation_size": self.min_annotation_size,
            "max_number_of_annotations": self.max_number_of_annotations,
        }

    def create_metadata(self) -> dict:
        """
        Returns a dictionary representing the metadata for a model test job.

        :return: dict with the job's metadata
        """
        model_template = self.model.model_storage.model_template
        return {
            "project": {
                "id": self.project.id_,
                "name": self.project.name,
            },
            "task": {
                "task_id": self.model.model_storage.task_node_id,
                "model_template_id": model_template.model_template_id,
                "model_architecture": model_template.name,
            },
            "model_storage_id": self.model.model_storage.id_,
            "base_model_id": self.model.id_,
            "optimization_type": self.optimization_type.name,
            "optimized_model_id": None,
        }

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains dataclasses and helper functions to easily create metadata and payloads for the jobs client"""

import json
import logging
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum, auto

from geti_types import ID
from iai_core_py.entities.dataset_storage import DatasetStorage
from iai_core_py.entities.model_storage import ModelStorage
from iai_core_py.entities.project import Project
from iai_core_py.entities.task_node import TaskNode

logger = logging.getLogger(__name__)

TRAIN_JOB_PRIORITY = 1

TRAIN_JOB_REQUIRED_GPUS = 1


class JobDuplicatePolicy(str, Enum):
    REPLACE = auto()
    OMIT = auto()
    REJECT = auto()


class JobType(str, Enum):
    TRAIN = "train"


class JobName(str, Enum):
    TRAIN = "Training"


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

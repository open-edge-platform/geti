# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from jobs_common.exceptions import CommandInternalError
from sc_sdk.entities.model_storage import ModelStorage
from sc_sdk.entities.project import Project
from sc_sdk.entities.task_node import TaskNode


def _get_task_node(model_storage: ModelStorage, project: Project) -> TaskNode:
    """
    This function tries to find a TaskNode for the model in the job by
    comparing model storages. If a TaskNode can not be found a
    CommandInternalError is raised
    """
    for task_node in project.get_trainable_task_nodes():
        if task_node.id_ == model_storage.task_node_id:
            return task_node
    raise CommandInternalError(f"Could not find a TaskNode for the passed model storage with ID {model_storage.id_}")

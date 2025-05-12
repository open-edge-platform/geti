# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
Database repo helpers
"""

from iai_core.entities.model_storage import ModelStorage
from iai_core.entities.project import Project
from iai_core.entities.task_node import NullTaskNode, TaskNode


def get_task_node_for_model_storage(model_storage: ModelStorage, project: Project) -> TaskNode:
    """
    Get the trainable task node for the model storage

    :param model_storage: model storage object
    :param project: project through which the model storage was created
    :return: trainable task node linked to the given model storage
    """
    # Find the task in the project that this model storage is connected to
    for task_node in project.get_trainable_task_nodes():
        if task_node.id_ == model_storage.task_node_id:
            return task_node
    return NullTaskNode()

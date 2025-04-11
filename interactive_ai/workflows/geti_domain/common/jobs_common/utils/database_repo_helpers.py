# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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
"""
Database repo helpers
"""

from sc_sdk.entities.model_storage import ModelStorage
from sc_sdk.entities.project import Project
from sc_sdk.entities.task_node import NullTaskNode, TaskNode


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

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

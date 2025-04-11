# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

"""This file defines the ActiveModelState class"""

from sc_sdk.entities.model_storage import ModelStorage, NullModelStorage
from sc_sdk.entities.persistent_entity import PersistentEntity

from geti_types import ID


class ActiveModelState(PersistentEntity):
    """
    ActiveModelState keeps track of the active model storage of a task node.

    The active model storage is the default model storage used for a task, when a model
    storage is not provided for a job or process.

    DatasetItemCount uses the same ID of the corresponding task node, which makes it
    a per-task singleton from the logical point of view.

    :param task_node_id: ID of the task node
    :param active_model_storage: ModelStorage of the active model of the task node
    """

    def __init__(
        self,
        task_node_id: ID,
        active_model_storage: ModelStorage,
        ephemeral: bool = True,
    ) -> None:
        super().__init__(id_=task_node_id, ephemeral=ephemeral)
        self._task_node_id = task_node_id
        self.active_model_storage = active_model_storage

    @property
    def task_node_id(self) -> ID:
        """Get the task node id."""
        return self._task_node_id

    def __repr__(self) -> str:
        return f"ActiveModelState(task_node_id={self.task_node_id}, active_model_storage={self.active_model_storage})"


class NullActiveModelState(ActiveModelState):
    """
    NullActiveModelState represents an ActiveModelState not found.
    """

    def __init__(self) -> None:
        super().__init__(
            task_node_id=ID(),
            active_model_storage=NullModelStorage(),
            ephemeral=False,
        )

    def __repr__(self) -> str:
        return "NullActiveModelState()"

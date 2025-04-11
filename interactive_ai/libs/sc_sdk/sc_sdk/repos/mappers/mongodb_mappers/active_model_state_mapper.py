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

"""This module contains the MongoDB mapper for active model state related entities"""

from sc_sdk.entities.active_model_state import ActiveModelState
from sc_sdk.repos.mappers.mongodb_mapper_interface import IMapperForward, IMapperProjectIdentifierBackward
from sc_sdk.repos.mappers.mongodb_mappers.id_mapper import IDToMongo

from geti_types import ProjectIdentifier


class ActiveModelStateToMongo(
    IMapperForward[ActiveModelState, dict],
    IMapperProjectIdentifierBackward[ActiveModelState, dict],
):
    """MongoDB mapper for `ActiveModelState` entities"""

    @staticmethod
    def forward(instance: ActiveModelState) -> dict:
        return {
            "_id": IDToMongo.forward(instance.id_),
            "active_model_storage_id": IDToMongo.forward(instance.active_model_storage.id_),
        }

    @staticmethod
    def backward(instance: dict, project_identifier: ProjectIdentifier) -> ActiveModelState:
        from sc_sdk.repos import ModelStorageRepo

        active_model_storage_id = IDToMongo.backward(instance["active_model_storage_id"])
        active_model_storage = ModelStorageRepo(project_identifier).get_by_id(active_model_storage_id)
        return ActiveModelState(
            # note: the id of an ActiveModelState matches the one of its TaskNode
            task_node_id=IDToMongo.backward(instance["_id"]),
            active_model_storage=active_model_storage,
            ephemeral=False,
        )

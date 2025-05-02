# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the MongoDB mapper for active model state related entities"""

from iai_core_py.entities.active_model_state import ActiveModelState
from iai_core_py.repos.mappers.mongodb_mapper_interface import IMapperForward, IMapperProjectIdentifierBackward
from iai_core_py.repos.mappers.mongodb_mappers.id_mapper import IDToMongo

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
        from iai_core_py.repos import ModelStorageRepo

        active_model_storage_id = IDToMongo.backward(instance["active_model_storage_id"])
        active_model_storage = ModelStorageRepo(project_identifier).get_by_id(active_model_storage_id)
        return ActiveModelState(
            # note: the id of an ActiveModelState matches the one of its TaskNode
            task_node_id=IDToMongo.backward(instance["_id"]),
            active_model_storage=active_model_storage,
            ephemeral=False,
        )

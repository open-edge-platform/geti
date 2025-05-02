#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the MongoDB mapper for Project entities"""

from iai_core_py.adapters.adapter import ProxyAdapter
from iai_core_py.entities.keypoint_structure import KeypointEdge, KeypointPosition, KeypointStructure
from iai_core_py.entities.project import Project
from iai_core_py.repos.mappers.mongodb_mapper_interface import IMapperBackward, IMapperForward, IMapperSimple
from iai_core_py.repos.mappers.mongodb_mappers.id_mapper import IDToMongo
from iai_core_py.repos.mappers.mongodb_mappers.primitive_mapper import DatetimeToMongo
from iai_core_py.repos.mappers.mongodb_mappers.project_performance_mapper import ProjectPerformanceToMongo
from iai_core_py.repos.mappers.mongodb_mappers.task_graph_mapper import TaskGraphToMongo
from iai_core_py.utils.feature_flags import FeatureFlagProvider

from geti_types import ProjectIdentifier

FEATURE_FLAG_KEYPOINT_DETECTION = "FEATURE_FLAG_KEYPOINT_DETECTION"


class ProjectToMongo(
    IMapperForward[Project, dict],
    IMapperBackward[Project, dict],
):
    """MongoDB mapper for `Project` entities"""

    @staticmethod
    def forward(instance: Project) -> dict:
        project_dict = {
            "_id": IDToMongo.forward(instance.id_),
            "name": instance.name,
            "creator_id": instance.creator_id,
            "description": instance.description,
            "creation_date": DatetimeToMongo.forward(instance.creation_date),
            "user_names": instance.user_names,
            "task_graph": TaskGraphToMongo.forward(instance.task_graph),
            "performance": ProjectPerformanceToMongo.forward(instance.performance),
            "workspace_id": IDToMongo.forward(instance.workspace_id),
            "dataset_storage_ids": [IDToMongo.forward(id_) for id_ in instance.dataset_storage_ids],
            "training_dataset_storage_id": IDToMongo.forward(instance.training_dataset_storage_id),
            "hidden": instance.hidden,
            "project_type": instance.get_project_type(),
        }
        if FeatureFlagProvider.is_enabled(FEATURE_FLAG_KEYPOINT_DETECTION) and instance.keypoint_structure:
            project_dict["keypoint_structure"] = KeypointStructureToMongo.forward(instance.keypoint_structure)
        return project_dict

    @staticmethod
    def backward(instance: dict) -> Project:
        from iai_core_py.adapters.task_graph_adapter import TaskGraphAdapter
        from iai_core_py.repos import DatasetStorageRepo

        project_id = IDToMongo.backward(instance["_id"])
        workspace_id = IDToMongo.backward(instance["workspace_id"])
        project_identifier = ProjectIdentifier(workspace_id=workspace_id, project_id=project_id)
        creation_date = DatetimeToMongo.backward(instance.get("creation_date"))

        task_graph_adapter = TaskGraphAdapter(
            mapper=TaskGraphToMongo,
            project_identifier=project_identifier,
            data=instance["task_graph"],
        )
        dataset_storage_ids = [
            IDToMongo.backward(str_id)
            for str_id in instance.get("dataset_storage_ids", [instance.get("dataset_storage_id", "")])
        ]
        training_dataset_storage_id = IDToMongo.backward(
            instance.get("training_dataset_storage_id", instance.get("dataset_storage_id", ""))
        )
        project_performance = ProjectPerformanceToMongo.backward(instance["performance"])

        ds_repo = DatasetStorageRepo(project_identifier)
        training_dataset_storage_adapter = ProxyAdapter(
            id=training_dataset_storage_id,
            proxy=lambda: ds_repo.get_by_id(training_dataset_storage_id),
        )

        dataset_storage_adapters = []
        for dataset_storage_id in dataset_storage_ids:
            dataset_storage_adapters.append(
                ProxyAdapter(
                    id=dataset_storage_id,
                    proxy=lambda ds_id=dataset_storage_id: ds_repo.get_by_id(ds_id),  # type: ignore
                )
            )

        keypoint_structure = None
        if FeatureFlagProvider.is_enabled(FEATURE_FLAG_KEYPOINT_DETECTION) and instance.get("keypoint_structure", {}):
            keypoint_structure = KeypointStructureToMongo.backward(instance["keypoint_structure"])

        return Project.with_adapters(
            training_dataset_storage_adapter=training_dataset_storage_adapter,
            dataset_storage_adapters=dataset_storage_adapters,  # type: ignore
            name=instance["name"],
            id=project_id,
            creator_id=instance.get("creator_id", "Unknown"),
            description=instance["description"],
            user_names=instance.get("user_names", []),
            creation_date=creation_date,
            project_performance=project_performance,
            task_graph_adapter=task_graph_adapter,
            hidden=instance.get("hidden", False),
            keypoint_structure=keypoint_structure,
            ephemeral=False,
        )


class KeypointStructureToMongo(IMapperSimple[KeypointStructure, dict]):
    """MongoDB mapper for `KeypointStructure` entities"""

    @staticmethod
    def forward(instance: KeypointStructure) -> dict:
        return {
            "edges": [
                {"nodes": [IDToMongo.forward(edge.node_1), IDToMongo.forward(edge.node_2)]} for edge in instance._edges
            ],
            "positions": [
                {"node": IDToMongo.forward(position.node), "x": position.x, "y": position.y}
                for position in instance._positions
            ],
        }

    @staticmethod
    def backward(instance: dict) -> KeypointStructure:
        edges = [
            KeypointEdge(IDToMongo.backward(edge["nodes"][0]), IDToMongo.backward(edge["nodes"][1]))
            for edge in instance["edges"]
        ]
        positions = [
            KeypointPosition(IDToMongo.backward(position["node"]), position["x"], position["y"])
            for position in instance["positions"]
        ]
        return KeypointStructure(edges=edges, positions=positions)

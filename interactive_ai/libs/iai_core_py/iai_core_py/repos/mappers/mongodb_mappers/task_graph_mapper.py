#
# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

"""This module contains the MongoDB mapper for task graph related entities"""

from dataclasses import dataclass

from iai_core_py.entities.graph import Graph
from iai_core_py.entities.task_graph import TaskEdge, TaskGraph
from iai_core_py.repos.mappers.mongodb_mapper_interface import (
    IMapperForward,
    IMapperParametricBackward,
    IMapperProjectIdentifierBackward,
)

from .id_mapper import IDToMongo
from geti_types import ID, ProjectIdentifier


@dataclass
class TaskEdgeToMongoParameters:
    """
    This class represents parameters that should be passed to the `TaskEdgeToMongo` .forward and .backward methods.
    """

    def __init__(self, task_map: dict) -> None:
        self.task_map = task_map


class TaskEdgeToMongo(
    IMapperForward[TaskEdge, dict],
    IMapperParametricBackward[TaskEdge, dict, TaskEdgeToMongoParameters],
):
    """MongoDB mapper for `TaskEdge` entities"""

    @staticmethod
    def forward(instance: TaskEdge) -> dict:
        return {
            "from_task_id": IDToMongo.forward(instance.from_task.id_),
            "to_task_id": IDToMongo.forward(instance.to_task.id_),
        }

    @staticmethod
    def backward(
        instance: dict,
        parameters: TaskEdgeToMongoParameters,
    ) -> TaskEdge:
        from_task_id = IDToMongo.backward(instance["from_task_id"])
        to_task_id = IDToMongo.backward(instance["to_task_id"])
        from_task = parameters.task_map.get(from_task_id, None)
        to_task = parameters.task_map.get(to_task_id, None)

        return TaskEdge(from_task=from_task, to_task=to_task)


class TaskGraphToMongo(IMapperForward[TaskGraph, dict], IMapperProjectIdentifierBackward[TaskGraph, dict]):
    """MongoDB mapper for `TaskGraph` entities"""

    @staticmethod
    def forward(instance: TaskGraph) -> dict:
        if not isinstance(instance, Graph):
            raise ValueError(f"Cannot store an instance of `{instance.__class__.__name__}` as a Graph")
        return {
            "pipeline_representation": instance.pipeline_representation,
            "nodes": [IDToMongo.forward(node.id_) for node in list(instance.nodes)],
            "edges": [TaskEdgeToMongo.forward(e) for e in list(instance.edges) if isinstance(e, TaskEdge)],
        }

    @staticmethod
    def backward(
        instance: dict,
        project_identifier: ProjectIdentifier,
    ) -> TaskGraph:
        from iai_core_py.repos import TaskNodeRepo

        task_node_repo = TaskNodeRepo(project_identifier)
        if "nodes" in instance:
            task_map = {
                ID(task_id): task_node_repo.get_by_id(IDToMongo.backward(task_id)) for task_id in instance["nodes"]
            }
            output = TaskGraph()
            for task in task_map.values():
                output.add_node(task)

            edge_parameters = TaskEdgeToMongoParameters(task_map)
            edges = [TaskEdgeToMongo.backward(e, parameters=edge_parameters) for e in instance["edges"]]
            for edge in edges:
                # Skip invalid edges. They might break the system
                if edge.from_task is not None and edge.to_task is not None:
                    output.add_task_edge(edge)
        else:
            output = TaskGraph()
            task_ids = instance.get("task_ids", [])
            for task_id in task_ids:
                output.add_node(task_node_repo.get_by_id(IDToMongo.backward(task_id)))
        return output

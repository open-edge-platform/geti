"""This module contains the implementation of the TaskGraphAdapter"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from iai_core_py.entities.interfaces.task_graph_adapter_interface import TaskGraphAdapterInterface
from iai_core_py.entities.task_graph import TaskGraph
from iai_core_py.repos.mappers.mongodb_mappers.task_graph_mapper import TaskGraphToMongo

from geti_types import ProjectIdentifier


class TaskGraphAdapter(TaskGraphAdapterInterface):
    """
    An adapter to lazy load the Task Graph.
    Deserialization of the graph is not needed upon loading a project.
    """

    def __init__(
        self,
        mapper: type[TaskGraphToMongo],
        project_identifier: ProjectIdentifier,
        data: dict,
    ) -> None:
        super().__init__(mapper, data)
        self.project_identifier = project_identifier
        self._graph: TaskGraph | None = None

    def __eq__(self, other: object):
        if not isinstance(other, TaskGraphAdapter):
            return False
        return self.mapper == other.mapper and self.data == other.data

    def __deserialize(self) -> TaskGraph:
        if self.mapper is None or self.data is None:
            raise ValueError("This task graph adapter has no mapper, nor does it have data assigned to de-serialize")

        return self.mapper.backward(self.data, project_identifier=self.project_identifier)

    @property
    def pipeline_representation(self) -> str:
        """
        Returns the pipeline representation string for a TaskGraph.
        E.g. "ImageDataset → Detection → Crop → Segmentation"

        :return: Representation string for TaskGraph
        """
        if self._graph is None:
            # Only return cached version if graph is not deserialized yet
            return self.data.get("pipeline_representation", "---")
        return self._graph.pipeline_representation

    @property
    def graph(self) -> TaskGraph:
        """
        Return the de-serialized graph.

        :return: TaskGraph entity
        """
        if self._graph is None:
            self._graph = self.__deserialize()
        return self._graph

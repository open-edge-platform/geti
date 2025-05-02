"""This module implements the TaskGraphAdapterInterface"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import abc

from iai_core_py.entities.task_graph import TaskGraph
from iai_core_py.repos.mappers.mongodb_mappers.task_graph_mapper import TaskGraphToMongo


class TaskGraphAdapterInterface(metaclass=abc.ABCMeta):
    """
    This interface describes how the Adapter looks like that allows an entity,
    such as a Project to fetch the TaskGraph lazily.
    """

    def __init__(self, mapper: type[TaskGraphToMongo], data: dict) -> None:
        self.mapper = mapper
        self.data: dict = data

    @property
    @abc.abstractmethod
    def graph(self) -> TaskGraph:
        """
        Return the de-serialized graph.

        :return: TaskGraph entity
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def pipeline_representation(self) -> str:
        """
        Returns the pipeline representation string for a TaskGraph.
        E.g. "ImageDataset → Detection → Crop → Segmentation"

        :return: Representation string for TaskGraph
        """
        raise NotImplementedError

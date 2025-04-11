"""This module implements the TaskGraphAdapterInterface"""

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

import abc

from sc_sdk.entities.task_graph import TaskGraph
from sc_sdk.repos.mappers.mongodb_mappers.task_graph_mapper import TaskGraphToMongo


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

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

"""This module implements the TaskGraph entity"""

from sc_sdk.entities.graph import Graph
from sc_sdk.entities.task_node import TaskNode

from geti_types import ID


class TaskEdge:
    """
    TaskEdge defines a connection between to tasks, defining their from and to tasks as well as the ports used for gRPC.
    """

    def __init__(self, from_task: TaskNode, to_task: TaskNode) -> None:
        self.from_task = from_task
        self.to_task = to_task

    def __repr__(self) -> str:
        return f"TaskEdge({self.from_task.title} -> {self.to_task.title})"


class TaskGraph(Graph):
    """
    Defines the relations between TaskNode in a task chain as a directed graph.
    """

    def __init__(self) -> None:
        super().__init__(directed=True)

    def __repr__(self) -> str:
        return f"TaskGraph({self.tasks})"

    def __eq__(self, other: object):
        if not isinstance(other, TaskGraph):
            return False
        return self.task_ids == other.task_ids

    @property
    def task_ids(self) -> list[ID]:
        """
        Returns IDs of all the TaskNodes in the graph
        """
        output = []
        for node in list(self._graph.nodes):
            output.append(node.id_)
        return output

    @property
    def pipeline_representation(self) -> str:
        """
        This method generates a pipeline representation string from the task graph.
        It is always called by the mongodb mapper (forward) to ensure a correct description

        :return: pipeline representation string
        """
        try:
            result = " → ".join([t.title for t in self.ordered_tasks])
        except KeyError:
            # Todo: make self. ordered_tasks stable. It can raise exceptions for a graph that is not updated
            # (edges to old nodes, etc.)
            result = " → ".join([t.title for t in self.tasks])
        return result

    @property
    def ordered_tasks(self) -> tuple[TaskNode, ...]:
        """
        Returns the tasks in a read-only tuple, first to last.
        """

        # this strategy assumes no merge
        def _get_following_tasks_recursive(task: TaskNode | None = None):
            following_tasks = self.first_tasks() if task is None else self.get_immediate_following_tasks(task)
            output_: list[TaskNode] = []
            for task_ in following_tasks:
                output_.extend(_get_following_tasks_recursive(task_))
            output_ = following_tasks + output_
            return tuple(output_)

        return tuple(_get_following_tasks_recursive())

    @property
    def tasks(self) -> list[TaskNode]:
        return list(self._graph.nodes)

    def add_task_edge(self, task_edge: TaskEdge) -> None:
        """
        Adds an edge (relation) between to tasks in the graph.
        :param task_edge: the TaskEdge
        """
        if task_edge.from_task is None or task_edge.to_task is None:
            # Skip edges to nothing
            return
        self.add_edge(task_edge.from_task, task_edge.to_task)

    @property
    def edges(self) -> list[TaskEdge]:
        """
        Returns all the edges (relations) between tasks in the graph.
        """
        all_edges = self._graph.edges(keys=True, data=True)
        output = []
        for edge in all_edges:
            if len(edge) < 4:
                # Skip invalid edges
                continue
            from_task = edge[0]
            to_task = edge[1]
            edge_data = edge[3]
            if not isinstance(edge_data, dict):
                # Skip invalid edges
                continue
            output.append(TaskEdge(from_task=from_task, to_task=to_task))

        return output

    def get_immediate_following_tasks(self, task: TaskNode) -> list[TaskNode]:
        """
        Returns all tasks that come immediately after `task` in the task chain (downstream tasks).
        :return: the immediate downstream tasks if present
        """
        return [edge[1] for edge in self.find_out_edges(task)]

    def get_immediate_previous_tasks(self, task: TaskNode) -> list[TaskNode]:
        """
        Returns all tasks that come immediately before `task` in the task chain (upstream tasks).
        :return: the immediate upstream tasks if present
        """
        return [edge[0] for edge in self.find_in_edges(task)]

    def first_tasks(self) -> list[TaskNode]:
        """
        Returns the root tasks (entry points in the task chain) in the graph. These are the tasks where the processing
        begins.
        :return: one or more entry point of the task chain
        """
        output = []
        for node in self._graph.nodes:
            if len(self.get_immediate_previous_tasks(node)) == 0:
                output.append(node)
        return output


class NullTaskGraph(TaskGraph):
    """Representation of a TaskGraph 'TaskGraph not found'"""

    def __repr__(self) -> str:
        return "NullTaskGraph()"

    @property
    def task_ids(self) -> list[ID]:
        return []

    @property
    def tasks(self) -> list[TaskNode]:
        return []

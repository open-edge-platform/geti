# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from iai_core.entities.task_graph import TaskGraph
from iai_core.entities.task_node import TaskNode, TaskProperties

from geti_types import ID


@pytest.fixture
def fxt_task_node_numeric(fxt_mongo_id, fxt_model_template_classification):
    def _build_task(index: int) -> TaskNode:
        return TaskNode(
            title=f"Task {index}",
            task_properties=TaskProperties.from_model_template(fxt_model_template_classification),
            project_id=ID(fxt_mongo_id(100)),
            id_=ID(fxt_mongo_id(index)),
        )

    yield _build_task


class TestTaskGraph:
    def test_task_graph_dummy(self, fxt_task_node_numeric) -> None:
        """
        <b>Description:</b>
        Check that a TaskGraph can be correctly traversed

        <b>Input data:</b>
        A graph with two edges and three nodes

        <b>Expected results:</b>
        Test passes if the previous and following tasks return the expected values

        <b>Steps</b>
        1. Create TaskGraph instance
        2. Check previous and following tasks
        """
        task_graph = TaskGraph()
        node1 = fxt_task_node_numeric(1)
        node2 = fxt_task_node_numeric(2)
        node3 = fxt_task_node_numeric(3)
        task_graph.add_edge(node1, node2)
        task_graph.add_edge(node2, node3)
        assert task_graph.directed
        assert [node1] == task_graph.get_immediate_previous_tasks(node2)
        assert [node2] == task_graph.get_immediate_previous_tasks(node3)
        assert [node3] == task_graph.get_immediate_following_tasks(node2)
        assert [node2] == task_graph.get_immediate_following_tasks(node1)

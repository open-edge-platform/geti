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

import pytest

from sc_sdk.entities.task_graph import TaskGraph
from sc_sdk.entities.task_node import TaskNode, TaskProperties

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


@pytest.mark.ScSdkComponent
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

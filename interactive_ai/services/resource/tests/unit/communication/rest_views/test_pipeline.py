# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import copy
from unittest.mock import patch

import pytest
from testfixtures import compare

from communication.rest_views.pipeline import CONNECTIONS, TASKS, PipelineRESTViews

from iai_core.entities.label_schema import LabelSchema
from iai_core.entities.model_template import TaskType


class TestPipelineRESTViews:
    def test_task_node_to_rest_include_deleted_labels(
        self, fxt_task, fxt_label_schema, fxt_label, fxt_task_1_rest, fxt_label_rest
    ):
        """
        Tests task_node_to_rest with include_delete_labels=True
        """

        task_rest = copy.deepcopy(fxt_task_1_rest)
        task_rest["labels"] = [copy.deepcopy(fxt_label_rest)]
        task_rest["labels"][0]["is_deleted"] = False
        task_rest["labels"][0]["group"] = fxt_label_schema.get_group_containing_label(fxt_label).name

        task_rest["label_schema_id"] = fxt_label_schema.id_

        with patch.object(LabelSchema, "get_all_labels", return_value=[fxt_label]) as mock_get_labels:
            result = PipelineRESTViews.task_node_to_rest(
                node=fxt_task,
                task_label_schema=fxt_label_schema,
                include_deleted_labels=True,
            )

            mock_get_labels.assert_called_once_with()
        compare(result, task_rest, ignore_eq=True)

    @pytest.mark.parametrize(
        "fxt_task, fxt_task_rest",
        [
            ("fxt_keypoint_task", "fxt_keypoint_detection_task_rest"),
            ("fxt_classification_task", "fxt_classification_task_rest"),
        ],
        ids=["keypoint_detection", "classification"],
    )
    def test_task_node_to_rest(
        self,
        fxt_task,
        fxt_label_schema,
        fxt_task_rest,
        fxt_label,
        fxt_label_rest,
        fxt_keypoint_structure,
        fxt_keypoint_structure_rest,
        request,
    ):
        node = request.getfixturevalue(fxt_task)
        task_rest = copy.deepcopy(request.getfixturevalue(fxt_task_rest))
        task_rest["labels"] = [copy.deepcopy(fxt_label_rest)]
        task_rest["labels"][0]["group"] = fxt_label_schema.get_group_containing_label(fxt_label).name
        task_rest["label_schema_id"] = fxt_label_schema.id_
        keypoint_structure = None
        if node.task_properties.task_type == TaskType.KEYPOINT_DETECTION:
            task_rest["keypoint_structure"] = fxt_keypoint_structure_rest
            keypoint_structure = fxt_keypoint_structure
        with patch.object(LabelSchema, "get_all_labels", return_value=[fxt_label]):
            result = PipelineRESTViews.task_node_to_rest(
                node=node,
                task_label_schema=fxt_label_schema,
                keypoint_structure=keypoint_structure,
            )

        compare(result, task_rest, ignore_eq=True)

    def test_task_connection_to_rest(self, fxt_task_edge, fxt_task_edge_rest):
        result = PipelineRESTViews.task_connection_to_rest(edge=fxt_task_edge)

        compare(result, fxt_task_edge_rest, ignore_eq=True)

    def test_task_graph_to_rest(self, fxt_task_graph, fxt_task_graph_rest, fxt_label_schema):
        with (
            patch.object(PipelineRESTViews, "task_connection_to_rest", return_value={}) as mock_conn_rest,
            patch.object(PipelineRESTViews, "task_node_to_rest", return_value={}) as mock_node_rest,
        ):
            label_schema_per_task = {task_node.id_: fxt_label_schema for task_node in fxt_task_graph.tasks}

            result = PipelineRESTViews.task_graph_to_rest(
                graph=fxt_task_graph, label_schema_per_task=label_schema_per_task
            )

            mock_conn_rest.assert_called()
            mock_node_rest.assert_called()
        assert TASKS in result
        assert CONNECTIONS in result
        assert isinstance(result[TASKS], list)
        assert isinstance(result[CONNECTIONS], list)
        assert all(isinstance(task, dict) for task in result[TASKS])
        assert all(isinstance(conn, dict) for conn in result[CONNECTIONS])

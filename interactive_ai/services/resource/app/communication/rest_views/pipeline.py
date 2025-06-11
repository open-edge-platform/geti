# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from typing import TYPE_CHECKING, Any, cast

from communication.rest_views.keypoint_structure_rest_views import KeypointStructureRESTViews
from communication.rest_views.label_rest_views import LabelRESTViews

from geti_types import ID
from iai_core.entities.keypoint_structure import KeypointStructure
from iai_core.entities.label_schema import LabelSchemaView, NullLabelSchema
from iai_core.entities.task_graph import TaskEdge, TaskGraph
from iai_core.entities.task_node import TaskNode

if TYPE_CHECKING:
    from iai_core.entities.label import Label

ZERO = "0"
CONNECTIONS = "connections"
DATASET_2D = "DATASET_2D"
DATA_TYPE = "data_type"
FROM = "from"
ID_ = "id"
IS_DELETED = "is_deleted"
KEYPOINT_STRUCTURE = "keypoint_structure"
LABELS = "labels"
MODEL_TEMPLATE_ID = "model_template_id"
PORT_NAME = "port_name"
PROPERTIES = "properties"
TASKS = "tasks"
TASK_ID = "task_id"
TASK_NAME = "task_name"
TASK_TYPE = "task_type"
LABEL_SCHEMA_ID = "label_schema_id"
TITLE = "title"
TO = "to"
USER_VALUE = "user_value"
X = "x"
Y = "y"


class PipelineRESTViews:
    @staticmethod
    def task_node_to_rest(
        node: TaskNode,
        task_label_schema: LabelSchemaView | None = None,
        include_deleted_labels: bool = False,
        keypoint_structure: KeypointStructure | None = None,
    ) -> dict:
        """
        Returns a view of a TaskNode.

        :param node: the TaskNode object to convert
        :param task_label_schema: label schema (view) relative to the task.
            Note: the full label schema will be retrieved from the task one.
            The argument can be None for task nodes without labels.
        :param include_deleted_labels: whether to include deleted labels in the response
        :param keypoint_structure: the keypoint structure associated with the task
        :return: dict of rest representation of task node
        """

        output: dict[str, Any] = {
            ID_: str(node.id_),
            TITLE: node.title,
            TASK_TYPE: str(node.task_properties.task_type).lower(),
        }

        # For tasks with a label schema, include their labels in the REST view
        if task_label_schema and not isinstance(task_label_schema, NullLabelSchema):
            project_schema = task_label_schema.parent_schema
            if not include_deleted_labels:
                labels = [
                    LabelRESTViews.label_to_rest(
                        label=cast("Label", label),
                        label_schema=project_schema,
                    )
                    for label in task_label_schema.get_labels(include_empty=True)
                ]
            else:
                labels = [
                    LabelRESTViews.label_to_rest(
                        label=cast("Label", label),
                        label_schema=project_schema,
                    )
                    for label in task_label_schema.get_all_labels()
                ]
                for label in labels:
                    label[IS_DELETED] = ID(label[ID_]) in task_label_schema.deleted_label_ids
            if len(labels) > 0:
                output[LABELS] = labels
                output[LABEL_SCHEMA_ID] = str(task_label_schema.id_)

        if keypoint_structure and node.task_properties.is_trainable:
            output[KEYPOINT_STRUCTURE] = KeypointStructureRESTViews.keypoint_structure_to_rest(keypoint_structure)

        return output

    @staticmethod
    def task_connection_to_rest(edge: TaskEdge) -> dict:
        """
        Returns serialized dict
        :param edge: Edge in Graph
        :return: rest representation of task connection
        """
        return {FROM: str(edge.from_task.id_), TO: str(edge.to_task.id_)}

    @staticmethod
    def task_graph_to_rest(
        graph: TaskGraph,
        label_schema_per_task: dict[ID, LabelSchemaView],
        include_deleted_labels: bool = False,
        keypoint_structure: KeypointStructure | None = None,
    ) -> dict:
        """
        Converts TaskGraph object to rest representation of task graph

        :param graph: TaskGraph objects to convert
        :param label_schema_per_task: Dictionary mapping each task node (ID) to its
            own label schema (view). Tasks that don't have a schema can be mapped to
            None or not mapped at all.
        :param include_deleted_labels: Whether to include deleted labels in the output.
        :param keypoint_structure: the keypoint structure associated with the task
        :return: rest representation of task graph
        """
        connections = [PipelineRESTViews.task_connection_to_rest(edge) for edge in graph.edges]
        return {
            TASKS: [
                PipelineRESTViews.task_node_to_rest(
                    node=node,
                    task_label_schema=label_schema_per_task.get(node.id_),
                    include_deleted_labels=include_deleted_labels,
                    keypoint_structure=keypoint_structure,
                )
                for node in graph.tasks
            ],
            CONNECTIONS: connections,
        }

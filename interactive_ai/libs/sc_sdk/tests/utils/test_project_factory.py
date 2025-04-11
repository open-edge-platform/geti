"""This UnitTest tests ProjectFactory functionality"""

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

from sc_sdk.algorithms import ModelTemplateList
from sc_sdk.entities.project import Project
from sc_sdk.entities.task_graph import TaskEdge, TaskGraph
from sc_sdk.entities.task_node import TaskNode, TaskProperties, TaskType
from sc_sdk.repos import TaskNodeRepo
from sc_sdk.utils.project_factory import ProjectFactory
from tests.test_helpers import register_model_template

from geti_types import ID


@pytest.mark.ScSdkComponent
class TestProjectFactory:
    def test_create_project_single_task_with_model_template_id(self, request) -> None:
        """
        <b>Description:</b>
        Tests that a single task project is created properly

        <b>Input data:</b>
        Several model template IDs, like 'classification', 'detection', 'torch_segmentation'

        <b>Expected results:</b>
        The test passes if the created project has the correct properties, like label domain and task type, or a
        ValueError has been raised if the task is not recognized

        <b>Steps</b>
        1. Make model template IDs
        2. Create project using model template IDs
        3. Check that incorrect model template IDs raise a ValueError
        4. Check that label domains and task type are (correctly) set
        """
        task_type_to_test = [
            TaskType.CLASSIFICATION,
            TaskType.DETECTION,
            TaskType.SEGMENTATION,
        ]
        model_templates = []

        for i, task_type in enumerate(task_type_to_test):
            model_template_id = f"test_model_template_{i}"
            model_template = register_model_template(request, type(None), model_template_id, task_type=str(task_type))
            model_templates.append(model_template)

        # Create project using model template IDs
        for model_template in model_templates:
            model_template_id = model_template.model_template_id

            project = ProjectFactory.create_project_single_task(
                name=f"__Test_project_creation {model_template_id}",
                description="",
                creator_id="",
                labels=[
                    {"name": "label_one", "color": "#00ff00ff"},
                    {"name": "label_two", "color": "#0000ffff"},
                ],
                model_template_id=model_template_id,
            )
            training_task = project.tasks[-1]

            # Check that label domains and task type are (correctly) set
            task_type = training_task.task_properties.task_type
            assert task_type == model_template.task_type, f"Task type must be {model_template.task_type}"

    def test_create_project_with_task_graph(self) -> None:
        """
        <b>Description:</b>
        Tests that a project can be created from a task graph

        <b>Input data:</b>
        TaskGraph with dataset and torch_segmentation nodes

        <b>Expected results:</b>
        The test passes if the created project has the correct properties

        <b>Steps</b>
        1. Make TaskGraph
        2. Create Project
        3. Check that values are correct in the project
        """
        task_graph = TaskGraph()

        first_model_template = ModelTemplateList().get_by_id("dataset")
        first_task_node = TaskNode(
            title="img_dataset",
            task_properties=TaskProperties.from_model_template(first_model_template),
            project_id=ID(),
            id_=TaskNodeRepo.generate_id(),
        )
        second_model_template = ModelTemplateList().get_by_id("torch_segmentation")
        second_task_node = TaskNode(
            title="segmentation",
            task_properties=TaskProperties.from_model_template(second_model_template),
            project_id=ID(),
            id_=TaskNodeRepo.generate_id(),
        )
        task_graph.add_node(first_task_node)
        task_graph.add_node(second_task_node)
        task_edge = TaskEdge(from_task=first_task_node, to_task=second_task_node)
        task_graph.add_task_edge(task_edge)
        model_templates = [first_model_template, second_model_template]

        project = ProjectFactory.create_project_with_task_graph(
            name="Test_Graph_LabelSchema",
            creator_id="",
            description="test projectfactory",
            task_graph=task_graph,
            model_templates=model_templates,
        )

        assert project.task_graph == task_graph

    def test_save_pipeline_to_project(self, sample_project: Project) -> None:
        """
        <b>Description:</b>
        Tests that a pipeline can be saved to a project

        <b>Input data:</b>
        A sample project
        A new pipeline for a classification task

        <b>Expected results:</b>
        The test passes if the project has the new pipeline

        <b>Steps</b>
        1. Make the new pipeline
        3. Change the pipeline of the project
        4. Check that the pipeline was correctly changed
        """
        task_graph = TaskGraph()

        first_task_model_template = ModelTemplateList().get_by_id("dataset")
        first_task_node = TaskNode(
            title="img_dataset",
            task_properties=TaskProperties.from_model_template(first_task_model_template),
            project_id=ID(),
            id_=TaskNodeRepo.generate_id(),
        )
        second_task_model_template = ModelTemplateList().get_by_id("classification")
        second_task_node = TaskNode(
            title="classification",
            task_properties=TaskProperties.from_model_template(second_task_model_template),
            project_id=ID(),
            id_=TaskNodeRepo.generate_id(),
        )
        task_graph.add_node(first_task_node)
        task_graph.add_node(second_task_node)
        task_edge1 = TaskEdge(from_task=first_task_node, to_task=second_task_node)
        task_graph.add_task_edge(task_edge1)
        model_templates = [first_task_model_template, second_task_model_template]
        assert sample_project.task_graph != task_graph

        updated_project = ProjectFactory.save_pipeline_to_project(
            task_graph=task_graph,
            model_templates=model_templates,
            project=sample_project,
        )
        assert task_graph == updated_project.task_graph

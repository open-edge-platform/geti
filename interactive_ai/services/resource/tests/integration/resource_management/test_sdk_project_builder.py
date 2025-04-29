# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import copy
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest
from geti_spicedb_tools import SpiceDB
from jsonschema import ValidationError

from communication.exceptions import (
    BadNumberOfConnectionsException,
    DuplicateLabelNamesException,
    DuplicateTaskNamesException,
    MismatchingParentsInLabelGroupException,
    TooManyLabelsException,
)
from communication.rest_data_validator import ProjectRestValidator
from communication.rest_parsers import RestProjectParser, RestProjectUpdateParser
from communication.rest_views.label_rest_views import LabelRESTViews
from managers.project_manager import ProjectManager
from service.label_schema_service import LabelSchemaService

from geti_types import ID
from sc_sdk.algorithms import ModelTemplateList
from sc_sdk.entities.label_schema import LabelGroupType
from sc_sdk.entities.project import NullProject
from sc_sdk.repos import LabelSchemaRepo, ProjectRepo
from sc_sdk.utils.project_builder import ProjectBuilder, ProjectUpdateError

if TYPE_CHECKING:
    from sc_sdk.entities.label import Label


class TestProjectCRUD:
    @staticmethod
    def get_task_chain_project_dict() -> dict[str, Any]:
        return {
            "name": "test sc create project",
            "pipeline": {
                "connections": [
                    {"from": "Image Dataset", "to": "Object Detection"},
                    {"from": "Object Detection", "to": "Crop"},
                    {"from": "Crop", "to": "Shape Classification"},
                ],
                "tasks": [
                    {"title": "Image Dataset", "task_type": "dataset"},
                    {
                        "title": "Object Detection",
                        "task_type": "detection",
                        "labels": [
                            {
                                "name": "object",
                                "color": "#0021FFFF",
                                "group": "default detection group",
                            }
                        ],
                    },
                    {"title": "Crop", "task_type": "crop"},
                    {
                        "title": "Shape Classification",
                        "task_type": "classification",
                        "labels": [
                            {
                                "name": "rectangle",
                                "color": "#0015FFFF",
                                "group": "default classification group",
                                "parent_id": "object",
                            },
                            {
                                "name": "circle",
                                "color": "#7F000AFF",
                                "group": "default classification group",
                                "parent_id": "object",
                            },
                            {
                                "name": "triangle",
                                "color": "#16FF00FF",
                                "group": "default classification group",
                                "parent_id": "object",
                            },
                        ],
                    },
                ],
            },
        }

    @staticmethod
    def get_hierarchy_project_dict() -> dict[str, Any]:
        return {
            "name": "Test hierarchy classification project",
            "pipeline": {
                "connections": [{"from": "Dataset", "to": "Classification task"}],
                "tasks": [
                    {"task_type": "dataset", "title": "Dataset"},
                    {
                        "title": "Classification task",
                        "task_type": "classification",
                        "labels": [
                            {
                                "name": "1",
                                "color": "#edb200ff",
                                "group": "Group 1",
                                "parent_id": None,
                                "hotkey": "",
                            },
                            {
                                "name": "1.1",
                                "color": "#548fadff",
                                "group": "Group 1.X",
                                "parent_id": "1",
                                "hotkey": "",
                            },
                            {
                                "name": "1.1.1",
                                "color": "#00f5d4ff",
                                "group": "Group 1.1.X",
                                "parent_id": "1.1",
                                "hotkey": "",
                            },
                            {
                                "name": "1.1.2",
                                "color": "#5b69ffff",
                                "group": "Group 1.1.X",
                                "parent_id": "1.1",
                                "hotkey": "",
                            },
                            {
                                "name": "1.2",
                                "color": "#9d3b1aff",
                                "group": "Group 1.X",
                                "parent_id": "1",
                                "hotkey": "",
                            },
                            {
                                "name": "1.3",
                                "color": "#d7bc5eff",
                                "group": "Group 1.X",
                                "parent_id": "1",
                                "hotkey": "",
                            },
                            {
                                "name": "2",
                                "color": "#708541ff",
                                "group": "Group 2",
                                "parent_id": None,
                                "hotkey": "",
                            },
                            {
                                "name": "2.1",
                                "color": "#c9e649ff",
                                "group": "Group 2.X",
                                "parent_id": "2",
                                "hotkey": "",
                            },
                        ],
                    },
                ],
            },
        }

    @patch.object(SpiceDB, "create_project")
    @patch.object(SpiceDB, "delete_project")
    def test_create_project(self, mock_spicedb_create_project, mock_spicedb_delete_project, request) -> None:
        """
        <b>Description:</b>
        To test the creation of a project using pipeline data.

        <b>Expected results:</b>
        Test passes if the project is created successfully and reflects the pipeline data

        <b>Steps</b>
        1. Load a dictionary object which contains the pipeline data.
        2. Create a project using this data.
        3. Check if the project is created successfully.
        4. Check if the number of tasks in the project and the pipeline data are the same.
        5. Check if the task titles are the same in pipeline data and the project object.
        6. Check that label names from the dict are reflected in project.
        """
        project_repo: ProjectRepo = ProjectRepo()
        project_manager = ProjectManager()
        model_template_dataset = ModelTemplateList().get_by_id("dataset")
        model_template_detection = ModelTemplateList().get_by_id("detection")
        model_template_crop = ModelTemplateList().get_by_id("crop")
        model_template_classification = ModelTemplateList().get_by_id("classification")

        # pull project data
        project_data = self.get_task_chain_project_dict()

        # create project based on json data
        ProjectRestValidator().validate_creation_data_statically(project_data)
        with patch.object(
            ProjectBuilder,
            "get_default_model_template_by_task_type",
            side_effect=[
                model_template_dataset,
                model_template_detection,
                model_template_crop,
                model_template_classification,
                model_template_dataset,
                model_template_detection,
                model_template_crop,
                model_template_classification,
            ],
        ):
            project, _, _ = project_manager.create_project(
                creator_id="admin",
                workspace_id=ID("test_workspace"),
                project_parser=RestProjectParser,
                parser_kwargs={"rest_data": project_data},
            )
            request.addfinalizer(lambda: project_repo.delete_by_id(project.id_))

        # assert that the created project reflects the json definition
        assert not isinstance(project, NullProject)
        assert project.name == project_data["name"]
        assert len(project.tasks) == len(project_data["pipeline"]["tasks"])
        task_titles = {task.title for task in project.tasks}
        task_dict_titles = {task_dict["title"] for task_dict in project_data["pipeline"]["tasks"]}
        assert task_titles == task_dict_titles
        for task_dict in project_data["pipeline"]["tasks"]:
            title = task_dict["title"]
            task = next(task for task in project.tasks if task.title == title)

            if task.task_properties.is_trainable:
                task_labels = LabelSchemaService.get_latest_labels_for_task(
                    project_identifier=project.identifier,
                    task_node_id=task.id_,
                    include_empty=True,
                )
                project_label_names = {label.name for label in task_labels}
                dict_label_names = {label["name"] for label in task_dict["labels"]}
                # check issubset because empty labels are added during creation if not supplied
                assert dict_label_names.issubset(project_label_names)

    def test_create_project_invalid_data(self) -> None:
        valid_data = self.get_task_chain_project_dict()
        no_name = copy.deepcopy(valid_data)
        no_name.pop("name", None)

        extra_property = copy.deepcopy(valid_data)
        extra_property["pipeline"]["tasks"][0]["extra"] = "extra"

        label_is_empty = copy.deepcopy(valid_data)
        label_is_empty["pipeline"]["tasks"][1]["labels"][0]["is_empty"] = True

        too_many_labels = copy.deepcopy(valid_data)
        label = too_many_labels["pipeline"]["tasks"][1]["labels"][0]
        too_many_labels["pipeline"]["tasks"][1]["labels"] = [label for _ in range(1001)]

        duplicate_task_title = copy.deepcopy(valid_data)
        duplicate_task_title["pipeline"]["tasks"][1]["title"] = duplicate_task_title["pipeline"]["tasks"][0]["title"]

        duplicate_label_name = copy.deepcopy(valid_data)
        duplicate_label_name["pipeline"]["tasks"][3]["labels"][1]["name"] = duplicate_label_name["pipeline"]["tasks"][
            3
        ]["labels"][0]["name"]

        missing_connection = copy.deepcopy(valid_data)
        del missing_connection["pipeline"]["connections"][0]

        different_label_parents_in_same_group = copy.deepcopy(valid_data)
        different_label_parents_in_same_group["pipeline"]["tasks"][3]["labels"] = [
            {
                "name": "parent 1",
                "color": "#0015FFFF",
                "group": "parent group",
            },
            {
                "name": "parent 2",
                "color": "#0020FFFF",
                "group": "parent group",
            },
            {
                "name": "child 1",
                "color": "#0018FFFA",
                "group": "child group",
                "parent_id": "parent 1",
            },
            {
                "name": "child 2",
                "color": "#0017FFFA",
                "group": "child group",
                "parent_id": "parent 2",
            },
        ]

        invalid_dicts = (
            (no_name, ValidationError),
            (extra_property, ValidationError),
            (label_is_empty, ValidationError),
            (duplicate_task_title, DuplicateTaskNamesException),
            (duplicate_label_name, DuplicateLabelNamesException),
            (missing_connection, BadNumberOfConnectionsException),
            (too_many_labels, TooManyLabelsException),
            (
                different_label_parents_in_same_group,
                MismatchingParentsInLabelGroupException,
            ),
        )
        # check that the expected error is raised
        for data, expected_exception in invalid_dicts:
            with pytest.raises(expected_exception):
                ProjectRestValidator().validate_creation_data_statically(data)
        ProjectRestValidator().validate_creation_data_statically(valid_data)

    @pytest.mark.parametrize(
        "update_operation,updated_task_index,updated_property,updated_property_value",
        [
            ("edit", 1, "hotkey", "A+X"),
            ("edit", 3, "color", "#12345678"),
            ("edit", 3, "name", "ellipse"),
            ("add", 3, None, None),
        ],
        ids=[
            "edit_detection_label_hotkey",
            "edit_classification_label_color",
            "edit_classification_label_name",
            "add_classification_label",
        ],
    )
    def test_update_task_chain_project(  # noqa: C901
        self, fxt_db_project_service, update_operation, updated_task_index, updated_property, updated_property_value
    ) -> None:
        """
        <b>Description:</b>
        Test if a task-chain project can be updated correctly.

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        Test passes if the operation succeeds and the project is updated as expected.

        <b>Steps</b>
        1. Define a REST dict to create a detection->classification project
        2. Create the project from its REST definition
        3. Define a REST dict to update the project.
           W.r.t. the creation dict, the following changes are applied:
            - change the 'hotkey' of the detection label
            - change the 'color' of a classification label
            - change the 'name' of another classification label
            - add a new classification label
        4. Validate the update dict with ProjectRestValidator().validate_update_data
        5. Update the project with ProjectBuilder.edit_existing_project
        6. Reload the project and its schema
        7. Verify that the updated objects contain the right information
        """
        NEW_LABEL_NAME = "pentagon"

        # Step 1
        project_creation_data = self.get_task_chain_project_dict()
        project_initial_name = project_creation_data["name"]
        creation_pipeline_data = project_creation_data["pipeline"]
        det_task = creation_pipeline_data["tasks"][1]
        cls_task = creation_pipeline_data["tasks"][3]
        assert det_task["task_type"] == "detection"
        assert cls_task["task_type"] == "classification"
        model_template_dataset = ModelTemplateList().get_by_id("dataset")
        model_template_detection = ModelTemplateList().get_by_id("detection")
        model_template_crop = ModelTemplateList().get_by_id("crop")
        model_template_classification = ModelTemplateList().get_by_id("classification")
        model_templates = [
            model_template_dataset,
            model_template_detection,
            model_template_crop,
            model_template_classification,
        ]
        # Step 2
        project = fxt_db_project_service.create_empty_project(
            name=project_initial_name,
            pipeline_data=creation_pipeline_data,
            model_templates=model_templates,
        )
        project_label_schema = fxt_db_project_service.label_schema
        detection_label_schema = fxt_db_project_service.label_schema_1
        classification_label_schema = fxt_db_project_service.label_schema_2
        initial_num_labels = len(project_label_schema.get_labels(include_empty=True))

        # Step 3
        # For the 'update', we reuse the same REST definition as for 'create', but with a few changes:
        #  - set the id for project, task and labels
        #  - connections now use ids instead of task names
        project_update_data = copy.deepcopy(project_creation_data)
        update_pipeline_data = project_update_data["pipeline"]
        task_title_to_id = {task.title: task.id_ for task in project.tasks}
        label_name_to_id = {label.name: label.id_ for label in project_label_schema.get_labels(True)}
        project_update_data["id"] = str(project.id_)
        for task in update_pipeline_data["tasks"]:
            task["id"] = str(task_title_to_id[task["title"]])
            for label in task.get("labels", []):
                label["id"] = str(label_name_to_id[label["name"]])
        for connection in update_pipeline_data["connections"]:
            connection["from"] = str(task_title_to_id[connection["from"]])
            connection["to"] = str(task_title_to_id[connection["to"]])
        # Custom modifications based on the test parametrization
        match update_operation:
            case "add":
                new_label_rest = {
                    "name": NEW_LABEL_NAME,
                    "color": "#AABBCCDD",
                    "group": "default classification group",
                    "parent_id": "object",
                    "revisit_affected_annotations": True,
                }
                update_pipeline_data["tasks"][updated_task_index]["labels"].append(new_label_rest)
            case "edit":
                update_pipeline_data["tasks"][updated_task_index]["labels"][0][updated_property] = (
                    updated_property_value
                )
            case _:
                raise ValueError(f"Unsupported operation {update_operation}")

        # Step 4
        ProjectRestValidator().validate_update_data_statically(project_update_data)
        parser_kwargs = {"rest_data": project_update_data}
        # Step 5
        _, _, _, _, _, _ = ProjectBuilder.edit_existing_project(
            project=project,
            class_parser=RestProjectUpdateParser,
            parser_kwargs=parser_kwargs,
        )

        # Step 6
        updated_project = ProjectManager.get_project_by_id(project_id=project.id_)
        updated_project_label_schema = LabelSchemaRepo(updated_project.identifier).get_latest()
        updated_project_labels = updated_project_label_schema.get_labels(include_empty=True)
        updated_detection_label_schema = LabelSchemaService.get_latest_label_schema_for_task(
            project_identifier=updated_project.identifier,
            task_node_id=project.tasks[1].id_,
        )
        updated_classification_label_schema = LabelSchemaService.get_latest_label_schema_for_task(
            project_identifier=updated_project.identifier,
            task_node_id=project.tasks[3].id_,
        )

        # Step 7
        match update_operation:
            case "edit":
                # no structural changes -> expect same schema
                assert updated_project_label_schema.id_ == project_label_schema.id_
                assert updated_detection_label_schema.id_ == detection_label_schema.id_
                assert updated_classification_label_schema.id_ == classification_label_schema.id_
            case "add":
                # structural changes -> expect new schema, properly linked to the previous one
                assert updated_project_label_schema.previous_schema_revision_id == project_label_schema.id_
                assert updated_detection_label_schema.previous_schema_revision_id == detection_label_schema.id_
                assert (
                    updated_classification_label_schema.previous_schema_revision_id == classification_label_schema.id_
                )
        final_num_labels = len(updated_project_labels)
        assert final_num_labels == initial_num_labels + (1 if update_operation == "add" else 0)
        label_name_to_obj: dict[str, Label] = {label.name: label for label in updated_project_labels}
        # Check the names
        det_label_rest = update_pipeline_data["tasks"][1]["labels"][0]
        cls_label_0_rest = update_pipeline_data["tasks"][3]["labels"][0]
        cls_label_1_rest = update_pipeline_data["tasks"][3]["labels"][1]
        assert det_label_rest["name"] in label_name_to_obj
        assert cls_label_0_rest["name"] in label_name_to_obj
        assert cls_label_1_rest["name"] in label_name_to_obj
        match update_operation:
            case "edit":
                # Check that the modified label is correctly updated
                edited_label_name = update_pipeline_data["tasks"][updated_task_index]["labels"][0]["name"]
                edited_label = label_name_to_obj[edited_label_name]
                if updated_property == "color":
                    assert getattr(edited_label, updated_property).hex_str == updated_property_value
                else:
                    assert getattr(edited_label, updated_property) == updated_property_value
            case "add":
                # Check that the added label is actually present
                assert NEW_LABEL_NAME in label_name_to_obj
                new_label = label_name_to_obj[NEW_LABEL_NAME]
                assert new_label.id_
            case _:
                raise ValueError(f"Unsupported operation {update_operation}")
        # Check the groups
        assert len(project_label_schema.get_groups(True)) == len(updated_project_label_schema.get_groups(True))
        assert any(
            group.group_type == LabelGroupType.EMPTY_LABEL
            for group in updated_project_label_schema.get_groups(include_empty=True)
        )
        assert any(
            group.group_type == LabelGroupType.EMPTY_LABEL
            for group in updated_detection_label_schema.get_groups(include_empty=True)
        )
        assert all(
            group.group_type == LabelGroupType.EXCLUSIVE
            for group in updated_classification_label_schema.get_groups(include_empty=True)
        )

    def test_update_hierarchy_classification_project(self, fxt_db_project_service) -> None:
        """
        <b>Description:</b>
        Test if a hierarchy_classification project can be updated correctly.

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        Test passes if the operation succeeds and the project is updated as expected.

        <b>Steps</b>
        1. Define a REST dict to create a hierarchy classification project
        2. Create the project from its REST definition
        3. Define a REST dict to update the project.
           W.r.t. the creation dict, the following changes are applied:
            - add a new child classification label
        4. Validate the update dict with ProjectRestValidator().validate_update_data
        5. Update the project with ProjectBuilder.edit_existing_project
        6. Reload the project and its schema
        7. Verify that the updated objects contain the right information
        """

        # Step 1
        project_creation_data = self.get_hierarchy_project_dict()
        project_name = project_creation_data["name"]
        pipeline_data = project_creation_data["pipeline"]
        model_template_dataset = ModelTemplateList().get_by_id("dataset")
        model_template_classification = ModelTemplateList().get_by_id("classification")
        model_templates = [model_template_dataset, model_template_classification]
        # Step 2
        project = fxt_db_project_service.create_empty_project(
            name=project_name,
            pipeline_data=pipeline_data,
            model_templates=model_templates,
        )
        project_label_schema = fxt_db_project_service.label_schema
        classification_label_schema = fxt_db_project_service.label_schema_1
        project_labels = project_label_schema.get_labels(include_empty=True)
        initial_num_labels = len(project_labels)

        # Step 3
        # For the 'update', we reuse the same REST definition as for 'create', with
        # only a few changes:
        #  - the 'id' is set for the project, tasks and labels
        #  - a new label is inserted for classification
        project_update_data = copy.deepcopy(project_creation_data)
        update_pipeline_data = project_update_data["pipeline"]
        task_title_to_id = {task.title: task.id_ for task in project.tasks}
        label_name_to_id = {label.name: label.id_ for label in project_labels}
        labels_as_rest = [
            LabelRESTViews.label_to_rest(label=label, label_schema=project_label_schema) for label in project_labels
        ]
        label_2_parent = project_label_schema.get_label_by_name("2")
        project_update_data["id"] = str(project.id_)
        for task in update_pipeline_data["tasks"]:
            task["id"] = str(task_title_to_id[task["title"]])
            for label in task.get("labels", []):
                label["id"] = str(label_name_to_id[label["name"]])
        for connection in update_pipeline_data["connections"]:
            connection["from"] = str(task_title_to_id[connection["from"]])
            connection["to"] = str(task_title_to_id[connection["to"]])
        new_label = {
            "name": "2.2",
            "color": "#00f5d4ff",
            "group": "Group 2.X",
            "hotkey": "",
            "parent_id": label_2_parent.id_,
            "revisit_affected_annotations": True,
        }
        labels_as_rest.append(new_label)
        update_pipeline_data["tasks"][1]["labels"] = labels_as_rest

        # Step 4
        ProjectRestValidator().validate_update_data_statically(project_update_data)
        parser_kwargs = {"rest_data": project_update_data}
        # Step 5
        _, _, _, _, _, _ = ProjectBuilder.edit_existing_project(
            project=project,
            class_parser=RestProjectUpdateParser,
            parser_kwargs=parser_kwargs,
        )

        # Step 6
        updated_project = ProjectManager.get_project_by_id(project_id=project.id_)
        updated_project_label_schema = LabelSchemaRepo(updated_project.identifier).get_latest()
        updated_project_labels = updated_project_label_schema.get_labels(include_empty=True)
        updated_classification_label_schema = LabelSchemaService.get_latest_label_schema_for_task(
            project_identifier=updated_project.identifier,
            task_node_id=project.tasks[1].id_,
        )
        added_label_22 = updated_classification_label_schema.get_label_by_name("2.2")

        # Step 7
        assert updated_project_label_schema.previous_schema_revision_id == project_label_schema.id_
        assert updated_classification_label_schema.previous_schema_revision_id == classification_label_schema.id_
        assert len(updated_project_labels) == initial_num_labels + 1
        assert updated_classification_label_schema.parent_schema.get_parent(added_label_22) == label_2_parent
        assert any(
            group.group_type == LabelGroupType.EMPTY_LABEL
            for group in updated_project_label_schema.get_groups(include_empty=True)
        )

    def test_update_project_name(self, fxt_db_project_service) -> None:
        """
        <b>Description:</b>
        Test if a hierarchy_classification project name is correctly updated

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        Test passes if the operation succeeds and the project is updated as expected.

        <b>Steps</b>
        1. Define a REST dict to create a hierarchy classification project
        2. Create the project from its REST definition
        3. Define a REST dict to update the project.
           W.r.t. the creation dict, the following changes are applied:
            - Project's name is updated
        4. Validate the update dict with ProjectRestValidator().validate_update_data
        5. Update the project with ProjectBuilder.edit_existing_project
        6. Reload the project and its schema
        7. Verify that the updated objects contain the right information
        """

        # Step 1
        project_creation_data = self.get_hierarchy_project_dict()
        project_name = project_creation_data["name"]
        pipeline_data = project_creation_data["pipeline"]
        model_template_dataset = ModelTemplateList().get_by_id("dataset")
        model_template_classification = ModelTemplateList().get_by_id("classification")
        model_templates = [model_template_dataset, model_template_classification]
        # Step 2
        project = fxt_db_project_service.create_empty_project(
            name=project_name,
            pipeline_data=pipeline_data,
            model_templates=model_templates,
        )
        project_label_schema = fxt_db_project_service.label_schema
        classification_label_schema = fxt_db_project_service.label_schema_1
        project_labels = project_label_schema.get_labels(include_empty=True)
        initial_num_labels = len(project_labels)

        # Step 3
        # For the 'update', we reuse the same REST definition as for 'create', with
        # only a few changes:
        #  - Project's name is set to "New project name"
        project_update_data = copy.deepcopy(project_creation_data)
        project_update_data["name"] = "New project name"
        project_update_data["id"] = str(project.id_)
        update_pipeline_data = project_update_data["pipeline"]
        task_title_to_id = {task.title: task.id_ for task in project.tasks}
        label_name_to_id = {label.name: label.id_ for label in project_labels}
        for task in update_pipeline_data["tasks"]:
            task["id"] = str(task_title_to_id[task["title"]])
            for label in task.get("labels", []):
                label["id"] = str(label_name_to_id[label["name"]])
        for connection in update_pipeline_data["connections"]:
            connection["from"] = str(task_title_to_id[connection["from"]])
            connection["to"] = str(task_title_to_id[connection["to"]])

        # Step 4
        ProjectRestValidator().validate_update_data_statically(project_update_data)
        parser_kwargs = {"rest_data": project_update_data}
        # Step 5
        _, _, _, _, _, _ = ProjectBuilder.edit_existing_project(
            project=project,
            class_parser=RestProjectUpdateParser,
            parser_kwargs=parser_kwargs,
        )

        # Step 6
        updated_project = ProjectManager.get_project_by_id(project_id=project.id_)
        updated_project_label_schema = LabelSchemaRepo(updated_project.identifier).get_latest()
        updated_project_labels = updated_project_label_schema.get_labels(include_empty=True)
        updated_classification_label_schema = LabelSchemaService.get_latest_label_schema_for_task(
            project_identifier=updated_project.identifier,
            task_node_id=project.tasks[1].id_,
        )

        # Step 7
        assert updated_project.name == "New project name"
        assert updated_project_label_schema == project_label_schema
        assert updated_project_label_schema.previous_schema_revision_id == ID()
        assert updated_classification_label_schema == classification_label_schema
        assert updated_classification_label_schema.previous_schema_revision_id == ID()
        assert len(updated_project_labels) == initial_num_labels

    def test_update_label_group_name(self, fxt_db_project_service) -> None:
        """
        <b>Description:</b>
        Test if a hierarchy_classification project blocks the editing of label groups.
        A new label group can be added, but an existing label cannot be associated with
        a new label group.

        <b>Input data:</b>
        None

        <b>Expected results:</b>
        Test passes if an error is raised when trying to incorrectly edit label groups

        <b>Steps</b>
        1. Define a REST dict to create a hierarchy classification project
        2. Create the project from its REST definition
        3. Define a REST dict to update the project.
            - An existing label's group is changed
        4. Validate the update dict with ProjectRestValidator().validate_update_data
        5. Update the project with ProjectBuilder.edit_existing_project
        6. Verify that an error is raised
        """

        # Step 1
        project_creation_data = self.get_hierarchy_project_dict()
        project_name = project_creation_data["name"]
        pipeline_data = project_creation_data["pipeline"]
        model_template_dataset = ModelTemplateList().get_by_id("dataset")
        model_template_classification = ModelTemplateList().get_by_id("classification")
        model_templates = [model_template_dataset, model_template_classification]
        # Step 2
        project = fxt_db_project_service.create_empty_project(
            name=project_name,
            pipeline_data=pipeline_data,
            model_templates=model_templates,
        )
        project_label_schema = fxt_db_project_service.label_schema
        project_labels = project_label_schema.get_labels(include_empty=True)

        # Step 3
        # For the 'update', we reuse the same REST definition as for 'create'
        #  - Project's name is set to "New project name"
        project_update_data = copy.deepcopy(project_creation_data)
        project_update_data["id"] = str(project.id_)
        update_pipeline_data = project_update_data["pipeline"]
        task_title_to_id = {task.title: task.id_ for task in project.tasks}
        label_name_to_id = {label.name: label.id_ for label in project_labels}
        for task in update_pipeline_data["tasks"]:
            task["id"] = str(task_title_to_id[task["title"]])
            for label in task.get("labels", []):
                label["id"] = str(label_name_to_id[label["name"]])
        for connection in update_pipeline_data["connections"]:
            connection["from"] = str(task_title_to_id[connection["from"]])
            connection["to"] = str(task_title_to_id[connection["to"]])
        update_pipeline_data["tasks"][1]["labels"][0]["group"] = "New group"

        # Step 4
        ProjectRestValidator().validate_update_data_statically(project_update_data)
        parser_kwargs = {"rest_data": project_update_data}
        # Step 5, 6
        with pytest.raises(ProjectUpdateError):
            _, _, _, _, _, _ = ProjectBuilder.edit_existing_project(
                project=project,
                class_parser=RestProjectUpdateParser,
                parser_kwargs=parser_kwargs,
            )

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

from unittest.mock import patch

import pytest
from geti_spicedb_tools import SpiceDB
from testfixtures import compare

from communication.rest_controllers.project_controller import ProjectRESTController
from communication.rest_data_validator import ProjectRestValidator
from communication.rest_parsers import RestProjectParser, RestProjectUpdateParser
from communication.rest_views.project_rest_views import ProjectRESTViews
from managers.project_manager import ProjectManager

from geti_fastapi_tools.responses import success_response_rest
from geti_types import ID
from sc_sdk.entities.project import NullProject
from sc_sdk.repos import ProjectRepo
from sc_sdk.utils.deletion_helpers import DeletionHelpers
from sc_sdk.utils.project_builder import PersistedProjectBuilder


class TestProjectRESTController:
    def test_create_project(
        self,
        fxt_organization_id,
        fxt_project,
        fxt_mongo_id,
        fxt_project_rest,
        fxt_detection_task,
        fxt_detection_label_schema,
    ):
        data = {"name": "dummy_name", "pipeline": "dummy_pipeline"}
        workspace_id = fxt_mongo_id(1)
        ret_sc_create = (
            fxt_project,
            fxt_detection_label_schema,
            {fxt_detection_task.title: fxt_detection_label_schema},
        )
        with (
            patch.object(
                ProjectRestValidator,
                "validate_creation_data_statically",
                return_value=True,
            ) as mock_validate_creation_data,
            patch.object(ProjectManager, "create_project", return_value=ret_sc_create) as mock_sc_create_project,
            patch.object(ProjectRESTViews, "project_to_rest", return_value=fxt_project_rest),
        ):
            result = ProjectRESTController.create_project(
                organization_id=fxt_organization_id,
                data=data,
                creator_id="",
                workspace_id=workspace_id,
            )

        compare(result, fxt_project_rest, ignore_eq=True)
        mock_validate_creation_data.assert_called_once_with(data)
        mock_sc_create_project.assert_called_once_with(
            creator_id="",
            workspace_id=workspace_id,
            project_parser=RestProjectParser,
            parser_kwargs={"rest_data": data},
        )

    def test_update_project(
        self,
        fxt_organization_id,
        fxt_project,
        fxt_project_with_detection_task,
        fxt_empty_label_schema,
        fxt_mongo_id,
        fxt_project_rest,
    ):
        data = {"name": "dummy_name", "pipeline": "dummy_pipeline"}
        project_id = fxt_mongo_id(1)
        schema_per_task = {"Sample detection task": fxt_empty_label_schema}
        with (
            patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project) as mock_get_project_by_id,
            patch.object(
                ProjectRestValidator,
                "validate_update_data_statically",
                return_value=True,
            ) as mock_validate_update_data,
            patch.object(
                PersistedProjectBuilder,
                "edit_existing_project",
                return_value=[fxt_project, fxt_empty_label_schema, schema_per_task, [], {}, False],
            ) as mock_update_project,
            patch.object(ProjectRESTViews, "project_to_rest", return_value=fxt_project_rest) as mock_project_to_rest,
        ):
            result = ProjectRESTController.update_project(
                organization_id=fxt_organization_id, project_id=project_id, data=data
            )

        compare(result, fxt_project_rest, ignore_eq=True)
        mock_get_project_by_id.assert_called_with(project_id=project_id)
        mock_validate_update_data.assert_called_with(data)
        mock_update_project.assert_called_with(
            project=fxt_project,
            class_parser=RestProjectUpdateParser,
            parser_kwargs={"rest_data": data},
        )
        mock_project_to_rest.assert_called_with(
            organization_id=fxt_organization_id,
            project=fxt_project_with_detection_task,
            label_schema_per_task={fxt_project.tasks[1].id_: fxt_empty_label_schema},
            storage_info={},
        )

    def test_delete_project(self, fxt_mongo_id):
        project_id = fxt_mongo_id(1)
        with patch.object(ProjectManager, "delete_project", return_value=True) as mock_delete_project:
            result = ProjectRESTController.delete_project(project_id=project_id)

        compare(result, success_response_rest(), ignore_eq=True)
        mock_delete_project.assert_called_with(project_id=project_id)

    # This is a test for the workaround mentioned in
    # CVS-86033
    # It should be removed or adapted once the proper fix is implemented.

    def test_hidden_project_delete_repo(
        self,
        fxt_db_project_service,
        fxt_organization_id,
        fxt_project_query_data,
    ) -> None:
        """
        <b>Description:</b>
        Test whether the project is appropriately hidden when it is set to be deleted.
        This can happen when a thread wants to delete the project when another thread
        wants to list the projects at the same time.


        <b>Input data:</b>
        None

        <b>Expected results:</b>
        The project entity remains but the label schema entity is deleted from
        the database

        <b>Steps</b>
        1. Create a detection project with some annotated images.
        2. Corrupt the deletion of the project by only deleting the label schema.
        3. Confirm that getting the projects fails.
        4. Properly delete the project with the workaround.
        5. Confirm that the project list is empty as the project is now hidden.
        """
        db_service = fxt_db_project_service
        project = db_service.create_annotated_detection_project(num_images_per_label=1)
        project_manager = ProjectManager()
        project_repo = ProjectRepo()

        # Thread 1 deletes part of the project. The project is not hidden and is corrupt
        DeletionHelpers.delete_all_label_schema_by_project(project.identifier)

        # Thread 2 wants to get all the projects, this causes an exception
        with (
            pytest.raises(Exception),
            patch.object(
                SpiceDB(),
                "get_user_projects",
                return_value=[project.id_],
            ),
        ):
            ProjectRESTController.get_projects(
                user_id=ID("dummy_id"),
                organization_id=fxt_organization_id,
                query_data=fxt_project_query_data,
                url=f"http://localhost/api/v1/organizations/{fxt_organization_id}/workspaces/{project.workspace_id}/projects",
                include_hidden=False,
            )

        # Thread 1 now uses the workaround to delete the project.
        # We mock "delete" with workaround as we are only setting it to hidden, this
        # simulates that thread 1 has not yet finished deleting the project.
        with (
            patch.object(
                DeletionHelpers,
                "delete_project_by_id",
                return_value=None,
            ),
            patch.object(
                SpiceDB(),
                "delete_project",
                return_value=None,
            ),
        ):
            project_manager.delete_project(project_id=project.id_)

        # Thread 2 gets the list of projects which should be 0 as the project is hidden.
        with patch.object(
            SpiceDB(),
            "get_user_projects",
            return_value=[project.id_],
        ):
            project_list = ProjectRESTController.get_projects(
                user_id=ID("dummy_id"),
                organization_id=fxt_organization_id,
                query_data=fxt_project_query_data,
                url=f"http://localhost/api/v1/organizations/{fxt_organization_id}/workspaces/{project.workspace_id}/projects",
                include_hidden=False,
            )
            assert project_list["project_counts"] == 0

        # Check if we can find the hidden project.
        hidden_project = project_repo.get_by_id(project.id_)
        assert not isinstance(hidden_project, NullProject)

    def test_get_project(
        self,
        fxt_organization_id,
        fxt_project,
        fxt_empty_label_schema,
        fxt_mongo_id,
        fxt_project_rest,
    ):
        project_id = fxt_mongo_id(1)
        schema_per_task = {fxt_mongo_id(1): fxt_empty_label_schema}
        with (
            patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project) as mock_get_project_by_id,
            patch.object(
                ProjectRESTController,
                "_get_label_schema_per_task",
                return_value=schema_per_task,
            ),
            patch.object(ProjectRESTViews, "project_to_rest", return_value=fxt_project_rest) as mock_project_to_rest,
        ):
            result = ProjectRESTController.get_project(organization_id=fxt_organization_id, project_id=project_id)

        compare(result, fxt_project_rest, ignore_eq=True)
        mock_get_project_by_id.assert_called_with(project_id=project_id)
        mock_project_to_rest.assert_called_with(
            organization_id=fxt_organization_id,
            project=fxt_project,
            label_schema_per_task=schema_per_task,
            include_deleted_labels=False,
            storage_info={},
        )

    def test_get_projects_names(
        self,
        fxt_project_query_data,
        fxt_project,
        fxt_mongo_id,
        fxt_project_rest,
        fxt_empty_label_schema,
    ):
        dummy_projects_names = {fxt_project.id_: "Test project"}
        dummy_rest = {"projects": [{"id": fxt_project.id_, "name": "Test project"}]}
        with (
            patch.object(
                ProjectManager,
                "get_projects_names",
                return_value=dummy_projects_names,
            ) as mock_sc_get_projects_names,
            patch.object(
                ProjectRESTViews, "projects_names_to_rest", return_value=dummy_rest
            ) as mock_projects_names_to_rest,
        ):
            result = ProjectRESTController.get_projects_names(user_id=ID("dummy_id"))

        mock_sc_get_projects_names.assert_called_once_with(user_uid=ID("dummy_id"))
        mock_projects_names_to_rest.assert_called_with(dummy_projects_names)
        assert result == dummy_rest

    def test_get_projects(
        self,
        fxt_project_query_data,
        fxt_project,
        fxt_mongo_id,
        fxt_project_rest,
        fxt_empty_label_schema,
    ):
        dummy_project_count = 6
        dummy_organization_id = fxt_mongo_id(3)
        dummy_url = "dummy_url"
        dummy_next_page = "dummy_next_page"
        dummy_projects = [fxt_project]
        dummy_rest = {
            "Items": [fxt_project_rest],
            "project_counts": dummy_project_count,
            "project_page_count": 1,
            "next_page": dummy_next_page,
        }
        schema_per_task = {fxt_mongo_id(1): fxt_empty_label_schema}
        with (
            patch.object(
                ProjectManager,
                "get_projects_and_count_all",
                return_value=(dummy_projects, dummy_project_count),
            ) as mock_sc_get_projects_and_count_all,
            patch.object(ProjectRESTViews, "projects_to_rest", return_value=dummy_rest) as mock_projects_to_rest,
            patch.object(ProjectRESTController, "get_next_page", return_value=dummy_next_page) as mock_get_next_page,
            patch.object(
                ProjectRESTController,
                "_get_label_schema_per_task",
                return_value=schema_per_task,
            ) as mock_get_label_schema_per_task,
        ):
            result = ProjectRESTController.get_projects(
                user_id=ID("dummy_id"),
                organization_id=dummy_organization_id,
                query_data=fxt_project_query_data,
                url=dummy_url,
            )

        mock_sc_get_projects_and_count_all.assert_called_once_with(
            user_uid=ID("dummy_id"),
            query_data=fxt_project_query_data,
            include_hidden=True,
        )
        mock_projects_to_rest.assert_called_with(
            organization_id=dummy_organization_id,
            projects=dummy_projects,
            label_schema_per_task_per_project=[schema_per_task],
            project_counts=dummy_project_count,
            next_page=dummy_next_page,
            storage_info_per_project=[{}],
        )
        mock_get_next_page.assert_called_with(url=dummy_url, skip=1)
        mock_get_label_schema_per_task.assert_called()
        assert result == dummy_rest

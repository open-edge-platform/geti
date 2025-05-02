# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import unittest
from unittest.mock import MagicMock, patch

from testfixtures import compare

from communication.rest_controllers import CodeDeploymentRESTController
from communication.rest_views.code_deployment_rest_views import CodeDeploymentRestViews
from managers.project_manager import ProjectManager
from resource_management.code_deployment_manager import DEPLOYMENT_FILENAME_TEMPLATE, CodeDeploymentManager

from geti_types import ID, ProjectIdentifier
from iai_core.utils.naming_helpers import slugify


class TestCodeDeploymentRESTController:
    def test_get_code_deployment_detail(
        self,
        fxt_project,
        fxt_code_deployment,
        fxt_code_deployment_rest,
    ) -> None:
        project_identifier = ProjectIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
        )
        with (
            patch.object(
                CodeDeploymentManager,
                "get_deployment_by_id",
                return_value=fxt_code_deployment,
            ) as mock_get_code_deployment_by_id,
            patch.object(
                CodeDeploymentRestViews,
                "to_rest",
                return_value=fxt_code_deployment_rest,
            ) as mock_code_deployment_to_rest,
        ):
            result = CodeDeploymentRESTController.get_code_deployment_detail(
                project_identifier=project_identifier,
                code_deployment_id=fxt_code_deployment.id_,
            )

        compare(result, fxt_code_deployment_rest, ignore_eq=True)
        mock_get_code_deployment_by_id.assert_called_once_with(
            project_identifier=project_identifier,
            code_deployment_id=fxt_code_deployment.id_,
        )
        mock_code_deployment_to_rest.assert_called_once_with(fxt_code_deployment)

    def test_delete_code_deployment(
        self,
        fxt_project,
        fxt_mongo_id,
        fxt_code_deployment,
    ) -> None:
        project_identifier = ProjectIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
        )
        with patch.object(
            CodeDeploymentManager,
            "delete_deployment_by_id",
            return_value=fxt_code_deployment,
        ) as mock_delete_code_deployment_by_id:
            CodeDeploymentRESTController.delete_code_deployment(
                project_identifier=project_identifier,
                code_deployment_id=fxt_code_deployment.id_,
            )

        mock_delete_code_deployment_by_id.assert_called_once_with(
            project_identifier=project_identifier,
            code_deployment_id=fxt_code_deployment.id_,
        )

    def test_get_filepath_by_deployment_id(
        self,
        fxt_project,
        fxt_mongo_id,
        fxt_code_deployment,
    ) -> None:
        test_file_path = "path/testing"
        fxt_project.name = f'"{fxt_project.name}"'
        file_path_response = (
            test_file_path,
            f"Deployment-{slugify(fxt_project.name)}.zip",
        )
        project_identifier = ProjectIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
        )
        with (
            patch.object(ProjectManager, "get_project_by_id", return_value=fxt_project) as mock_get_project_by_id,
            patch.object(
                CodeDeploymentManager,
                "get_code_deployment_path_or_presigned_url",
                return_value=test_file_path,
            ) as mock_get_file_path_deployment_by_id,
        ):
            result = CodeDeploymentRESTController.get_filepath_by_deployment_id(
                project_identifier=project_identifier,
                code_deployment_id=fxt_code_deployment.id_,
            )

        mock_get_project_by_id.assert_called_once_with(project_id=project_identifier.project_id)
        mock_get_file_path_deployment_by_id.assert_called_once_with(
            project_identifier=project_identifier,
            code_deployment_id=fxt_code_deployment.id_,
            check_ready=True,
            filename=f"{DEPLOYMENT_FILENAME_TEMPLATE % slugify(fxt_project.name)}.zip",
        )
        compare(result, file_path_response, ignore_eq=True)


class TestCodeDeploymentController(unittest.TestCase):
    @patch("communication.rest_controllers.code_deployment_controller.check_free_space_for_operation")
    @patch("communication.rest_controllers.code_deployment_controller.ProjectManager.get_project_by_id")
    @patch("communication.rest_controllers.code_deployment_controller.CodeDeploymentRepo")
    @patch("communication.rest_controllers.code_deployment_controller.CodeDeploymentRESTValidator")
    @patch("communication.rest_controllers.code_deployment_controller.ProjectRESTViews.project_to_rest")
    @patch("communication.rest_controllers.code_deployment_controller.CodeDeploymentRestViews.to_rest")
    @patch("communication.rest_controllers.code_deployment_controller.contextvars.copy_context")
    @patch("communication.rest_controllers.code_deployment_controller.export_executor.submit")
    def test_prepare_for_code_deployment_successful(
        self,
        mock_submit,
        mock_copy_context,
        mock_to_rest,
        mock_project_to_rest,
        mock_validator,
        mock_repo,
        mock_get_project,
        mock_check_space,
    ):
        organization_id = ID("org_id")
        workspace_id = ID("workspace_id")
        project_id = ID("project_id")
        user_id = ID("user_id")
        model_list_rest = {"models": [{"model_group_id": "group_id", "model_id": "model_id"}]}

        mock_project = MagicMock()
        mock_get_project.return_value = mock_project
        mock_repo_instance = MagicMock()
        mock_repo.return_value = mock_repo_instance
        mock_copy_context.return_value.run = MagicMock()
        mock_to_rest.return_value = {}

        result = CodeDeploymentRESTController.prepare_for_code_deployment(
            organization_id, workspace_id, project_id, model_list_rest, user_id
        )

        self.assertEqual(result, {})
        mock_check_space.assert_called_once()
        mock_validator().validate_code_deployment.assert_called_once_with(model_list_rest)
        mock_repo_instance.save.assert_called_once()
        mock_submit.assert_called_once()

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import numpy as np
import pytest

from communication.exceptions import CodeDeploymentFileIsNotReadyException, CodeDeploymentNotFoundException
from entities.deployment import CodeDeployment, DeploymentState, NullCodeDeployment
from repos.code_deployment_repo import CodeDeploymentRepo
from resource_management.code_deployment_manager import CodeDeploymentManager

from geti_types import ProjectIdentifier
from iai_core.entities.model import Model, ModelFormat
from iai_core.entities.task_node import TaskNode
from iai_core.repos.storage.binary_repos import CodeDeploymentBinaryRepo


class TestCodeDeploymentManager:
    def test_get_deployment_by_id(self, fxt_project, fxt_code_deployment) -> None:
        """
        Tests the function 'get_code_deployment_by_id' with valid id and invalid id
        """
        project_identifier = ProjectIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
        )
        with patch.object(CodeDeploymentRepo, "get_by_id", return_value=fxt_code_deployment) as patched_get_by_id:
            result = CodeDeploymentManager().get_deployment_by_id(
                project_identifier=project_identifier,
                code_deployment_id=fxt_code_deployment.id_,
            )

        patched_get_by_id.assert_called_once_with(id_=fxt_code_deployment.id_)
        assert result == fxt_code_deployment

        random_id = CodeDeploymentRepo.generate_id()

        with pytest.raises(CodeDeploymentNotFoundException):
            with patch.object(
                CodeDeploymentRepo, "get_by_id", return_value=NullCodeDeployment()
            ) as mock_code_deployment_repo_get_by_id:
                CodeDeploymentManager().get_deployment_by_id(
                    project_identifier=project_identifier,
                    code_deployment_id=random_id,
                )

            mock_code_deployment_repo_get_by_id.assert_called_once_with(id_=random_id)

    def test_get_filepath_deployment_by_id(self, fxt_project, fxt_code_deployment) -> None:
        project_identifier = ProjectIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
        )
        temp_path = "/tmp/local/code-deployment"
        fxt_code_deployment.state = DeploymentState.DONE
        fxt_code_deployment.binary_filename = temp_path
        with (
            patch.object(
                CodeDeploymentManager,
                "get_deployment_by_id",
                return_value=fxt_code_deployment,
            ) as mock_get_deployment,
            patch.object(
                CodeDeploymentBinaryRepo,
                "get_path_or_presigned_url",
                return_value=Path(temp_path),
            ) as mock_get_path,
        ):
            result = CodeDeploymentManager().get_code_deployment_path_or_presigned_url(
                project_identifier=project_identifier,
                code_deployment_id=fxt_code_deployment.id_,
                check_ready=True,
                filename="dummy",
            )

        mock_get_deployment.assert_called_once_with(
            project_identifier=project_identifier,
            code_deployment_id=fxt_code_deployment.id_,
            check_binary_when_done=True,
        )
        mock_get_path.assert_called_once()
        assert result == Path(temp_path)

    def test_get_filepath_deployment_by_id_with_deployment_not_ready(self, fxt_project, fxt_code_deployment) -> None:
        project_identifier = ProjectIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
        )
        temp_path = "/temp/local/code-deployment"

        with (
            patch.object(
                CodeDeploymentManager,
                "get_deployment_by_id",
                return_value=fxt_code_deployment,
            ) as mock_get_deployment,
            patch.object(
                CodeDeploymentBinaryRepo,
                "get_path_or_presigned_url",
                return_value=Path(temp_path),
            ) as mock_get_path,
            pytest.raises(CodeDeploymentFileIsNotReadyException),
        ):
            CodeDeploymentManager().get_code_deployment_path_or_presigned_url(
                project_identifier=project_identifier,
                code_deployment_id=fxt_code_deployment.id_,
                check_ready=True,
                filename="dummy",
            )

        mock_get_deployment.assert_called_once_with(
            project_identifier=project_identifier,
            code_deployment_id=fxt_code_deployment.id_,
            check_binary_when_done=True,
        )
        mock_get_path.assert_not_called()

    def test_delete_deployment_by_id(self, fxt_project, fxt_code_deployment) -> None:
        project_identifier = ProjectIdentifier(
            workspace_id=fxt_project.workspace_id,
            project_id=fxt_project.id_,
        )
        fxt_code_deployment.binary_filename = "a_filename"
        with (
            patch.object(
                CodeDeploymentManager,
                "get_deployment_by_id",
                return_value=fxt_code_deployment,
            ) as patched_get_deployment,
            patch.object(
                CodeDeploymentBinaryRepo, "delete_by_filename", return_value=None
            ) as patched_delete_deployment_binary_repo,
            patch.object(CodeDeploymentRepo, "delete_by_id", return_value=None) as patched_delete_deployment_repo,
        ):
            CodeDeploymentManager.delete_deployment_by_id(
                project_identifier=project_identifier,
                code_deployment_id=fxt_code_deployment.id_,
            )

        patched_get_deployment.assert_called_once_with(
            project_identifier=project_identifier,
            code_deployment_id=fxt_code_deployment.id_,
            check_binary_when_done=True,
        )
        patched_delete_deployment_binary_repo.assert_called_once_with(filename=fxt_code_deployment.binary_filename)
        patched_delete_deployment_repo.assert_called_once_with(fxt_code_deployment.id_)


class TestCodeDeploymentManagerZip(unittest.TestCase):
    @patch("resource_management.code_deployment_manager.ModelRESTViews")
    @patch("resource_management.code_deployment_manager.CodeDeploymentRepo")
    @patch("resource_management.code_deployment_manager.CodeDeploymentBinaryRepo")
    @patch("resource_management.code_deployment_manager.ModelRepo")
    @patch("resource_management.code_deployment_manager.StatisticsUseCase")
    @patch("resource_management.code_deployment_manager.PipelineRESTViews")
    @patch("resource_management.code_deployment_manager.CodeDeploymentManager._get_random_2d_numpy_from_project")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    @patch("os.path.isdir")
    @patch("os.listdir")
    @patch("shutil.copytree")
    @patch("shutil.copyfile")
    @patch("zipfile.ZipFile")
    @patch("tempfile.TemporaryDirectory")
    def test_prepare_zip_file_successful(
        self,
        mock_tempdir,
        mock_zipfile,
        mock_copyfile,
        mock_copytree,
        mock_listdir,
        mock_isdir,
        mock_makedirs,
        mock_open,
        mock_get_random_2d_numpy,
        mock_pipeline_rest_views,
        mock_statistics_usecase,
        mock_model_repo,
        mock_code_deployment_binary_repo,
        mock_code_deployment_repo,
        mock_model_rest_view,
    ):
        task_node = MagicMock(spec=TaskNode)
        project = MagicMock()
        project.workspace_id = "workspace_id"
        project.tasks = [task_node]
        project.name = "test"
        project.get_trainable_task_nodes.return_value = [task_node]
        project_rest_view = {}
        code_deployment = MagicMock(spec=CodeDeployment)
        code_deployment.model_identifiers = [MagicMock()]
        code_deployment.progress = 0
        mock_tempdir.return_value.__enter__.return_value = "/tmp/dir"
        mock_listdir.return_value = []
        mock_isdir.return_value = False
        model = MagicMock(spec=Model)
        model.model_storage = MagicMock()
        model.model_storage.task_node_id = task_node.id_
        model.model_format = ModelFormat.OPENVINO
        model.exportable_code = b"sample data"
        mock_model_repo.return_value.get_by_id.return_value = model

        mock_pipeline_rest_views.task_node_to_rest.return_value = {"title": "task_node"}
        mock_statistics_usecase.get_model_performance.return_value = {}
        mock_pipeline_rest_views.optimized_model_to_rest.return_value = {}
        mock_model_rest_view.optimized_model_to_rest.return_value = {}
        mock_get_random_2d_numpy.return_value = np.zeros([10, 10, 3], dtype=np.float32)

        CodeDeploymentManager.prepare_zip_file(project, project_rest_view, code_deployment)

        self.assertEqual(code_deployment.state, DeploymentState.DONE)
        self.assertEqual(code_deployment.message, "Code deployment preparation successful.")
        mock_code_deployment_repo.return_value.save.assert_called_with(code_deployment)

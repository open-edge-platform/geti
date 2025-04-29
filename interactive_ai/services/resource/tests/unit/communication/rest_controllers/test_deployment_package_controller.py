# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import MagicMock, patch

from communication.model_registration_utils import ModelMapper, ProjectMapper
from communication.rest_controllers import DeploymentPackageRESTController
from communication.rest_views.project_rest_views import ProjectRESTViews
from managers.project_manager import ProjectManager
from resource_management.deployment_package_manager import DeploymentPackageManager

from geti_types import ProjectIdentifier
from grpc_interfaces.model_registration.client import ModelRegistrationClient
from sc_sdk.entities.project import Project
from sc_sdk.entities.task_node import TaskNode
from sc_sdk.repos import ModelRepo


class TestDeploymentPackageRESTController:
    def test_download_ovms_package(
        self,
        fxt_detection_classification_chain_project,
        fxt_model_identifiers,
        fxt_optimized_openvino_model,
        fxt_model_storage_detection,
    ) -> None:
        project_identifier = ProjectIdentifier(
            workspace_id=fxt_detection_classification_chain_project.workspace_id,
            project_id=fxt_detection_classification_chain_project.id_,
        )

        model_id_1 = fxt_model_identifiers[0].model_id
        model_storage_id_1 = fxt_model_identifiers[0].model_storage_id
        model_id_2 = fxt_model_identifiers[1].model_id
        model_storage_id_2 = fxt_model_identifiers[1].model_storage_id
        deployment_package_json = {
            "package_type": "ovms",
            "models": [
                {
                    "model_id": model_id_1,
                    "model_group_id": model_storage_id_1,
                },
                {
                    "model_id": model_id_2,
                    "model_group_id": model_storage_id_2,
                },
            ],
        }
        with (
            patch(
                "communication.rest_controllers.deployment_package_controller.check_free_space_for_operation",
                return_value=None,
            ),
            patch.object(ModelRegistrationClient, "download_graph", return_value="test.zip") as mock_download_graph,
            patch.object(
                ProjectManager, "get_project_by_id", return_value=fxt_detection_classification_chain_project
            ) as mock_get_project_by_id,
            patch.object(
                ModelRepo,
                "get_by_id",
                return_value=fxt_optimized_openvino_model,
            ) as mock_get_model_by_id_and_storage,
            patch.object(Project, "get_trainable_task_node_by_id", return_value=MagicMock(spec=TaskNode)),
            patch.object(ModelMapper, "forward"),
            patch.object(ProjectMapper, "forward"),
        ):
            DeploymentPackageRESTController.download_ovms_package(
                project_identifier=project_identifier, deployment_package_json=deployment_package_json
            )
            assert mock_download_graph.call_count == 1
            assert mock_get_project_by_id.call_count == 1
            assert mock_get_model_by_id_and_storage.call_count == 2

    def test_download_geti_sdk_package(
        self,
        fxt_detection_classification_chain_project,
        fxt_model_identifiers,
        fxt_project_rest,
    ) -> None:
        project_identifier = ProjectIdentifier(
            workspace_id=fxt_detection_classification_chain_project.workspace_id,
            project_id=fxt_detection_classification_chain_project.id_,
        )

        model_id_1 = fxt_model_identifiers[0].model_id
        model_storage_id_1 = fxt_model_identifiers[0].model_storage_id
        model_id_2 = fxt_model_identifiers[1].model_id
        model_storage_id_2 = fxt_model_identifiers[1].model_storage_id
        deployment_package_json = {
            "package_type": "geti_sdk",
            "models": [
                {
                    "model_id": model_id_1,
                    "model_group_id": model_storage_id_1,
                },
                {
                    "model_id": model_id_2,
                    "model_group_id": model_storage_id_2,
                },
            ],
        }

        with (
            patch(
                "communication.rest_controllers.deployment_package_controller.check_free_space_for_operation",
                return_value=None,
            ),
            patch.object(ProjectRESTViews, "project_to_rest", return_value=fxt_project_rest) as mock_project_to_rest,
            patch.object(
                ProjectManager, "get_project_by_id", return_value=fxt_detection_classification_chain_project
            ) as mock_get_project_by_id,
            patch.object(
                DeploymentPackageRESTController, "_get_label_schema_per_task", return_value=None
            ) as mock_get_label_schema_per_task,
            patch.object(
                DeploymentPackageManager, "prepare_geti_sdk_package", return_value="test.zip"
            ) as mock_prepare_geti_sdk_package,
        ):
            DeploymentPackageRESTController.download_geti_sdk_package(
                project_identifier=project_identifier,
                deployment_package_json=deployment_package_json,
            )
            assert mock_get_label_schema_per_task.call_count == 1
            assert mock_prepare_geti_sdk_package.call_count == 1
            assert mock_project_to_rest.call_count == 1
            assert mock_get_project_by_id.call_count == 1

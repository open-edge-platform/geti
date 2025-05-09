# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import ANY, MagicMock, call, patch

import pytest
from testfixtures import compare

from communication.model_registration_utils import ModelMapper, ProjectMapper
from communication.rest_controllers import ModelRESTController
from tests.fixtures.job import do_nothing
from usecases.statistics import StatisticsUseCase

import iai_core.configuration.helper as otx_config_helper
from geti_kafka_tools import publish_event
from geti_types import ID, make_session, session_context
from grpc_interfaces.model_registration.client import ModelRegistrationClient
from iai_core.entities.label_schema import LabelGroup, LabelSchema
from iai_core.entities.model import Model, ModelFormat, ModelOptimizationType
from iai_core.entities.model_storage import ModelStorageIdentifier
from iai_core.entities.project import Project
from iai_core.repos import DatasetRepo, LabelSchemaRepo, ModelRepo, ModelStorageRepo, ProjectRepo
from iai_core.services import ModelService


class TestModelRESTController:
    def test_export_base_model(
        self,
        fxt_project,
        fxt_model,
        fxt_zip_file_data,
    ) -> None:
        project_id = fxt_project.id_
        model_storage_id = fxt_model.model_storage.id_
        model_id = fxt_model.id_
        fxt_model.model_format = ModelFormat.BASE_FRAMEWORK
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(ModelRepo, "get_by_id", return_value=fxt_model) as mock_get_model,
        ):
            result_file, result_file_name = ModelRESTController.export_model(
                project_id=project_id,
                model_storage_id=model_storage_id,
                model_id=model_id,
                model_only=True,
            )

            mock_get_project.assert_called_once()
            mock_get_model.assert_called_once()
            compare(result_file.read(), fxt_zip_file_data.read(), ignore_eq=True)
            compare(result_file_name, "PyTorch_model.zip", ignore_eq=True)

    @pytest.mark.parametrize("model_only", [True, False])
    def test_export_onnx_model(
        self,
        fxt_project,
        fxt_model,
        fxt_zip_file_data,
        model_only,
    ) -> None:
        fxt_model.model_format = ModelFormat.ONNX
        fxt_model.optimization_type = ModelOptimizationType.ONNX
        project_id = fxt_project.id_
        model_storage_id = fxt_model.model_storage.id_
        model_id = fxt_model.id_
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(ModelRepo, "get_by_id", return_value=fxt_model) as mock_get_model,
        ):
            result_file, result_file_name = ModelRESTController.export_model(
                project_id=project_id,
                model_storage_id=model_storage_id,
                model_id=model_id,
                model_only=model_only,
            )

            mock_get_project.assert_called_once()
            mock_get_model.assert_called_once()
            compare(result_file.read(), fxt_zip_file_data.read(), ignore_eq=True)
            compare(result_file_name, "ONNX_model.zip", ignore_eq=True)

    @pytest.mark.parametrize(
        "model_only, file_name, file_bytes",
        [
            (True, "OpenVINO_model.zip", "model_data"),
            (False, "OpenVINO_exportable_code.zip", "export_data"),
        ],
    )
    def test_export_optimized_model(
        self,
        fxt_model_storage,
        fxt_project,
        fxt_optimized_openvino_model,
        fxt_zip_file_data,
        model_only,
        file_name,
        file_bytes,
    ) -> None:
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project) as mock_get_project,
            patch.object(
                ModelRepo,
                "get_by_id",
                return_value=fxt_optimized_openvino_model,
            ) as mock_get_model,
        ):
            result_file, result_file_name = ModelRESTController.export_model(
                project_id=fxt_project.id_,
                model_storage_id=fxt_model_storage.id_,
                model_id=fxt_optimized_openvino_model.id_,
                model_only=model_only,
            )

            mock_get_project.assert_called_once()
            mock_get_model.assert_called_once()
            if file_bytes == "model_data":
                file_bytes = fxt_zip_file_data.read()
            else:
                file_bytes = b"DUMMY_EXPORTABLE_CODE_DATA"
            compare(result_file.read(), file_bytes, ignore_eq=True)
            compare(result_file_name, file_name, ignore_eq=True)

    def test_get_model_detail(
        self,
        fxt_project,
        fxt_model_storage,
        fxt_model,
        fxt_obsolete_model,
        fxt_optimized_model,
        fxt_detection_task,
        fxt_detection_label_schema,
        fxt_model_info_rest,
        fxt_obsolete_model_info_rest,
        fxt_dataset_counts,
    ) -> None:
        fxt_model_storage.project_id = fxt_project.id_
        fxt_model_storage.identifier = ModelStorageIdentifier(
            workspace_id=fxt_project.identifier.workspace_id,
            project_id=fxt_project.id_,
            model_storage_id=fxt_model_storage.id_,
        )
        fxt_detection_task.id_ = fxt_model.model_storage.task_node_id
        with (
            patch.object(
                ProjectRepo,
                "get_by_id",
                return_value=fxt_project,
            ) as mock_get_project,
            patch.object(
                ModelRepo,
                "get_optimized_models_by_trained_revision_id",
                return_value=[],
            ),
            patch.object(
                ModelStorageRepo,
                "get_by_task_node_id",
                return_value=[fxt_model_storage],
            ),
            patch.object(
                Project,
                "get_trainable_task_nodes",
                return_value=[fxt_detection_task],
            ),
            patch.object(otx_config_helper, "create", return_value={}),
            patch.object(
                StatisticsUseCase,
                "get_model_performance",
                return_value=fxt_optimized_model.performance,
            ),
            patch.object(
                ModelRepo,
                "get_latest_model_for_inference",
                return_value=fxt_optimized_model,
            ),
            patch.object(
                ModelRepo,
                "get_all_equivalent_model_ids",
                return_value=[fxt_optimized_model.id_],
            ),
            patch.object(
                LabelSchemaRepo,
                "get_latest_view_by_task",
                return_value=fxt_detection_label_schema,
            ),
            patch.object(
                LabelSchemaRepo,
                "get_by_id",
                return_value=fxt_detection_label_schema,
            ),
            patch.object(DatasetRepo, "__init__", new=do_nothing),
            patch.object(DatasetRepo, "count_per_media_type", return_value=fxt_dataset_counts) as mock_dataset_counts,
            patch.object(ModelService, "get_model_size", return_value=1),
        ):
            with patch.object(ModelRepo, "get_by_id", return_value=fxt_model):
                result = ModelRESTController.get_model_detail(
                    project_id=fxt_project.id_,
                    model_storage_id=fxt_model_storage.id_,
                    model_id=fxt_model.id_,
                )

                mock_get_project.assert_called_once_with(fxt_project.id_)
                mock_dataset_counts.assert_called_once_with(dataset_id=fxt_model.train_dataset_id)
                compare(result, fxt_model_info_rest, ignore_eq=True)

            mock_get_project.reset_mock()
            mock_dataset_counts.reset_mock()

            with patch.object(ModelRepo, "get_by_id", return_value=fxt_obsolete_model):
                result = ModelRESTController.get_model_detail(
                    project_id=fxt_project.id_,
                    model_storage_id=fxt_model_storage.id_,
                    model_id=fxt_obsolete_model.id_,
                )

                mock_get_project.assert_called_once_with(fxt_project.id_)
                mock_dataset_counts.assert_called_once_with(dataset_id=fxt_obsolete_model.train_dataset_id)
                compare(result, fxt_obsolete_model_info_rest, ignore_eq=True)

    def test_activate_model_storage(self, fxt_project, fxt_model_storage, fxt_model, fxt_optimized_model_leaf) -> None:
        session = make_session(
            organization_id=ID("test_organization_id"),
            workspace_id=ID("test_workspace_id"),
        )
        task_node_id = fxt_model_storage.task_node_id
        fxt_model_storage.project_id = fxt_project.id_
        fxt_model_storage.identifier = ModelStorageIdentifier(
            workspace_id=fxt_project.identifier.workspace_id,
            project_id=fxt_project.id_,
            model_storage_id=fxt_model_storage.id_,
        )

        # Hook for event publishing
        patch_publish_event = patch(
            "communication.rest_controllers.model_controller.publish_event",
            side_effect=publish_event,
        )
        expected_event_body = {
            "workspace_id": str(fxt_project.workspace_id),
            "project_id": str(fxt_project.id_),
            "task_node_id": str(fxt_model_storage.task_node_id),
            "model_storage_id": str(fxt_model_storage.id_),
            "base_model_id": str(fxt_model.id_),
            "inference_model_id": str(fxt_optimized_model_leaf.id_),
        }

        with (
            patch_publish_event as patched_publish_activated,
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project) as mock_get_project_by_id,
            patch.object(ModelStorageRepo, "get_by_id", return_value=fxt_model_storage) as mock_get_model_storage,
            patch.object(ModelService, "is_model_storage_activable", return_value=True),
            patch.object(ModelService, "activate_model_storage") as mock_activate_model_storage,
            patch.object(
                ModelService,
                "get_inference_active_model",
                return_value=fxt_optimized_model_leaf,
            ) as mock_get_inference_active_model,
            patch.object(ModelRESTController, "_get_per_model_info") as mock_get_model_info,
            patch.object(
                Project,
                "get_trainable_task_node_by_id",
                return_value=fxt_project.get_trainable_task_nodes()[0],
            ) as mock_validate_task_node_id,
            patch.object(ModelRegistrationClient, "register") as mock_registration_client_register,
            session_context(session=session),
        ):
            ModelRESTController.activate_model_storage(
                workspace_id=fxt_project.workspace_id,
                project_id=fxt_project.id_,
                model_storage_id=fxt_model_storage.id_,
                include_lifecycle_stage=True,
            )

        mock_get_project_by_id.assert_called_once_with(fxt_project.id_)
        mock_get_model_storage.assert_called_once_with(fxt_model_storage.id_)
        mock_validate_task_node_id.assert_called()
        mock_activate_model_storage.assert_called_once_with(model_storage=fxt_model_storage)
        mock_get_inference_active_model.assert_called_with(
            project_identifier=fxt_project.identifier,
            task_node_id=task_node_id,
        )
        mock_registration_client_register.assert_called_once_with(
            name=f"{str(fxt_project.id_)}-active",
            project=ANY,
            models=ANY,
            override=True,
        )
        mock_get_model_info.assert_called_once_with(
            task_node_id=task_node_id,
            model_storage_identifier=fxt_model_storage.identifier,
        )
        patched_publish_activated.assert_called_once_with(
            topic="model_activated", body=expected_event_body, headers_getter=ANY
        )

    @pytest.mark.parametrize("_fxt_project_name", ["fxt_project_with_detection_task", "fxt_chain_project"])
    def test_register_models(
        self,
        request,
        _fxt_project_name,
        fxt_model,
        fxt_model_2,
        fxt_optimized_model,
        fxt_optimized_model_2,
        fxt_session_ctx,
    ) -> None:
        # Arrange
        project = request.getfixturevalue(_fxt_project_name)
        project_tasks_nodes = project.get_trainable_task_nodes()
        is_task_chain = len(project_tasks_nodes) > 1
        task_id = project_tasks_nodes[0].id_
        task_id_2 = project_tasks_nodes[1].id_ if is_task_chain else None
        proto_project = ProjectMapper.forward(project)
        proto_model = ModelMapper.forward(
            model=fxt_model,
            organization_id=fxt_session_ctx.organization_id,
            workspace_id=fxt_session_ctx.workspace_id,
            project_id=project.id_,
            task_id=task_id,
            optimized_model_id=fxt_optimized_model.id_,
        )
        proto_model_2 = (
            ModelMapper.forward(
                model=fxt_model_2,
                organization_id=fxt_session_ctx.organization_id,
                workspace_id=fxt_session_ctx.workspace_id,
                project_id=project.id_,
                task_id=task_id_2,
                optimized_model_id=fxt_optimized_model_2.id_,
            )
            if is_task_chain
            else None
        )

        # Act
        with (
            session_context(session=fxt_session_ctx),
            patch.object(ModelRegistrationClient, "register", return_value=None) as mock_grpc_client_register,
            patch.object(ModelRegistrationClient, "close", return_value=None) as mock_grpc_client_close,
            patch.object(
                ModelService,
                "get_inference_active_model",
                return_value=fxt_optimized_model_2,
            ) as mock_get_other_inference_model,
            patch.object(Model, "get_base_model", return_value=fxt_model_2) as mock_get_other_model,
        ):
            ModelRESTController._register_model(
                project=project,
                model=fxt_model,
                optimized_model_id=fxt_optimized_model.id_,
                task_id=task_id,
            )

        # Assert
        if len(project_tasks_nodes) == 1:
            mock_grpc_client_register.assert_called_once_with(
                name=f"{str(project.id_)}-active",
                project=proto_project,
                models=[proto_model],
                override=True,
            )
        else:
            mock_get_other_inference_model.assert_called_with(
                project_identifier=project.identifier,
                task_node_id=project.get_trainable_task_nodes()[1].id_,
            )
            mock_get_other_model.assert_called_once()
            mock_grpc_client_register.assert_has_calls(
                [
                    call(
                        name=f"{str(project.id_)}-{str(task_id)}",
                        project=proto_project,
                        models=[proto_model],
                        override=True,
                    ),
                    call(
                        name=f"{str(project.id_)}-active",
                        project=proto_project,
                        models=[proto_model_2, proto_model],
                        override=True,
                    ),
                ]
            )
        mock_grpc_client_close.assert_called_once()


class TestModelRESTControllerUnit:
    @patch("communication.rest_controllers.model_controller.ProjectRepo.get_by_id")
    @patch("communication.rest_controllers.model_controller.ModelStorageRepo.get_by_id")
    @patch("communication.rest_controllers.model_controller.ModelService.get_inference_active_model")
    @patch("communication.rest_controllers.model_controller.ModelRESTController._get_per_model_info")
    @patch("communication.rest_controllers.model_controller.ModelRESTViews.model_storage_to_rest")
    def test_get_model_group_successful(
        self,
        mock_model_storage_to_rest,
        mock_get_per_model_info,
        mock_get_inference_active_model,
        mock_get_model_storage,
        mock_get_project,
    ):
        project_id = ID("project_id")
        model_storage_id = ID("model_storage_id")
        mock_project = MagicMock()
        mock_model_storage = MagicMock()
        mock_task_node = MagicMock()
        mock_base_active_model = MagicMock()
        mock_per_model_info = MagicMock()
        mock_rest_output = MagicMock()

        mock_get_project.return_value = mock_project
        mock_get_model_storage.return_value = mock_model_storage
        mock_project.get_trainable_task_nodes.return_value = [mock_task_node]
        mock_task_node.id_ = mock_model_storage.task_node_id
        mock_get_inference_active_model.return_value.get_base_model.return_value = mock_base_active_model
        mock_get_per_model_info.return_value = mock_per_model_info
        mock_model_storage_to_rest.return_value = mock_rest_output

        result = ModelRESTController.get_model_group(project_id, model_storage_id)

        assert result == mock_rest_output
        mock_get_project.assert_called_once_with(project_id)
        mock_get_model_storage.assert_called_once_with(model_storage_id)
        mock_get_inference_active_model.assert_called_once_with(
            project_identifier=mock_project.identifier, task_node_id=mock_task_node.id_
        )
        mock_get_per_model_info.assert_called_once_with(
            task_node_id=mock_task_node.id_,
            model_storage_identifier=mock_model_storage.identifier,
        )
        mock_model_storage_to_rest.assert_called_once_with(
            model_storage=mock_model_storage,
            per_model_info=mock_per_model_info,
            task_node_id=mock_task_node.id_,
            active_model=mock_base_active_model,
            include_lifecycle_stage=False,
        )

    @patch("communication.rest_controllers.model_controller.ProjectRepo.get_by_id")
    @patch("communication.rest_controllers.model_controller.ModelStorageRepo.get_by_task_node_id")
    @patch("communication.rest_controllers.model_controller.ModelService.get_inference_active_model")
    @patch("communication.rest_controllers.model_controller.ModelRESTController._get_per_model_info")
    @patch("communication.rest_controllers.model_controller.ModelRESTViews.model_storage_to_rest")
    def test_get_all_model_groups_successful(
        self,
        mock_model_storage_to_rest,
        mock_get_per_model_info,
        mock_get_inference_active_model,
        mock_get_by_task_node_id,
        mock_get_project_by_id,
    ):
        project_id = ID("project_id")
        task_id = ID("task_id")
        mock_project = MagicMock()
        mock_task_node = MagicMock()
        mock_model_storage = MagicMock()
        mock_base_active_model = MagicMock()
        mock_per_model_info = ["model_info"]
        mock_rest_output = MagicMock()

        mock_task_node.id_ = task_id
        mock_get_project_by_id.return_value = mock_project
        mock_project.get_trainable_task_nodes.return_value = [mock_task_node]
        mock_get_inference_active_model.return_value.get_base_model.return_value = mock_base_active_model
        mock_get_by_task_node_id.return_value = [mock_model_storage]
        mock_get_per_model_info.return_value = mock_per_model_info
        mock_model_storage_to_rest.return_value = mock_rest_output

        result = ModelRESTController.get_all_model_groups(project_id, task_id)

        assert result == {"model_groups": [mock_rest_output]}
        mock_get_project_by_id.assert_called_once_with(project_id)
        mock_project.get_trainable_task_nodes.assert_called_once()
        mock_get_inference_active_model.assert_called_once_with(
            project_identifier=mock_project.identifier, task_node_id=mock_task_node.id_
        )
        mock_get_by_task_node_id.assert_called_once_with(task_node_id=mock_task_node.id_)
        mock_get_per_model_info.assert_called_once_with(
            task_node_id=mock_task_node.id_,
            model_storage_identifier=mock_model_storage.identifier,
        )
        mock_model_storage_to_rest.assert_called_once_with(
            model_storage=mock_model_storage,
            per_model_info=mock_per_model_info,
            task_node_id=mock_task_node.id_,
            active_model=mock_base_active_model,
            include_lifecycle_stage=False,
        )

    @pytest.mark.parametrize(
        "scenario",
        [
            "identical",
            "different_schemas_equivalent_groups",
            "different_schemas_mismatching_groups",
            "different_groups",
        ],
    )
    def test_compare_labels_sync_status(
        self,
        scenario,
        fxt_mongo_id,
        fxt_project_identifier,
        fxt_classification_label_factory,
    ) -> None:
        labels = [fxt_classification_label_factory(i) for i in range(5)]
        label_group_1 = LabelGroup(
            name="group_1",
            labels=labels[:2],
        )
        label_group_2 = LabelGroup(
            name="group_2",
            labels=labels[2:4],
        )
        label_group_3 = LabelGroup(
            name="group_3",
            labels=labels[4:],
        )
        label_group_4 = LabelGroup(  # same name as label_group_1 but different labels
            name="group_1",
            labels=labels[:3],
        )
        label_schema_1 = LabelSchema(
            id_=fxt_mongo_id(21),
            project_id=fxt_project_identifier.project_id,
            label_groups=[label_group_1, label_group_2],
        )
        label_schema_2 = LabelSchema(
            id_=fxt_mongo_id(22),
            project_id=fxt_project_identifier.project_id,
            label_groups=[
                label_group_1,
                label_group_2,
            ],  # same groups as label_schema_1
        )
        label_schema_3 = LabelSchema(
            id_=fxt_mongo_id(23),
            project_id=fxt_project_identifier.project_id,
            label_groups=[
                label_group_1,
                label_group_3,
            ],  # different groups from label_schema_1
        )
        label_schema_4 = LabelSchema(
            id_=fxt_mongo_id(24),
            project_id=fxt_project_identifier.project_id,
            label_groups=[
                label_group_1,
                label_group_4,
            ],  # same group names as label_schema_1, but labels differ
        )
        label_schema_index = {
            label_schema_1.id_: label_schema_1,
            label_schema_2.id_: label_schema_2,
            label_schema_3.id_: label_schema_3,
            label_schema_4.id_: label_schema_4,
        }

        with patch.object(LabelSchemaRepo, "get_by_id", new=lambda self_, id_: label_schema_index[id_]):
            match scenario:
                case "identical":
                    assert ModelRESTController._compare_labels_sync_status(
                        project_identifier=fxt_project_identifier,
                        label_schema_1=label_schema_1,
                        label_schema_id_2=label_schema_1.id_,
                    )
                case "different_schemas_equivalent_groups":
                    assert ModelRESTController._compare_labels_sync_status(
                        project_identifier=fxt_project_identifier,
                        label_schema_1=label_schema_1,
                        label_schema_id_2=label_schema_2.id_,
                    )
                case "different_schemas_mismatching_groups":
                    assert not ModelRESTController._compare_labels_sync_status(
                        project_identifier=fxt_project_identifier,
                        label_schema_1=label_schema_1,
                        label_schema_id_2=label_schema_4.id_,
                    )
                case "different_groups":
                    assert not ModelRESTController._compare_labels_sync_status(
                        project_identifier=fxt_project_identifier,
                        label_schema_1=label_schema_1,
                        label_schema_id_2=label_schema_3.id_,
                    )
                case _:
                    raise ValueError(f"Unknown scenario: {scenario}")

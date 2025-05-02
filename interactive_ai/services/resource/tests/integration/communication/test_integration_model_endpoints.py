# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from http import HTTPStatus
from unittest.mock import patch

from freezegun import freeze_time
from testfixtures import compare

from communication.rest_controllers.model_controller import ModelRESTController
from communication.rest_views.model_rest_views import ModelRESTViews

from geti_types import CTX_SESSION_VAR, ID
from iai_core_py.configuration.elements.hyper_parameters import HyperParameters
from iai_core_py.entities.label import Domain, Label
from iai_core_py.entities.label_schema import LabelSchemaView
from iai_core_py.entities.metrics import Performance, ScoreMetric
from iai_core_py.entities.model import (
    Model,
    ModelConfiguration,
    ModelOptimizationType,
    ModelStatus,
    TrainingFramework,
    TrainingFrameworkType,
)
from iai_core_py.entities.model_storage import ModelStorage, ModelStorageIdentifier
from iai_core_py.repos import ConfigurableParametersRepo, LabelSchemaRepo, ModelRepo, ModelStorageRepo
from iai_core_py.services import ModelService


class TestModelRESTEndpoint:
    def test_model_storage_activation_endpoint(
        self,
        fxt_resource_rest,
        fxt_db_project_service,
    ) -> None:
        """
        <b>Description:</b>
        Check that the model storage activation endpoint makes the correct activation
        and returns the expected rest representation.

        <b>Input data:</b>
        Detection project

        <b>Expected results:</b>
        Test passes if the active model is switched and the correct rest view is returned

        <b>Steps</b>
        1. Create a project
        2. Create two model storages
        3. Create and save base and MO model for both model storages
        4. Call the model activation endpoint to activate the second model storage
        5. Verify that the new active model and the rest view are the expected ones
        """
        session = CTX_SESSION_VAR.get()
        project = fxt_db_project_service.create_annotated_detection_project()
        task_node = project.get_trainable_task_nodes()[0]
        model_storage_repo = ModelStorageRepo(project.identifier)

        model_storage_1 = fxt_db_project_service.model_storage_1
        model_storage_2 = ModelStorage(
            id_=model_storage_repo.generate_id(),
            project_id=project.id_,
            task_node_id=task_node.id_,
            model_template=model_storage_1.model_template,
        )
        model_storage_repo.save(model_storage_2)

        # Save base and mo models to model_storage_1
        base_active_model = fxt_db_project_service.create_and_save_model()
        assert base_active_model == ModelService.get_base_active_model(
            project_identifier=project.identifier,
            task_node_id=task_node.id_,
        )

        # Save base and mo models to model_storage_2
        dataset = fxt_db_project_service.dataset
        hyper_parameters: HyperParameters = ConfigurableParametersRepo(
            project_identifier=project.identifier
        ).get_or_create_hyper_parameters(model_storage=model_storage_2)
        configuration = ModelConfiguration(
            configurable_parameters=hyper_parameters.data,
            label_schema=fxt_db_project_service.label_schema_1,
        )
        base_activation_model = Model(
            project=project,
            model_storage=model_storage_2,
            train_dataset=dataset,
            configuration=configuration,
            id_=ModelRepo.generate_id(),
            performance=Performance(score=ScoreMetric(value=0.8, name="accuracy")),
            data_source_dict={"dummy.file": b"DUMMY_DATA"},
            model_status=ModelStatus.SUCCESS,
            has_xai_head=True,
            optimization_type=ModelOptimizationType.NONE,
        )
        inference_activation_model = Model(
            project=project,
            model_storage=model_storage_2,
            train_dataset=dataset,
            configuration=configuration,
            id_=ModelRepo.generate_id(),
            performance=Performance(score=ScoreMetric(value=0.8, name="accuracy")),
            previous_trained_revision=base_activation_model,
            data_source_dict={"dummy.file": b"DUMMY_DATA"},
            model_status=ModelStatus.SUCCESS,
            has_xai_head=True,
            optimization_type=ModelOptimizationType.MO,
        )
        ModelRepo(model_storage_2.identifier).save_many([base_activation_model, inference_activation_model])
        assert inference_activation_model == ModelRepo(model_storage_2.identifier).get_latest_model_for_inference()

        per_model_info = ModelRESTController._get_per_model_info(
            task_node_id=task_node.id_,
            model_storage_identifier=model_storage_2.identifier,
        )
        expected_rest = ModelRESTViews.model_storage_to_rest(
            model_storage=model_storage_2,
            per_model_info=per_model_info,
            task_node_id=task_node.id_,
            active_model=base_activation_model,
            include_lifecycle_stage=True,
        )

        endpoint = (
            f"/api/v1/organizations/{str(session.organization_id)}/workspaces/{session.workspace_id}/projects/{project.id_}/"
            f"model_groups/{model_storage_2.id_}:activate?include_lifecycle_stage=true"
        )

        with patch.object(ModelRESTController, "_register_model") as mock_register_model:
            result = fxt_resource_rest.post(endpoint, json={})

        assert result.status_code == HTTPStatus.OK
        assert base_activation_model == ModelService.get_base_active_model(
            project_identifier=project.identifier,
            task_node_id=task_node.id_,
        )
        mock_register_model.assert_called_once_with(
            project=project,
            model=base_activation_model,
            optimized_model_id=inference_activation_model.id_,
            task_id=task_node.id_,
        )
        compare(result.json(), expected_rest, ignore_eq=True)

    @freeze_time("2024-01-01 00:00:01")
    def test_get_all_models_endpoint(
        self,
        fxt_resource_rest,
        fxt_db_project_service,
    ) -> None:
        """
        <b>Description:</b>
        Check that the get all models endpoint returns the correct set of models, and that their details are correct
        in a task chain.
        <b>Input data:</b>
        Detection -> Classification project
        <b>Expected results:</b>
        Test passes if the models are return correctly, and a label sync is handled per task
        <b>Steps</b>
        1. Create a project
        2. Create models for both tasks.
        3. Verify that the model rest is correct
        4. Update the labels for the classification task
        5. Verify that the model rest is correct, the detection task is still in sync, the classification is not in sync
        """
        session = CTX_SESSION_VAR.get()
        project = fxt_db_project_service.create_annotated_detection_classification_project()
        # detection model
        fxt_db_project_service.create_and_save_model(
            training_framework=TrainingFramework(type=TrainingFrameworkType.OTX, version="1.6.0"),
        )
        # classification model
        fxt_db_project_service.create_and_save_model(
            task_node_index=1,
            training_framework=TrainingFramework(type=TrainingFrameworkType.OTX, version="2.2.0"),
        )

        endpoint = (
            f"/api/v1/organizations/{str(session.organization_id)}/workspaces/{str(session.workspace_id)}"
            f"/projects/{project.id_}/models"
        )

        # assert that the original project with no changes is returned correctly
        result = fxt_resource_rest.get(endpoint)
        expected_results = ModelRESTController.get_all_models(project_id=project.id_, active_only=True)
        compare(result.json(), expected_results, ignore_eq=True)

        # simulate adding a label to the classification task by updating the label schema ID
        fxt_db_project_service.label_schema_2.id_ = ID("new_id")
        new_label_schema = LabelSchemaView(
            label_schema=fxt_db_project_service.label_schema_2,
            id_=ID("new_label_schema_2"),
            label_groups=fxt_db_project_service.label_schema_2.get_groups(include_empty=True),
        )
        new_label = Label(name="new_label", domain=Domain.CLASSIFICATION, id_=ID("new_id"))
        new_label_schema.add_labels_to_group_by_group_name(group_name="default_classification", labels=[new_label])
        with (
            patch.object(
                LabelSchemaRepo,
                "get_latest_view_by_task",
                side_effect=[fxt_db_project_service.label_schema_1, fxt_db_project_service.label_schema_2],
            ),
            patch.object(
                LabelSchemaRepo,
                "get_by_id",
                side_effect=[new_label_schema, fxt_db_project_service.label_schema_2],
            ),
        ):
            result = fxt_resource_rest.get(endpoint)

        # assert that only the label schema for the classification task is out of sync
        assert result.json()["models"][0]["label_schema_in_sync"] is True  # Detection task
        assert result.json()["models"][1]["label_schema_in_sync"] is False  # classification task

    def test_model_purge_endpoint(self, fxt_resource_rest, fxt_db_project_service, fxt_model) -> None:
        """
        <b>Description:</b>
        Check that the model purge endpoint correctly purges a model and its data.

        <b>Expected results:</b>
        Test passes if the model is purged and its data is removed

        <b>Steps</b>
        1. Create a project and a model with a dummy file for its weights
        2. Call the model purge endpoint for this model and assert a 200 response
        3. Verify that model is correctly saved as purged and the weights are removed
        """
        session = CTX_SESSION_VAR.get()
        project = fxt_db_project_service.create_annotated_detection_project()
        workspace_id = project.workspace_id
        model_storage = fxt_db_project_service.model_storage_1
        base_model = fxt_db_project_service.create_and_save_model()
        model_storage_identifier = ModelStorageIdentifier(
            workspace_id=workspace_id, project_id=project.id_, model_storage_id=model_storage.id_
        )
        binary_repo = ModelRepo(model_storage_identifier).binary_repo
        assert binary_repo.exists(base_model.weight_paths["dummy.file"])
        endpoint = (
            f"/api/v1/organizations/{str(session.organization_id)}"
            f"/workspaces/{workspace_id}"
            f"/projects/{project.id_}"
            f"/model_groups/{model_storage.id_}"
            f"/models/{base_model.id_}:purge"
        )
        with (
            patch.object(ModelService, "get_base_active_model", return_value=fxt_model),
            patch.object(ModelRepo, "get_latest_successful_version", return_value=100),
        ):
            result = fxt_resource_rest.post(endpoint, json={})
        assert result.status_code == HTTPStatus.NO_CONTENT
        purged_model = ModelRepo(model_storage_identifier).get_by_id(base_model.id_)
        assert purged_model.purge_info.is_purged
        assert purged_model.exportable_code is None
        assert purged_model.weight_paths == {}
        assert not binary_repo.exists(base_model.weight_paths["dummy.file"])

    def test_purge_active_model(self, fxt_resource_rest, fxt_db_project_service) -> None:
        """
        <b>Description:</b>
        Check that the model purge endpoint fails when trying to purge the active model.

        <b>Expected results:</b>
        Test passes if the endpoint responds with a 422 response
        """
        session = CTX_SESSION_VAR.get()
        project = fxt_db_project_service.create_annotated_detection_project()
        workspace_id = project.workspace_id
        model_storage = fxt_db_project_service.model_storage_1
        base_model = fxt_db_project_service.create_and_save_model()
        endpoint = (
            f"/api/v1/organizations/{str(session.organization_id)}"
            f"/workspaces/{workspace_id}"
            f"/projects/{project.id_}"
            f"/model_groups/{model_storage.id_}"
            f"/models/{base_model.id_}:purge"
        )
        result = fxt_resource_rest.post(endpoint, json={})
        assert result.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    def test_download_purged_model(self, fxt_resource_rest, fxt_db_project_service) -> None:
        """
        <b>Description:</b>
        Check that downloading a purged model endpoint is not possible.

        <b>Expected results:</b>
        Test passes if the endpoint responds with a 422 response
        """
        session = CTX_SESSION_VAR.get()
        project = fxt_db_project_service.create_annotated_detection_project()
        workspace_id = project.workspace_id
        model_storage = fxt_db_project_service.model_storage_1
        base_model = fxt_db_project_service.create_and_save_model()
        model_storage_identifier = ModelStorageIdentifier(
            workspace_id=workspace_id, project_id=project.id_, model_storage_id=model_storage.id_
        )
        base_model.purge_info.is_purged = True
        ModelRepo(model_storage_identifier).save(base_model)
        endpoint = (
            f"/api/v1/organizations/{str(session.organization_id)}"
            f"/workspaces/{workspace_id}"
            f"/projects/{project.id_}"
            f"/model_groups/{model_storage.id_}"
            f"/models/{base_model.id_}/export"
        )
        result = fxt_resource_rest.get(endpoint)
        assert result.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

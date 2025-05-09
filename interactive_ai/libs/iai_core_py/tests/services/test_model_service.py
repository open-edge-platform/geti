# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest

from iai_core.adapters.model_adapter import DataSource
from iai_core.algorithms import ModelTemplateList
from iai_core.entities.model import Model, ModelPurgeInfo, NullModel
from iai_core.entities.model_storage import ModelStorageIdentifier
from iai_core.repos import ModelStorageRepo
from iai_core.repos.model_repo import ModelRepo, ModelStatusFilter
from iai_core.repos.storage.binary_repos import ModelBinaryRepo
from iai_core.services.model_service import ModelService
from iai_core.utils.exceptions import (
    PurgeActiveModelException,
    PurgeLatestModelException,
    PurgeOptimizedModelException,
    SDKModelNotFoundException,
)

from geti_types import ID


@pytest.fixture
def optimized_model():
    model = MagicMock(spec=Model)
    model.is_optimized.return_value = True
    model.size = 1024  # Assuming 1KB for test
    return model


@pytest.fixture
def non_optimized_model():
    model = MagicMock(spec=Model)
    model.is_optimized.return_value = False
    purge_info = ModelPurgeInfo()
    model.purge_info = purge_info
    model.weight_paths = {"weights": "path/to/weights"}
    model.exportable_code_adapter.data_source = MagicMock(spec=DataSource)
    model.exportable_code_adapter.data_source.binary_filename = "path/to/code"
    return model


@pytest.fixture
def purged_model():
    model = MagicMock(spec=Model)
    model.is_optimized.return_value = False
    purge_info = ModelPurgeInfo(is_purged=True)
    model.purge_info = purge_info
    return model


@pytest.fixture
def model_storage_identifier():
    return ModelStorageIdentifier(workspace_id="workspace_1", project_id="project_1", model_storage_id="storage_1")


class TestModelService:
    def test_get_or_create_model_storage(
        self,
        request,
        fxt_detection_task,
        fxt_model_template_detection,
        fxt_model_template_classification,
        fxt_empty_project_persisted,
    ) -> None:
        """
        <b>Description:</b>
        Tests the `get_or_create_model_storage` function of the ModelService,
        to verify that a model storage can be successfully created and retrieved for
        a specific task node and model template

        <b>Input data:</b>
        An empty project with a detection task and a detection model template

        <b>Expected results:</b>
        The test passes if:
            1. A model storage is successfully created and saved, in case no model
                storage for the task node and model template exists yet
            2. The model storage is successfully retrieved, in case it already exists
                for the specified task node and model template
            3. Passing an invalid model template id raises an error
            4. Passing a valid model template id, but with an invalid task type raises
                an error

        <b>Steps</b>
        1. Get list of model storages for task
        2. Call 'get_or_create_model_storage' to create a new model storage
        3. Call 'get_or_create_model_storage' again to retrieve an existing model
            storage
        4. Call 'get_or_create_model_storage' with an invalid model_template_id to
            ensure ValueError is raised
        5. Call 'get_or_create_model_storage' with a valid model_template_id, but with
            invalid task_type to ensure ValueError is raised
        """
        # Arrange
        model_storage_repo = ModelStorageRepo(fxt_empty_project_persisted.identifier)
        model_storage_list = list(model_storage_repo.get_by_task_node_id(task_node_id=fxt_detection_task.id_))
        available_algos = [
            model_template.model_template_id
            for model_template in ModelTemplateList().get_all()
            if model_template.task_type == fxt_detection_task.task_properties.task_type
        ]

        # Act
        # Test case 1: Successful model storage creation
        model_storage = ModelService.get_or_create_model_storage(
            project_identifier=fxt_empty_project_persisted.identifier,
            task_node=fxt_detection_task,
            model_template_id=fxt_model_template_detection.model_template_id,
        )
        request.addfinalizer(lambda: model_storage_repo.delete_by_id(model_storage.id_))
        # Test case 2: Model storage retrieval
        model_storage_exists = ModelService.get_or_create_model_storage(
            project_identifier=fxt_empty_project_persisted.identifier,
            task_node=fxt_detection_task,
            model_template_id=fxt_model_template_detection.model_template_id,
        )
        # Test case 3: Raise error for invalid model template id
        invalid_template_id = "non existing model template id"
        with pytest.raises(ValueError) as exc_non_existing:
            ModelService.get_or_create_model_storage(
                project_identifier=fxt_empty_project_persisted.identifier,
                task_node=fxt_detection_task,
                model_template_id=invalid_template_id,
            )
        # Test case 4: Raise error for model template with non-matching task type
        with pytest.raises(ValueError) as exc_non_matching:
            ModelService.get_or_create_model_storage(
                project_identifier=fxt_empty_project_persisted.identifier,
                task_node=fxt_detection_task,
                model_template_id=fxt_model_template_classification.model_template_id,
            )

        # Assert
        assert (
            str(exc_non_existing.value) == f"Algorithm with name '{invalid_template_id}' was not found for task "
            f"{fxt_detection_task.title} of type {fxt_detection_task.task_properties.task_type}. "
            f"Algorithms that are available to this task are: {available_algos}."
        )
        assert (
            str(exc_non_matching.value)
            == f"Algorithm with name '{fxt_model_template_classification.model_template_id}' was not found for task "
            f"{fxt_detection_task.title} of type {fxt_detection_task.task_properties.task_type}. "
            f"Algorithms that are available to this task are: {available_algos}."
        )
        assert model_storage not in model_storage_list
        assert model_storage.model_template == fxt_model_template_detection
        assert model_storage_exists == model_storage

    def test_is_model_storage_activable(self, fxt_model) -> None:
        model_storage = fxt_model.model_storage
        model_storage_repo = ModelStorageRepo(model_storage.project_identifier)
        model_storage_repo.save(model_storage)
        model_repo = ModelRepo(model_storage.identifier)

        try:
            # Empty model storage is not activable
            activable = ModelService.is_model_storage_activable(model_storage)

            assert not activable

            # Save a model inside the storage to make it activable
            model_repo.save(fxt_model)
            activable = ModelService.is_model_storage_activable(model_storage)

            assert activable

        finally:  # cleanup
            model_repo.delete_all()
            model_storage_repo.delete_by_id(model_storage.id_)

    def test_get_base_active_model(self, fxt_ote_id, fxt_project_identifier, fxt_model_storage, fxt_model) -> None:
        task_node_id = fxt_ote_id(1)
        with (
            patch.object(ModelService, "get_active_model_storage", return_value=fxt_model_storage) as mock_get_ms,
            patch.object(ModelRepo, "get_latest", return_value=fxt_model) as mock_get_model,
        ):
            ModelService.get_base_active_model(project_identifier=fxt_project_identifier, task_node_id=task_node_id)

        mock_get_ms.assert_called_once_with(
            project_identifier=fxt_project_identifier,
            task_node_id=task_node_id,
        )
        mock_get_model.assert_called_once_with(
            model_status_filter=ModelStatusFilter.IMPROVED, include_optimized_models=False
        )

    def test_get_inference_active_model(self, fxt_ote_id, fxt_project_identifier, fxt_model_storage, fxt_model) -> None:
        task_node_id = fxt_ote_id(1)
        with (
            patch.object(ModelService, "get_active_model_storage", return_value=fxt_model_storage) as mock_get_ms,
            patch.object(ModelRepo, "get_latest_model_for_inference", return_value=fxt_model) as mock_get_model,
        ):
            returned_model = ModelService.get_inference_active_model(
                project_identifier=fxt_project_identifier, task_node_id=task_node_id
            )

        mock_get_ms.assert_called_once_with(
            project_identifier=fxt_project_identifier,
            task_node_id=task_node_id,
        )
        mock_get_model.assert_called_once_with()
        assert returned_model == fxt_model

    def test_get_inference_active_model_id(self, fxt_ote_id, fxt_project_identifier, fxt_model_storage) -> None:
        task_node_id = fxt_ote_id(1)
        model_id = fxt_ote_id(2)
        with (
            patch.object(ModelService, "get_active_model_storage", return_value=fxt_model_storage) as mock_get_ms,
            patch.object(ModelRepo, "get_latest_model_id_for_inference", return_value=model_id) as mock_get_model,
        ):
            returned_model_id = ModelService.get_inference_active_model_id(
                project_identifier=fxt_project_identifier, task_node_id=task_node_id
            )

        mock_get_ms.assert_called_once_with(
            project_identifier=fxt_project_identifier,
            task_node_id=task_node_id,
        )
        mock_get_model.assert_called_once_with()
        assert returned_model_id == model_id

    def test_purge_active_model(self, fxt_ote_id, fxt_model_storage, fxt_model) -> None:
        with (
            patch.object(ModelStorageRepo, "get_by_id", return_value=fxt_model_storage),
            patch.object(ModelRepo, "get_by_id", return_value=fxt_model),
            patch.object(ModelService, "get_base_active_model", return_value=fxt_model),
            pytest.raises(PurgeActiveModelException),
        ):
            ModelService.purge_model_binaries(fxt_ote_id(0), fxt_ote_id(1), fxt_ote_id(2), fxt_ote_id(3), fxt_ote_id(4))

    def test_purge_latest_model(self, fxt_ote_id, fxt_model_storage, fxt_model) -> None:
        with (
            patch.object(ModelStorageRepo, "get_by_id", return_value=fxt_model_storage),
            patch.object(ModelRepo, "get_by_id", return_value=fxt_model),
            patch.object(ModelService, "get_base_active_model", return_value=NullModel()),
            patch.object(ModelRepo, "get_latest_successful_version", return_value=fxt_model.version),
            pytest.raises(PurgeLatestModelException),
        ):
            ModelService.purge_model_binaries(fxt_ote_id(0), fxt_ote_id(1), fxt_ote_id(2), fxt_ote_id(3), fxt_ote_id(4))

    def test_purge_optimized_model(self, fxt_ote_id, fxt_model_storage, fxt_model) -> None:
        with (
            patch.object(ModelStorageRepo, "get_by_id", return_value=fxt_model_storage),
            patch.object(ModelRepo, "get_by_id", return_value=fxt_model),
            patch.object(Model, "is_optimized", return_value=True),
            pytest.raises(PurgeOptimizedModelException),
        ):
            ModelService.purge_model_binaries(fxt_ote_id(0), fxt_ote_id(1), fxt_ote_id(2), fxt_ote_id(3), fxt_ote_id(4))

    def test_purge_not_found_model(self, fxt_ote_id, fxt_model_storage) -> None:
        with (
            patch.object(ModelStorageRepo, "get_by_id", return_value=fxt_model_storage),
            pytest.raises(SDKModelNotFoundException),
        ):
            ModelService.purge_model_binaries(fxt_ote_id(0), fxt_ote_id(1), fxt_ote_id(2), fxt_ote_id(3), fxt_ote_id(4))

    def test_get_model_size_for_optimized_model_returns_correct_size(
        self, optimized_model, model_storage_identifier
    ) -> None:
        size = ModelService.get_model_size(optimized_model, model_storage_identifier)
        assert size == 1024

    def test_get_model_size_for_non_optimized_model_includes_weights_and_code(
        self, non_optimized_model, model_storage_identifier
    ) -> None:
        with patch.object(ModelBinaryRepo, "get_object_size", return_value=512):
            size = ModelService.get_model_size(non_optimized_model, model_storage_identifier)
        assert size == 1024  # 512 for weights + 512 for exportable code

    def test_get_model_size_for_purged_model_returns_zero(self, purged_model, model_storage_identifier) -> None:
        size = ModelService.get_model_size(purged_model, model_storage_identifier)
        assert size == 0

    @mock.patch("iai_core.services.model_service.ModelStorageRepo")
    @mock.patch("iai_core.services.model_service.ModelRepo")
    @mock.patch("iai_core.services.model_service.NUM_MODELS_TO_KEEP_IN_STORAGE", 1)
    def test_should_purge_oldest_models_when_storage_limit_exceeded(self, mock_model_repo, fxt_model):
        # Setup
        identifier = ModelStorageIdentifier(ID(), ID(), ID())

        model_1 = fxt_model
        model_1.version = 1
        model_2 = fxt_model
        model_2.version = 2

        mock_model_repo.return_value.get_non_purged_base_models.return_value = [model_1, model_2]
        mock_purge = mock.patch("iai_core.services.model_service.ModelService.purge_model_binaries")

        # Execute
        with mock_purge as mocked_purge:
            ModelService.auto_archive_models(identifier)

        # Assert
        assert mocked_purge.call_count == 1

    @mock.patch("iai_core.services.model_service.ModelStorageRepo")
    @mock.patch("iai_core.services.model_service.ModelRepo")
    def test_should_not_purge_any_models_when_under_storage_limit(self, mock_model_repo, fxt_model):
        # Setup
        identifier = ModelStorageIdentifier(ID(), ID(), ID())

        model_1 = fxt_model
        model_1.version = 1

        mock_model_repo.return_value.get_non_purged_base_models.return_value = [model_1]
        mock_purge = mock.patch("iai_core.services.model_service.ModelService.purge_model_binaries")

        # Execute
        with mock_purge as mocked_purge:
            ModelService.auto_archive_models(identifier)

        # Assert
        mocked_purge.assert_not_called()

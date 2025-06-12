# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

import pytest
from geti_configuration_tools.training_configuration import PartialTrainingConfiguration

from communication.controllers.training_configuration_controller import TrainingConfigurationRESTController
from communication.views.training_configuration_rest_views import TrainingConfigurationRESTViews
from service.configuration_service import ConfigurationService
from storage.repos.partial_training_configuration_repo import PartialTrainingConfigurationRepo

from geti_types import ID
from iai_core.repos import TaskNodeRepo


@pytest.fixture
def fxt_partial_training_configuration():
    config = {
        "id_": ID("partial_training_configuration_id"),
        "task_id": "partial_training_configuration_task_id",
        "global_parameters": {
            "dataset_preparation": {
                "subset_split": {
                    "training": 80,
                    "validation": 10,
                    "test": 10,
                }
            }
        },
    }
    yield PartialTrainingConfiguration.model_validate(config)


@pytest.fixture
def fxt_partial_training_configuration_rest_view(fxt_partial_training_configuration):
    yield {
        "task_id": fxt_partial_training_configuration.task_id,
        "dataset_preparation": {
            "subset_split": [
                {
                    "default_value": 70,
                    "description": "Percentage of data to use for training",
                    "key": "training",
                    "max_value": 100,
                    "min_value": 1,
                    "name": "Training percentage",
                    "type": "int",
                    "value": 80,
                },
                {
                    "default_value": 20,
                    "description": "Percentage of data to use for validation",
                    "key": "validation",
                    "max_value": 100,
                    "min_value": 1,
                    "name": "Validation percentage",
                    "type": "int",
                    "value": 10,
                },
                {
                    "default_value": 10,
                    "description": "Percentage of data to use for testing",
                    "key": "test",
                    "max_value": 100,
                    "min_value": 1,
                    "name": "Test percentage",
                    "type": "int",
                    "value": 10,
                },
            ],
        },
        "training": [],
        "evaluation": [],
    }


class TestTrainingConfigurationController:
    @patch.object(TaskNodeRepo, "exists", return_value=True)
    def test_configurable_parameters_to_rest(
        self,
        request,
        fxt_project_identifier,
        fxt_training_configuration_task_level,
        fxt_training_configuration_task_level_rest_view,
        fxt_partial_training_configuration_manifest_level,
        fxt_training_configuration_full_rest_view,
    ) -> None:
        # Arrange
        repo = PartialTrainingConfigurationRepo(fxt_project_identifier)
        request.addfinalizer(lambda: repo.delete_all())

        repo.save(fxt_training_configuration_task_level)

        # Act & Assert
        # check that only task level configuration is present
        config_rest = TrainingConfigurationRESTController.get_configuration(
            project_identifier=fxt_project_identifier,
            task_id=fxt_training_configuration_task_level.task_id,
        )
        assert config_rest == fxt_training_configuration_task_level_rest_view

        repo.save(fxt_partial_training_configuration_manifest_level)

        config_rest = TrainingConfigurationRESTController.get_configuration(
            project_identifier=fxt_project_identifier,
            task_id=fxt_partial_training_configuration_manifest_level.task_id,
            model_manifest_id=fxt_partial_training_configuration_manifest_level.model_manifest_id,
        )

        # check that both task level and manifest level configuration are present
        assert config_rest == fxt_training_configuration_full_rest_view

    @patch.object(TaskNodeRepo, "exists", return_value=True)
    def test_partial_configurable_parameters_to_rest(
        self,
        request,
        fxt_project_identifier,
        fxt_partial_training_configuration,
        fxt_partial_training_configuration_rest_view,
    ) -> None:
        # Arrange
        repo = PartialTrainingConfigurationRepo(fxt_project_identifier)
        request.addfinalizer(lambda: repo.delete_all())

        repo.save(fxt_partial_training_configuration)

        # Act & Assert
        # check that only task level configuration is present
        config_rest = TrainingConfigurationRESTController.get_configuration(
            project_identifier=fxt_project_identifier,
            task_id=ID(fxt_partial_training_configuration.task_id),
            model_manifest_id=fxt_partial_training_configuration.model_manifest_id,
        )

        # check that both task level and manifest level configuration are present
        assert config_rest == fxt_partial_training_configuration_rest_view

    @patch.object(TaskNodeRepo, "exists", return_value=True)
    def test_get_configuration_from_model_id(
        self, fxt_project_identifier, fxt_partial_training_configuration_manifest_level, fxt_model_storage
    ) -> None:
        # Arrange
        model_id = ID("model_id")
        fxt_partial_training_configuration_manifest_level.model_manifest_id = (
            fxt_model_storage.model_template.model_template_id
        )
        model_hyperparams_dict = fxt_partial_training_configuration_manifest_level.hyperparameters.model_dump()
        fxt_partial_training_configuration_manifest_level.global_parameters = None
        expected_rest_view = TrainingConfigurationRESTViews.training_configuration_to_rest(
            fxt_partial_training_configuration_manifest_level
        )

        # Act
        with patch.object(
            ConfigurationService,
            "get_configuration_from_model",
            return_value=(model_hyperparams_dict, fxt_model_storage),
        ) as mock_get_configuration_from_model:
            config_rest = TrainingConfigurationRESTController.get_configuration(
                project_identifier=fxt_project_identifier,
                task_id=ID(fxt_partial_training_configuration_manifest_level.task_id),
                model_id=model_id,
            )

        # Assert
        mock_get_configuration_from_model.assert_called_once_with(
            project_identifier=fxt_project_identifier,
            task_id=ID(fxt_partial_training_configuration_manifest_level.task_id),
            model_id=model_id,
        )
        assert config_rest == expected_rest_view

    @patch.object(TaskNodeRepo, "exists", return_value=True)
    def test_update_configuration(
        self,
        request,
        fxt_project_identifier,
        fxt_training_configuration_task_level,
        fxt_partial_training_configuration_manifest_level,
    ) -> None:
        # Arrange
        repo = PartialTrainingConfigurationRepo(fxt_project_identifier)
        request.addfinalizer(lambda: repo.delete_all())

        # Save initial configurations
        repo.save(fxt_training_configuration_task_level)
        repo.save(fxt_partial_training_configuration_manifest_level)

        # Create an update with modified parameters
        update_config_dict = {
            "task_id": fxt_training_configuration_task_level.task_id,
            "global_parameters": {
                "dataset_preparation": {
                    "subset_split": {
                        "training": 60,  # Changed from default 70
                        "validation": 30,  # Changed from default 20
                        "test": 10,
                    }
                }
            },
        }
        update_config = PartialTrainingConfiguration.model_validate(update_config_dict)

        # Act
        TrainingConfigurationRESTController.update_configuration(
            project_identifier=fxt_project_identifier,
            update_configuration=update_config,
        )

        # Assert
        updated_config = repo.get_task_only_configuration(
            task_id=fxt_training_configuration_task_level.task_id,
        )

        # Verify the update was applied correctly
        assert updated_config.global_parameters.dataset_preparation.subset_split.training == 60
        assert updated_config.global_parameters.dataset_preparation.subset_split.validation == 30
        assert updated_config.global_parameters.dataset_preparation.subset_split.test == 10

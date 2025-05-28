# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

from geti_configuration_tools.training_configuration import PartialTrainingConfiguration

from communication.controllers.training_configuration_controller import TrainingConfigurationRESTController
from storage.repos.partial_training_configuration_repo import PartialTrainingConfigurationRepo

from iai_core.repos import TaskNodeRepo


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

    def test_overlay_configurations(self, fxt_training_configuration_task_level) -> None:
        # Arrange
        # Create base configuration
        base_partial_config = PartialTrainingConfiguration(
            task_id="task_123",
            global_parameters={
                "dataset_preparation": {
                    "subset_split": {"training": 70, "validation": 20, "test": 10, "auto_selection": True},
                    "filtering": {"min_annotation_pixels": {"enable": False, "min_annotation_pixels": 1}},
                }
            },
        )

        # Create overlay configuration with some changes
        overlay_config_1 = PartialTrainingConfiguration(
            task_id="task_123",
            global_parameters={
                "dataset_preparation": {
                    "subset_split": {"training": 60, "validation": 30, "test": 10, "remixing": True},
                    "filtering": {"max_annotation_pixels": {"enable": True, "max_annotation_pixels": 5000}},
                }
            },
            hyperparameters={
                "training": {
                    "max_epochs": 32,
                    "learning_rate": 0.01,
                }
            },
        )

        overlay_config_2 = PartialTrainingConfiguration(
            task_id="task_123", hyperparameters={"training": {"learning_rate": 0.05}}
        )

        expected_partial_overlay_config = PartialTrainingConfiguration(
            task_id="task_123",
            global_parameters={
                "dataset_preparation": {
                    "subset_split": {
                        "training": 60,
                        "validation": 30,
                        "test": 10,
                        "remixing": True,
                        "auto_selection": True,
                    },
                    "filtering": {
                        "min_annotation_pixels": {"enable": False, "min_annotation_pixels": 1},
                        "max_annotation_pixels": {"enable": True, "max_annotation_pixels": 5000},
                    },
                }
            },
            hyperparameters={
                "training": {
                    "max_epochs": 32,
                    "learning_rate": 0.05,  # This should be the last value applied
                }
            },
        )

        # Act
        full_config_overlay = TrainingConfigurationRESTController._overlay_configurations(
            fxt_training_configuration_task_level, base_partial_config, overlay_config_1, overlay_config_2
        )
        partial_overlay = TrainingConfigurationRESTController._overlay_configurations(
            base_partial_config, overlay_config_1, overlay_config_2, validate_full_config=False
        )

        # Assert
        full_config_dataset_preparation = full_config_overlay.global_parameters.dataset_preparation
        assert partial_overlay.model_dump() == expected_partial_overlay_config.model_dump()
        assert full_config_dataset_preparation.subset_split.training == 60
        assert full_config_dataset_preparation.subset_split.validation == 30
        assert full_config_dataset_preparation.subset_split.remixing
        assert full_config_dataset_preparation.filtering.max_annotation_pixels.enable
        assert not full_config_dataset_preparation.filtering.min_annotation_pixels.enable
        assert full_config_dataset_preparation.filtering.min_annotation_pixels.min_annotation_pixels == 1
        assert full_config_overlay.hyperparameters.training.max_epochs == 32
        assert full_config_overlay.hyperparameters.training.learning_rate == 0.05

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from geti_configuration_tools.training_configuration import PartialTrainingConfiguration, TrainingConfiguration
from geti_types import ID

from service.configuration_service import ConfigurationService
from service.utils import delete_none_from_dict, merge_deep_dict
from storage.repos.partial_training_configuration_repo import PartialTrainingConfigurationRepo


class TestConfigurationService:
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
        full_config_overlay = ConfigurationService.overlay_training_configurations(
            fxt_training_configuration_task_level, base_partial_config, overlay_config_1, overlay_config_2
        )
        partial_overlay = ConfigurationService.overlay_training_configurations(
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

    def test_get_full_training_configuration(
        self,
        request,
        fxt_project_identifier,
        fxt_training_configuration_task_level,
        fxt_partial_training_configuration_manifest_level,
    ) -> None:
        # Arrange
        repo = PartialTrainingConfigurationRepo(fxt_project_identifier)
        request.addfinalizer(lambda: repo.delete_all())

        repo.save(fxt_training_configuration_task_level)
        repo.save(fxt_partial_training_configuration_manifest_level)

        overlay_config = merge_deep_dict(
            fxt_training_configuration_task_level.model_dump(),
            delete_none_from_dict(fxt_partial_training_configuration_manifest_level.model_dump()),
        )
        overlay_config["id_"] = ID(
            f"full_training_configuration_{fxt_partial_training_configuration_manifest_level.model_manifest_id}"
        )

        expected_config = TrainingConfiguration.model_validate(overlay_config)

        # Act & Assert
        full_config = ConfigurationService.get_full_training_configuration(
            project_identifier=fxt_project_identifier,
            task_id=fxt_training_configuration_task_level.task_id,
            model_manifest_id=fxt_partial_training_configuration_manifest_level.model_manifest_id,
            strict_validation=True,
        )
        assert full_config == expected_config

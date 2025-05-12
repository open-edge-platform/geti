# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from entities.training_configuration import NullTrainingConfiguration
from storage.repos.training_configuration_repo import TrainingConfigurationRepo

from geti_types import ID


class TestTrainingConfigurationRepo:
    def test_get_by_task_id(self, request, fxt_project_identifier, fxt_training_configuration):
        # Arrange
        repo = TrainingConfigurationRepo(fxt_project_identifier)
        request.addfinalizer(lambda: repo.delete_all())

        # Save the configuration to the repository
        repo.save(fxt_training_configuration)

        # Act
        retrieved_config = repo.get_by_task_id(fxt_training_configuration.task_id)

        # Assert
        assert retrieved_config.id_ == fxt_training_configuration.id_
        assert retrieved_config.task_id == fxt_training_configuration.task_id
        assert retrieved_config.global_parameters == fxt_training_configuration.global_parameters
        assert retrieved_config.hyperparameters == fxt_training_configuration.hyperparameters

        # Test with non-existent task ID
        non_existent_task_id = ID("non_existent_task_id")
        null_config = repo.get_by_task_id(non_existent_task_id)
        assert isinstance(null_config, NullTrainingConfiguration)

    def test_get_by_model_manifest_id(self, request, fxt_project_identifier, fxt_training_configuration):
        # Arrange
        repo = TrainingConfigurationRepo(fxt_project_identifier)
        request.addfinalizer(lambda: repo.delete_all())

        # Ensure configuration has a model_manifest_id
        fxt_training_configuration.model_manifest_id = "test-model-manifest-id"
        repo.save(fxt_training_configuration)

        # Act
        retrieved_config = repo.get_by_model_manifest_id(fxt_training_configuration.model_manifest_id)

        # Assert
        assert retrieved_config.id_ == fxt_training_configuration.id_
        assert retrieved_config.model_manifest_id == fxt_training_configuration.model_manifest_id
        assert retrieved_config.global_parameters == fxt_training_configuration.global_parameters
        assert retrieved_config.hyperparameters == fxt_training_configuration.hyperparameters

        # Test with non-existent model manifest ID
        non_existent_manifest_id = "non-existent-manifest-id"
        null_config = repo.get_by_model_manifest_id(non_existent_manifest_id)
        assert isinstance(null_config, NullTrainingConfiguration)

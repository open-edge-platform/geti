# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from iai_core.entities.project_configuration import NullProjectConfiguration, TaskConfig
from iai_core.repos.project_configuration_repo import ProjectConfigurationRepo

from geti_types import ID


class TestProjectConfigurationRepo:
    def test_update_task_config(self, request, fxt_project_identifier, fxt_project_configuration):
        # Arrange
        repo = ProjectConfigurationRepo(fxt_project_identifier)
        request.addfinalizer(lambda: repo.delete_all())

        # Act - Save the configuration
        repo.save(fxt_project_configuration)

        # Assert - Verify saved configuration
        retrieved_config = repo.get_project_configuration()
        assert retrieved_config == fxt_project_configuration

        # Verify task 2 configuration before update
        assert retrieved_config.task_configs[1].auto_training.enable is False
        assert retrieved_config.task_configs[1].auto_training.min_images_per_label == 8

        # Act - Update task 2 configuration
        # Enable auto training and set min_images_per_label to 10
        new_task_2_config = TaskConfig(**retrieved_config.task_configs[1].model_dump())
        new_task_2_config.auto_training.enable = True
        new_task_2_config.auto_training.min_images_per_label = 10
        repo.update_task_config(new_task_2_config)

        # Save the updated configuration
        repo.update_task_config(new_task_2_config)

        # Act - Retrieve the updated configuration
        final_config = repo.get_project_configuration()

        # Assert - Verify the updated configuration
        assert final_config.id_ == fxt_project_configuration.id_
        assert len(final_config.task_configs) == 2

        # Verify task 1 configuration remains unchanged
        assert final_config.task_configs[0].task_id == "task_1"
        assert final_config.task_configs[0].auto_training.enable is True
        assert final_config.task_configs[0].auto_training.min_images_per_label == 5

        # Verify task 2 configuration was updated correctly
        assert final_config.task_configs[1].task_id == "task_2"
        assert final_config.task_configs[1].auto_training.enable is True
        assert final_config.task_configs[1].auto_training.min_images_per_label == 10

    def test_project_configuration_not_found(self, request, fxt_project_identifier):
        # Arrange
        repo = ProjectConfigurationRepo(fxt_project_identifier)
        request.addfinalizer(lambda: repo.delete_all())

        # Make sure no configurations exist
        repo.delete_all()

        # Act
        retrieved_config = repo.get_project_configuration()

        # Assert
        assert isinstance(retrieved_config, NullProjectConfiguration)
        assert retrieved_config.id_ == ID()
        assert retrieved_config.task_configs == []

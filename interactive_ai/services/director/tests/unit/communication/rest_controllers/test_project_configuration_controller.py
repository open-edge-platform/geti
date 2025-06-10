# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest
from geti_configuration_tools.project_configuration import PartialProjectConfiguration
from testfixtures import compare

from communication.controllers.project_configuration_controller import ProjectConfigurationRESTController
from communication.exceptions import ProjectConfigurationNotFoundException
from storage.repos.project_configuration_repo import ProjectConfigurationRepo

from geti_types import ID, ProjectIdentifier


class TestProjectConfigurationRESTController:
    def test_get_configuration(
        self,
        request,
        fxt_project_identifier,
        fxt_project_configuration,
        fxt_project_configuration_rest_view,
    ) -> None:
        # Arrange
        repo = ProjectConfigurationRepo(fxt_project_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        repo.save(fxt_project_configuration)

        # Act
        result = ProjectConfigurationRESTController.get_configuration(project_identifier=fxt_project_identifier)

        # Convert to dict to compare with expected output
        compare(result, fxt_project_configuration_rest_view, ignore_eq=True)

    def test_get_configuration_not_found(self) -> None:
        project_id = ID("dummy_project_id")
        workspace_id = ID("dummy_workspace_id")
        project_identifier = ProjectIdentifier(workspace_id=workspace_id, project_id=project_id)

        with pytest.raises(ProjectConfigurationNotFoundException):
            ProjectConfigurationRESTController.get_configuration(project_identifier=project_identifier)

    def test_update_configuration(
        self,
        request,
        fxt_project_identifier,
        fxt_project_configuration,
    ) -> None:
        # Arrange
        repo = ProjectConfigurationRepo(fxt_project_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        repo.save(fxt_project_configuration)

        # Ensure there's at least one task config
        assert len(fxt_project_configuration.task_configs) > 0
        task_id = fxt_project_configuration.task_configs[0].task_id

        # Store original values for later comparison
        original_config = repo.get_project_configuration()
        original_task = next(t for t in original_config.task_configs if t.task_id == task_id)
        original_min_images = original_task.auto_training.min_images_per_label
        original_enable = original_task.auto_training.enable
        original_constraints_min_images = original_task.training.constraints.min_images_per_label

        # Create a partial update with only min_images_per_label modified
        new_min_images = original_min_images + 5
        partial_update = PartialProjectConfiguration.model_validate(
            {
                "task_configs": [
                    {
                        "task_id": "task_1",
                        "auto_training": {"min_images_per_label": new_min_images},
                    }
                ]
            }
        )

        # Act
        ProjectConfigurationRESTController.update_configuration(
            project_identifier=fxt_project_identifier,
            update_configuration=partial_update,
        )

        # Assert
        updated_config = repo.get_project_configuration()
        updated_task = next(t for t in updated_config.task_configs if t.task_id == task_id)

        # Verify the specified parameter was updated
        assert updated_task.auto_training.min_images_per_label == new_min_images

        # Verify other parameters were not modified
        assert updated_task.auto_training.enable == original_enable
        assert updated_task.training.constraints.min_images_per_label == original_constraints_min_images

        # Verify other task configs were not modified
        for original_task, updated_task in zip(
            [t for t in original_config.task_configs if t.task_id != task_id],
            [t for t in updated_config.task_configs if t.task_id != task_id],
        ):
            assert original_task == updated_task

    def test_update_configuration_empty(
        self,
        request,
        fxt_project_identifier,
        fxt_project_configuration,
    ) -> None:
        # Arrange
        repo = ProjectConfigurationRepo(fxt_project_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        repo.save(fxt_project_configuration)

        # Ensure there's at least one task config
        assert len(fxt_project_configuration.task_configs) > 0

        # Store original values for later comparison
        original_config = repo.get_project_configuration()

        # Create an empty update
        empty_update_1 = PartialProjectConfiguration.model_validate({"task_configs": []})
        empty_update_2 = PartialProjectConfiguration.model_validate({})

        # Act
        ProjectConfigurationRESTController.update_configuration(
            project_identifier=fxt_project_identifier,
            update_configuration=empty_update_1,
        )
        ProjectConfigurationRESTController.update_configuration(
            project_identifier=fxt_project_identifier,
            update_configuration=empty_update_2,
        )

        # Assert
        updated_config = repo.get_project_configuration()
        assert updated_config == original_config, "Configuration should remain unchanged when empty update is provided"

    @pytest.mark.parametrize(
        "invalid_update, error_location",
        [
            (
                {"non_existent_field": "value"},
                "non_existent_field",
            ),
            (
                {"task_configs": [{"task_id": "task_1", "invalid_field": "value"}]},
                "task_configs.0.invalid_field",
            ),
            (
                {"task_configs": [{"task_id": "task_1", "auto_training": {"unknown_param": "value"}}]},
                "task_configs.0.auto_training.unknown_param",
            ),
            (
                {"task_configs": [{"task_id": "task_1", "training": {"invalid_section": {"param": "value"}}}]},
                "task_configs.0.training.invalid_section",
            ),
        ],
    )
    def test_update_configuration_unrecognized_params(
        self,
        request,
        fxt_project_identifier,
        fxt_project_configuration,
        invalid_update,
        error_location,
    ) -> None:
        # Arrange
        repo = ProjectConfigurationRepo(fxt_project_identifier)
        request.addfinalizer(lambda: repo.delete_all())
        repo.save(fxt_project_configuration)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            # This should fail during validation
            partial_update = PartialProjectConfiguration.model_validate(invalid_update)
            ProjectConfigurationRESTController.update_configuration(
                project_identifier=fxt_project_identifier,
                project_configuration=partial_update,
            )

        # Verify the error message contains the unrecognized field
        assert error_location in str(exc_info.value), f"Error should mention '{error_location}'"

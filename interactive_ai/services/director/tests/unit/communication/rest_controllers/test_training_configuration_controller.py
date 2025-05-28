# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from unittest.mock import patch

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

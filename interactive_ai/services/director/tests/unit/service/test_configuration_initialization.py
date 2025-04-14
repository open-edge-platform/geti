# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import inspect
from typing import cast
from unittest.mock import patch

from testfixtures import compare

from configuration import ComponentRegisterEntry, ConfigurableComponentRegister
from coordination.configuration_manager.task_node_config import AnomalyTaskNodeConfig
from coordination.dataset_manager.dataset_counter_config import (
    AnomalyDatasetCounterConfig,
    ClassificationDatasetCounterConfig,
    KeypointDetectionCounterConfig,
)
from service.project_service import ProjectService

from sc_sdk.configuration.elements.component_parameters import ComponentType
from sc_sdk.configuration.enums.utils import get_enum_names
from sc_sdk.repos import ConfigurableParametersRepo, ProjectRepo


class TestConfigurationInitializer:
    def test_validate_component_register(self):
        for component in ComponentType:
            if component is not ComponentType.NULL_COMPONENT and component.name not in get_enum_names(
                ConfigurableComponentRegister
            ):
                raise KeyError(
                    f"Unregistered configurable component found. Please add the "
                    f"configuration for {component.name} to the ConfigurableComponentRegister "
                    f"in {inspect.getfile(ConfigurableComponentRegister)}"
                )

    def test_initialize_project_configuration(
        self,
        request,
        fxt_pipeline_project,
        fxt_project_with_detection_task,
        fxt_project_with_segmentation_task,
        fxt_project_with_anomaly_classification_task,
    ):
        # Arrange
        projects_to_test = [
            fxt_project_with_segmentation_task,
            fxt_project_with_detection_task,
            fxt_pipeline_project,
            fxt_project_with_anomaly_classification_task,
        ]

        for project in projects_to_test:
            # Act
            project_repo = ProjectRepo()
            project_repo.save(project)
            request.addfinalizer(lambda: project_repo.delete_by_id(project.id_))

            ProjectService.init_configuration(project_id=project.id_)
            repo = ConfigurableParametersRepo(project.identifier)
            request.addfinalizer(lambda: repo.delete_all())

            for component in ComponentType:
                if component == ComponentType.NULL_COMPONENT:
                    continue
                task_ids = []
                task_types = []
                if component.metadata.per_task:
                    for task in project.get_trainable_task_nodes():
                        task_ids.append(task.id_)
                else:
                    task_ids.append(None)
                    task_types.append(None)
                for task_id, task_type in zip(task_ids, task_types):
                    config = repo.get_latest_component_parameters(
                        component_type=component,
                        task_id=task_id,
                    )
                    repo_id = config.id
                    register_data = cast("ComponentRegisterEntry", ConfigurableComponentRegister[component.name].value)
                    config_type = register_data.get_configuration_type(task_type)
                    expected_config = config_type(id=repo_id)

                    # Assert
                    compare(config.data, expected_config, ignore_eq=True)

    def test_initialize_project_configuration_anomaly_case(self, request, fxt_project_with_anomaly_classification_task):
        # Arrange
        repo = ConfigurableParametersRepo(fxt_project_with_anomaly_classification_task.identifier)
        request.addfinalizer(lambda: repo.delete_all())
        task = fxt_project_with_anomaly_classification_task.get_trainable_task_nodes()[0]
        components_to_check = [ComponentType.DATASET_COUNTER, ComponentType.TASK_NODE]
        expected_config_types = [AnomalyDatasetCounterConfig, AnomalyTaskNodeConfig]

        # Act
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project_with_anomaly_classification_task),
        ):
            ProjectService.init_configuration(project_id=fxt_project_with_anomaly_classification_task.id_)
            for component, expected_config_type in zip(components_to_check, expected_config_types):
                config = repo.get_latest_component_parameters(
                    component_type=component,
                    task_id=task.id_,
                )
                expected_config = expected_config_type(id=config.id)  # type: ignore

            # Assert
            compare(config.data, expected_config, ignore_eq=True)

    def test_initialize_project_configuration_classification_case(self, request, fxt_pipeline_project):
        # Arrange
        project = fxt_pipeline_project
        repo = ConfigurableParametersRepo(project.identifier)
        request.addfinalizer(lambda: repo.delete_all())
        task = project.get_trainable_task_nodes()[0]

        # Act
        ProjectService.init_configuration(project_id=project.id_)
        config = repo.get_latest_component_parameters(
            component_type=ComponentType.DATASET_COUNTER,
            task_id=task.id_,
        )
        expected_config = ClassificationDatasetCounterConfig(id=config.id)  # type: ignore[call-arg]

        # Assert
        compare(config.data, expected_config, ignore_eq=True)

    def test_initialize_project_configuration_keypoint_detection_case(
        self, request, fxt_project_with_keypoint_detection_task
    ):
        # Arrange
        project = fxt_project_with_keypoint_detection_task
        repo = ConfigurableParametersRepo(project.identifier)
        request.addfinalizer(lambda: repo.delete_all())
        task = project.get_trainable_task_nodes()[0]

        # Act
        with (
            patch.object(ProjectRepo, "get_by_id", return_value=fxt_project_with_keypoint_detection_task),
        ):
            ProjectService.init_configuration(project_id=project.id_)
            config = repo.get_latest_component_parameters(
                component_type=ComponentType.DATASET_COUNTER,
                task_id=task.id_,
            )
            expected_config = KeypointDetectionCounterConfig(id=config.id)  # type: ignore[call-arg]

        # Assert
        compare(config.data, expected_config, ignore_eq=True)

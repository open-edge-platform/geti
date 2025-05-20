# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from geti_configuration_tools.project_configuration import ProjectConfiguration, TaskConfig

from communication.views.configurable_parameters_to_rest import ConfigurableParametersRESTViews


class ProjectConfigurationRESTViews(ConfigurableParametersRESTViews):
    """
    Converters between ProjectConfiguration models and their corresponding REST views
    """

    @classmethod
    def task_config_to_rest(cls, task_config: TaskConfig) -> dict:
        """
        Get the REST view of a task configuration

        :param task_config: Task configuration object
        :return: REST view of the task configuration
        """
        return {
            "task_id": task_config.task_id,
            "training": cls.configurable_parameters_to_rest(task_config.training),
            "auto_training": cls.configurable_parameters_to_rest(task_config.auto_training),
        }

    @classmethod
    def project_configuration_to_rest(cls, project_configuration: ProjectConfiguration) -> dict:
        """
        Get the REST view of a project configuration

        :param project_configuration: Project configuration object
        :return: REST view of the project configuration
        """
        return {
            "task_configs": [
                cls.task_config_to_rest(task_config) for task_config in project_configuration.task_configs
            ],
        }

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from geti_configuration_tools.project_configuration import (
    AutoTrainingParameters,
    ProjectConfiguration,
    TaskConfig,
    TrainingParameters,
)

PYDANTIC_TYPES_MAPPING = {
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "string": "str",
}


class ProjectConfigurationRESTViews:
    """
    Converters between ProjectConfiguration models and their corresponding REST views
    """

    @staticmethod
    def _parameter_to_rest(key: str, value: float | str | bool, json_schema: dict) -> dict:
        rest_view = {
            "key": key,
            "name": json_schema.get("title"),
            "description": json_schema.get("description"),
            "value": value,
            "default_value": json_schema.get("default"),
        }
        # optional parameter may contain `'anyOf': [{'exclusiveMinimum': 0, 'type': 'integer'}, {'type': 'null'}]`
        type_any_of = json_schema.get("anyOf", [{}])[0]
        rest_view["type"] = PYDANTIC_TYPES_MAPPING.get(json_schema.get("type", type_any_of.get("type")))
        if rest_view["type"] in ["int", "float"]:
            rest_view["min_value"] = json_schema.get("minimum", type_any_of.get("exclusiveMinimum"))
            rest_view["max_value"] = json_schema.get("maximum", type_any_of.get("exclusiveMaximum"))
        return rest_view

    @classmethod
    def _auto_training_parameters_to_rest(cls, auto_training_parameters: AutoTrainingParameters) -> list[dict]:
        """
        Get the REST view of auto-training parameters

        :param auto_training_parameters: Auto-training parameters object
        :return: REST view of the auto-training parameters
        """
        auto_training_dict = auto_training_parameters.model_dump()
        auto_training_parameters_schema = auto_training_parameters.model_json_schema()
        return [
            cls._parameter_to_rest(
                key=key,
                value=auto_training_dict[key],
                json_schema=auto_training_parameters_schema["properties"][key],
            )
            for key in auto_training_dict
        ]

    @classmethod
    def _training_parameters_to_rest(cls, training_parameters: TrainingParameters) -> dict:
        """
        Get the REST view of training parameters

        :param training_parameters: Training parameters object
        :return: REST view of the training parameters
        """
        constraints_dict = training_parameters.constraints.model_dump()
        constraints_schema = training_parameters.constraints.model_json_schema()
        return {
            "constraints": [
                cls._parameter_to_rest(
                    key=key,
                    value=constraints_dict[key],
                    json_schema=constraints_schema["properties"][key],
                )
                for key in constraints_dict
            ],
        }

    @classmethod
    def task_config_to_rest(cls, task_config: TaskConfig) -> dict:
        """
        Get the REST view of a task configuration

        :param task_config: Task configuration object
        :return: REST view of the task configuration
        """
        return {
            "task_id": task_config.task_id,
            "training": cls._training_parameters_to_rest(task_config.training),
            "auto_training": cls._auto_training_parameters_to_rest(task_config.auto_training),
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

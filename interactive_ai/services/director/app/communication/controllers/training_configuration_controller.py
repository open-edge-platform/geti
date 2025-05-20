# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import Any

from geti_configuration_tools.training_configuration import TrainingConfiguration

from communication.exceptions import TaskNodeNotFoundException
from communication.views.training_configuration_rest_views import TrainingConfigurationRESTViews
from storage.repos.training_configuration_repo import TrainingConfigurationRepo

from geti_telemetry_tools import unified_tracing
from geti_types import ID, ProjectIdentifier
from iai_core.repos import TaskNodeRepo


class TrainingConfigurationRESTController:
    @classmethod
    def _delete_none_from_dict(cls, d: dict) -> dict:
        """
        Remove None values recursively from dictionaries.

        :param d: Dictionary to process
        :return: Dictionary with None values removed
        """
        for key, value in list(d.items()):
            if isinstance(value, dict):
                cls._delete_none_from_dict(value)
            elif value is None:
                del d[key]
            elif isinstance(value, list):
                for v_i in value:
                    if isinstance(v_i, dict):
                        cls._delete_none_from_dict(v_i)
        return d

    @classmethod
    def _merge_deep_dict(cls, a: dict, b: dict) -> dict:
        """
        Recursively merge dictionaries 'b' into 'a' with deep dictionary support.

        This method merges keys and values from dictionary 'b' into dictionary 'a'.
        For nested dictionaries, it performs a recursive merge. For all other value types,
        values from 'b' overwrite values in 'a' when keys exist in both dictionaries.

        Example:
            a = {'x': 1, 'y': {'a': 2}}
            b = {'y': {'b': 3}, 'z': 4}
            result = {'x': 1, 'y': {'a': 2, 'b': 3}, 'z': 4}

        :param a: Target dictionary to merge into (modified in-place)
        :param b: Source dictionary whose values will be merged into 'a'
        :return: The modified dictionary 'a' containing merged values from 'b'
        """
        for key, val in b.items():
            if key in a:
                if isinstance(a[key], dict) and isinstance(val, dict):
                    cls._merge_deep_dict(a[key], val)
                else:
                    a[key] = val
            else:
                a[key] = val
        return a

    @classmethod
    @unified_tracing
    def get_configuration(
        cls,
        project_identifier: ProjectIdentifier,
        task_id: ID,
        model_manifest_id: str | None = None,
        exclude_none: bool = False,
    ) -> dict[str, Any]:
        """ """
        if not TaskNodeRepo(project_identifier).exists(task_id):
            raise TaskNodeNotFoundException(task_node_id=task_id)

        # TODO: load hyperparameters from model manifest and merge with the stored configuration
        training_configuration_repo = TrainingConfigurationRepo(project_identifier)
        training_config = training_configuration_repo.get_by_task_id(task_id)
        # Merge with algorithm level configuration if model_manifest_id is provided
        if model_manifest_id:
            algo_config = training_configuration_repo.get_by_model_manifest_id(model_manifest_id)
            training_config_dict = training_config.model_dump()
            algo_config_dict = cls._delete_none_from_dict(algo_config.model_dump())
            complete_config_dict = cls._merge_deep_dict(training_config_dict, algo_config_dict)
            complete_config_dict["id_"] = ""  # ID is required but is not relevant for the REST view
            training_config = TrainingConfiguration.model_validate(complete_config_dict)
        return TrainingConfigurationRESTViews.training_configuration_to_rest(
            training_configuration=training_config, exclude_none=exclude_none
        )

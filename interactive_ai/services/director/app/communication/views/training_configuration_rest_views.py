# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from typing import Any

from geti_configuration_tools.hyperparameters import Hyperparameters
from geti_configuration_tools.training_configuration import (
    GlobalParameters,
    NullTrainingConfiguration,
    TrainingConfiguration, PartialTrainingConfiguration,
)

from communication.views.configurable_parameters_to_rest import ConfigurableParametersRESTViews

DATASET_PREPARATION = "dataset_preparation"
TRAINING = "training"
EVALUATION = "evaluation"


class TrainingConfigurationRESTViews(ConfigurableParametersRESTViews):
    """
    Converters between objects and their corresponding REST views
    """

    @classmethod
    def _dataset_preparation_to_rest(
        cls, global_parameters: GlobalParameters, hyperparameters: Hyperparameters
    ) -> dict[str, Any]:
        # Return a combined view of global and hyperparameters for dataset preparation
        global_parameters_rest = (
            cls.configurable_parameters_to_rest(
                configurable_parameters=global_parameters.dataset_preparation,
            )
            if global_parameters.dataset_preparation
            else {}
        )
        hyperparameters_rest = (
            cls.configurable_parameters_to_rest(
                configurable_parameters=hyperparameters.dataset_preparation,
            )
            if hyperparameters.dataset_preparation
            else {}
        )
        if not isinstance(global_parameters_rest, dict) or not isinstance(hyperparameters_rest, dict):
            raise ValueError("Expected dictionary for global and hyperparameters REST views")
        return global_parameters_rest | hyperparameters_rest

    @classmethod
    def training_configuration_to_rest(cls, training_configuration: TrainingConfiguration) -> dict[str, Any]:
        """
        Get the REST view of a training configuration. Also supports PartialTrainingConfiguration.

        :param training_configuration: training configuration
        :return: REST view of the training configuration
        """
        if isinstance(training_configuration, NullTrainingConfiguration):
            return {}

        training_params_rest = (
            cls.configurable_parameters_to_rest(
                configurable_parameters=training_configuration.hyperparameters.training,
            )
            if training_configuration.hyperparameters and training_configuration.hyperparameters.training
            else {}
        )

        rest_view = {
            "task_id": training_configuration.task_id,
            DATASET_PREPARATION: cls._dataset_preparation_to_rest(
                global_parameters=training_configuration.global_parameters,
                hyperparameters=training_configuration.hyperparameters,
            ),
            TRAINING: training_params_rest,
            EVALUATION: [],  # Evaluation parameters are not yet available
        }

        if training_configuration.model_manifest_id:
            rest_view["model_manifest_id"] = training_configuration.model_manifest_id
        return rest_view

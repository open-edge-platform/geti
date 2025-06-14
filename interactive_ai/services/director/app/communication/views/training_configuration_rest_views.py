# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from collections import defaultdict
from typing import Any

from geti_configuration_tools.hyperparameters import (
    DatasetPreparationParameters as HyperparametersDatasetPreparationParameters,
)
from geti_configuration_tools.hyperparameters import EvaluationParameters, Hyperparameters, TrainingHyperParameters
from geti_configuration_tools.training_configuration import (
    GlobalDatasetPreparationParameters,
    GlobalParameters,
    NullTrainingConfiguration,
    PartialTrainingConfiguration,
    TrainingConfiguration,
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
        cls, global_parameters: GlobalParameters | None, hyperparameters: Hyperparameters | None
    ) -> dict[str, Any]:
        # Return a combined view of global and hyperparameters for dataset preparation
        global_parameters_rest = (
            cls.configurable_parameters_to_rest(
                configurable_parameters=global_parameters.dataset_preparation,
            )
            if global_parameters and global_parameters.dataset_preparation
            else {}
        )
        hyperparameters_rest = (
            cls.configurable_parameters_to_rest(
                configurable_parameters=hyperparameters.dataset_preparation,
            )
            if hyperparameters and hyperparameters.dataset_preparation
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
            else []
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

    @classmethod
    def training_configuration_from_rest(cls, rest_input: dict[str, Any]) -> PartialTrainingConfiguration:
        """
        Convert REST input to a PartialTrainingConfiguration object.

        :param rest_input: REST input dictionary
        :return: TrainingConfiguration object
        """
        dataset_preparation = cls.configurable_parameters_from_rest(rest_input.pop(DATASET_PREPARATION, {}))
        training = cls.configurable_parameters_from_rest(rest_input.pop(TRAINING, {}))
        evaluation = cls.configurable_parameters_from_rest(rest_input.pop(EVALUATION, {}))

        global_parameters: dict = defaultdict(dict)
        hyperparameters: dict = defaultdict(dict)

        for field, _ in GlobalDatasetPreparationParameters.model_fields.items():
            global_parameters[DATASET_PREPARATION][field] = dataset_preparation.pop(field, None)

        for field, _ in HyperparametersDatasetPreparationParameters.model_fields.items():
            hyperparameters[DATASET_PREPARATION][field] = dataset_preparation.pop(field, None)

        for field, _ in TrainingHyperParameters.model_fields.items():
            hyperparameters[TRAINING][field] = training.pop(field, None)

        for field, _ in EvaluationParameters.model_fields.items():
            hyperparameters[EVALUATION][field] = evaluation.pop(field, None)

        # add remaining parameters for validation (extra parameters should not be present)
        global_parameters[DATASET_PREPARATION].update(dataset_preparation)
        hyperparameters[TRAINING].update(training)
        hyperparameters[EVALUATION].update(evaluation)

        # Convert defaultdict to regular dicts for the model validation
        global_parameters = dict(global_parameters)
        hyperparameters = dict(hyperparameters)
        global_parameters.pop("default_factory", None)
        hyperparameters.pop("default_factory", None)

        dict_model = {
            "global_parameters": global_parameters,
            "hyperparameters": hyperparameters,
        }

        return PartialTrainingConfiguration.model_validate(dict_model | rest_input)

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the TaskEnvironment entity."""

from typing import TypeVar

import iai_core.configuration.helper as cfg_helper
from iai_core.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core.entities.label import Label
from iai_core.entities.label_schema import LabelSchema
from iai_core.entities.model import Model, ModelConfiguration
from iai_core.entities.model_template import ModelTemplate

TypeVariable = TypeVar("TypeVariable", bound=ConfigurableParameters)


class TaskEnvironment:
    """Defines the machine learning environment the task runs in.

    :param model_template: The model template used for this task
    :param model: Model to use; if not specified, the task must be either weight-less
        or use pre-trained or randomly initialised weights.
    :param hyper_parameters: Set of hyper parameters
    :param label_schema: Label schema associated to this task
    """

    def __init__(
        self,
        model_template: ModelTemplate,
        model: Model | None,
        hyper_parameters: ConfigurableParameters,
        label_schema: LabelSchema,
    ):
        self.model_template = model_template
        self.model = model
        self.__hyper_parameters = hyper_parameters
        self.label_schema = label_schema

    def __repr__(self):
        """String representation of the TaskEnvironment object."""
        return (
            f"TaskEnvironment(model={self.model}, label_schema={self.label_schema}, "
            f"hyper_params={self.__hyper_parameters})"
        )

    def __eq__(self, other: object) -> bool:
        """Compares two TaskEnvironment objects."""
        if isinstance(other, TaskEnvironment):
            return (
                self.model == other.model
                and self.label_schema == other.label_schema
                # TODO get_hyperparameters should return Union rather than TypeVariable
                and self.get_hyper_parameters(instance_of=None)  # type: ignore
                == other.get_hyper_parameters(instance_of=None)
            )
        return False

    def get_labels(self, include_empty: bool = False) -> list[Label]:
        """Return the labels in this task environment (based on the label schema).

        :param include_empty: Include the empty label if True
        :return: List of labels
        """
        return self.label_schema.get_labels(include_empty)

    def get_hyper_parameters(self, instance_of: type[TypeVariable] | None = None) -> TypeVariable:
        """Returns Configuration for the task, de-serialized as type specified in `instance_of`.

        If the type of the configurable parameters is unknown, a generic
        ConfigurableParameters object with all available parameters can be obtained
        by calling method with instance_of = None.

        Example:
            >>> self.get_hyper_parameters(instance_of=TorchSegmentationConfig)
            TorchSegmentationConfig()

        :param instance_of: subtype of ModelConfig of the hyperparamters. Defaults to None.
        :return: ConfigurableParameters entity
        """
        if instance_of is None:
            # If the instance_of is None, the type variable is not defined so the
            # return type won't be deduced correctly
            return self.__hyper_parameters  # type: ignore

        # Otherwise, update the base config according to what is stored in the repo.
        base_config = instance_of(header=self.__hyper_parameters.header)  # type: ignore

        cfg_helper.substitute_values(base_config, value_input=self.__hyper_parameters, allow_missing_values=True)

        return base_config

    def set_hyper_parameters(self, hyper_parameters: ConfigurableParameters) -> None:
        """Sets the hyper parameters for the task.

        Example:
            >>> self.set_hyper_parameters(hyper_parameters=TorchSegmentationParameters())
            None

        :param hyper_parameters: ConfigurableParameters entity to assign to task
        """
        if not isinstance(hyper_parameters, ConfigurableParameters):
            raise ValueError(f"Unable to set hyper parameters, invalid input: {hyper_parameters}")
        self.__hyper_parameters = hyper_parameters

    def get_model_configuration(self) -> ModelConfiguration:
        """Get the configuration needed to use the current model.

        That is the current set of:
            * configurable parameters
            * labels
            * label schema

        :return: Model configuration
        """
        return ModelConfiguration(self.__hyper_parameters, self.label_schema)

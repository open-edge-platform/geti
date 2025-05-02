"""This module implements the SubsetManagerConfig class"""

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
#

import attr
from iai_core.configuration.elements.configurable_parameters import ConfigurableParameters
from iai_core.configuration.elements.parameter_group import ParameterGroup, add_parameter_group
from iai_core.configuration.elements.primitive_parameters import (
    configurable_boolean,
    configurable_float,
    string_attribute,
)
from iai_core.configuration.enums.model_lifecycle import ModelLifecycle
from iai_core.configuration.ui_rules.rules import Action, Operator, Rule, UIRules


@attr.s
class SubsetManagerConfig(ConfigurableParameters):
    """
    Class that holds the configurable parameters for the subset manager.
    """

    # Header is required for all ConfigurableParameters
    header = string_attribute("Subset splitting")
    description = string_attribute(
        "Specify the distribution of annotated samples over the training, validation and test sets."
    )

    auto_subset_fractions = configurable_boolean(
        default_value=True,
        header="Automatically determine subset proportions",
        description="If this setting is enabled, the system will "
        "automatically determine the most optimal "
        "distribution of the annotated samples over training, "
        "validation and test set. Disable this setting to "
        "manually specify the proportions.",
        affects_outcome_of=ModelLifecycle.TRAINING,
    )

    train_validation_remixing = configurable_boolean(
        default_value=False,
        header="Remix training and validation sets",
        description="Turn on this setting to reshuffle training and validation subsets every training round. This "
        "strategy could improve the performance of the model on the testing subset, especially when there "
        "is new data added in between training rounds.",
    )

    @attr.s
    class __SubsetParameters(ParameterGroup):
        """
        This holds the fractions for the different subsets.
        """

        # Header is required for all parameter groups
        header = string_attribute("Subset distribution")
        # Description is optional, if not provided the default parameter group description will be used
        description = string_attribute(
            "Specify the distributions of annotated samples over training, validation and test set. These values must "
            "add up to 1, and will be rescaled if they do not add up correctly."
        )

        # If the boolean `auto_subset_fractions` is set to `False`, this UI rule will SHOW the parameter it is applied
        # to. We apply this rule to train, validation and test proportion, and make them hidden from the ui by default.
        __ui_rules = UIRules(
            rules=[
                Rule(
                    parameter=["auto_subset_fractions"],
                    value=False,
                    operator=Operator.EQUAL_TO,
                )
            ],
            action=Action.SHOW,
        )

        train_proportion = configurable_float(
            default_value=0.5,
            min_value=0.1,
            max_value=1.0,
            header="Training set proportion",
            description="Fraction of annotated data that will be assigned to the training set",
            affects_outcome_of=ModelLifecycle.TRAINING,
            ui_rules=__ui_rules,
            warning="When the proportions do not add up to 1, they will be rescaled to add up to 1.",
        )

        validation_proportion = configurable_float(
            default_value=0.2,
            min_value=0.1,
            max_value=1.0,
            header="Validation set proportion",
            description="Fraction of annotated data that will be assigned to the validation set",
            affects_outcome_of=ModelLifecycle.TRAINING,
            ui_rules=__ui_rules,
            warning="When the proportions do not add up to 1, they will be rescaled to add up to 1.",
        )

        test_proportion = configurable_float(
            default_value=0.3,
            min_value=0.1,
            max_value=1.0,
            header="Test set proportion",
            description="Fraction of annotated data that will be assigned to the test set",
            affects_outcome_of=ModelLifecycle.TRAINING,
            ui_rules=__ui_rules,
            warning="When the proportions do not add up to 1, they will be rescaled to add up to 1.",
        )

    # Finally, add the parameter group to the configuration
    subset_parameters = add_parameter_group(__SubsetParameters)


@attr.s
class AnomalySubsetManagerConfig(ConfigurableParameters):
    """
    Class that holds the configurable parameters for the subset manager for anomaly classification tasks.
    """

    # Header is required for all ConfigurableParameters
    header = string_attribute("Subset splitting")
    description = string_attribute(
        "Specify the distribution of annotated samples over the training, validation and test sets."
    )

    auto_subset_fractions = configurable_boolean(
        default_value=True,
        header="Automatically determine subset proportions",
        description="If this setting is enabled, the system will "
        "automatically determine the most optimal "
        "distribution of the annotated samples over training, "
        "validation and test set. Disable this setting to "
        "manually specify the proportions.",
        affects_outcome_of=ModelLifecycle.TRAINING,
    )

    @attr.s
    class __SubsetParameters(ParameterGroup):
        """
        This holds the fractions for the different subsets.
        """

        # Header is required for all parameter groups
        header = string_attribute("Subset distribution")
        # Description is optional, if not provided the default parameter group description will be used
        description = string_attribute(
            "Specify the distributions of annotated samples over training, validation and test set."
        )

        # If the boolean `auto_subset_fractions` is set to `False`, this UI rule will SHOW the parameter it is applied
        # to. We apply this rule to train, validation and test proportion, and make them hidden from the ui by default.
        __ui_rules = UIRules(
            rules=[
                Rule(
                    parameter=["auto_subset_fractions"],
                    value=False,
                    operator=Operator.EQUAL_TO,
                )
            ],
            action=Action.SHOW,
        )

        train_proportion = configurable_float(
            default_value=0.5,
            min_value=0.1,
            max_value=1.0,
            header="Training set proportion",
            description="Fraction of annotated data that will be assigned to the "
            "training set. The distribution may deviate from the set values, because "
            "anomalous labels are not used in training and are only assigned "
            "to validation and testing subsets.",
            affects_outcome_of=ModelLifecycle.TRAINING,
            ui_rules=__ui_rules,
        )

        validation_proportion = configurable_float(
            default_value=0.2,
            min_value=0.1,
            max_value=1.0,
            header="Validation set proportion",
            description="Fraction of annotated data that will be assigned to the "
            "validation set. The distribution may deviate from the set values, because "
            "anomalous labels are not used in training and are only assigned "
            "to validation and testing subsets.",
            affects_outcome_of=ModelLifecycle.TRAINING,
            ui_rules=__ui_rules,
        )

        test_proportion = configurable_float(
            default_value=0.3,
            min_value=0.1,
            max_value=1.0,
            header="Test set proportion",
            description="Fraction of annotated data that will be assigned to the "
            "test set. The distribution may deviate from the set values, because "
            "anomalous labels are not used in training and are only assigned "
            "to validation and testing subsets.",
            affects_outcome_of=ModelLifecycle.TRAINING,
            ui_rules=__ui_rules,
        )

    # Finally, add the parameter group to the configuration
    subset_parameters = add_parameter_group(__SubsetParameters)

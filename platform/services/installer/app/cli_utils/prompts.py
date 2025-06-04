# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

"""
Functions for generic prompts displayed by the CLI.
"""

import rich_click as click

from configuration_models.base_config_model import ConfigurationField
from validators.errors import ValidationError


def prompt_for_configuration_value(config_field: ConfigurationField, prompt_message: str, **kwargs):  # noqa: ANN201
    """
    Prompt for value of config_field, by displaying prompt_message.
    Additional kwargs, if provided, are passed to the click.prompt or click.confirm function call.
    """
    if config_field.type is bool:
        value = click.confirm(prompt_message, **kwargs)
    else:
        value = click.prompt(prompt_message, type=config_field.type, **kwargs)

    if config_field.trim:
        value = value.strip()

    try:
        config_field.validation_callback(value)
        config_field.value = value
    except ValidationError as error:
        click.echo(f"The provided value is invalid: {error}")
        prompt_for_configuration_value(config_field, prompt_message, **kwargs)

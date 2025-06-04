# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
A module containing basic classes for creating Configuration models for installer operations.
"""

import logging
from abc import ABC
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, cast

import yaml

from validators.errors import ValidationError

logger = logging.getLogger(__name__)


@dataclass
class ConfigurationField:
    """
    type: Type of value of configuration field
    value: value of configuration field
    validation_callback: Function called to validate the value, ValidationError shall be raised in case of error
    required: if value of configuration field has to be set
    """

    type: type
    value: Any = None
    validation_callback: Callable = lambda x: True  # noqa: ARG005
    required: bool = True
    trim: bool = False


class BaseConfig(ABC):
    """
    An abstract base class for creating Config models.
    NOTE: All public instance variables of subclasses shall have ConfigurationField type
    """

    _ERR_MSG_INVALID_YAML = "The provided file does not contain the expected YAML document."

    def __repr__(self) -> str:
        def format_field_value(value):  # noqa: ANN001
            return f'"{value}"' if isinstance(value, str) else value

        fields = ", ".join([f"{key}={format_field_value(value)}" for key, value in self.__dict__.items()])
        return f"{self.__class__.__name__}({fields})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {str(self.convert_to_config_dict())}"

    def get_configuration_fields(self) -> list[tuple[str, ConfigurationField]]:
        """
        Returns a list of tuples with field_name, ConfigurationField items/
        List of configuration fields is composed from public Config instance attributes.
        """
        return [(k, v) for k, v in vars(self).items() if k[0] != "_"]

    def are_all_required_fields_set(self):  # noqa: ANN201
        """
        Check if all configuration fields marked as required are not empty

        :raises: ValidationError with list of error messages
        """
        field_validation_err_msgs = []
        for field_name, config_field in self.get_configuration_fields():
            logger.debug(
                f"Checking field {field_name}[required: {config_field.required}] with value {config_field.value}"
            )
            if config_field.required and config_field.value is None:
                err_msg = f"Required field {field_name} is not set."
                logger.warning(err_msg)
                field_validation_err_msgs.append(err_msg)

        if field_validation_err_msgs:
            raise ValidationError(error_messages=field_validation_err_msgs, message="Not all required fields are set")

    def are_all_fields_valid(self):  # noqa: ANN201
        """
        Run validation for all configuration fields in the config.

        :returns: List of error messages for each invalid field as strings
        """
        invalid_field_msgs = []
        for field_name, config_field in self.get_configuration_fields():
            try:
                logger.debug(f"Validating field {field_name} with {config_field.validation_callback}")
                if config_field.value is not None:
                    config_field.validation_callback(config_field.value)
            except ValidationError as error:
                logger.exception(error)
                invalid_field_msgs.append(f"Field {field_name} has invalid value - {error}")

        if invalid_field_msgs:
            raise ValidationError(error_messages=invalid_field_msgs, message="Some config fields have invalid values.")

    def validate(self):  # noqa: ANN201
        """
        Check if all required fields are set and have valid values.
        """
        logger.debug(f"Validating {self.__class__.__name__}")
        config_error_messages = []
        try:
            self.are_all_required_fields_set()
        except ValidationError as val_err:
            config_error_messages.extend(val_err.error_messages)

        try:
            self.are_all_fields_valid()
        except ValidationError as val_err:
            config_error_messages.extend(val_err.error_messages)

        if config_error_messages:
            raise ValidationError(error_messages=config_error_messages, message="Config field validation has failed")

    def convert_to_config_dict(self) -> dict:
        """
        Convert Config to a dict, with configuration field names as keys and configuration field values as values.
        """
        return {field_name: config_field.value for field_name, config_field in self.get_configuration_fields()}

    def load_config_from_yaml(self, yaml_file_path: str, validate: bool = False):  # noqa: ANN201
        """
        Load values for the Config from a yaml file.
        If validate flag is passed, ensure that are loaded fields have valid values.

        :raise ValidationError: If the target file is not a valid YAML document.
        """
        logger.debug(f"Loading configuration for {self.__class__.__name__} from: {yaml_file_path}")
        try:
            with open(yaml_file_path) as yaml_file:
                yaml_config = yaml.safe_load(yaml_file)
        except yaml.error.YAMLError as err:
            raise ValidationError(self._ERR_MSG_INVALID_YAML) from err

        if not isinstance(yaml_config, Mapping):
            raise ValidationError(self._ERR_MSG_INVALID_YAML)

        self._load_fields_from_mapping(yaml_config)

        if validate:
            self.validate()

    def _load_fields_from_mapping(self, mapping: Mapping) -> None:
        """Loads fields from the provided mapping into this configuration's state."""
        for field_name, configuration_field in self.get_configuration_fields():
            if field_name in mapping:
                if configuration_field.trim and mapping[field_name] is not None:
                    field_value = mapping[field_name].strip()
                else:
                    field_value = mapping[field_name]
                configuration_field.value = cast("configuration_field.type", field_value)  # type: ignore[name-defined]

    def log_config_info(self):  # noqa: ANN201
        """
        Log config parameters provided by the user.
        """
        config_dict = self.convert_to_config_dict()
        hidden_fields = [
            "user_password",
            "smtp_password",
            "user_pass_sha",
            "authorization_cookie_secret",
        ]
        log_message = "Config parameters provided by the user:"
        for key in config_dict:
            if key in hidden_fields:
                continue
            log_message += f"\n{key}: {str(config_dict[key])}"
        logger.info(log_message)

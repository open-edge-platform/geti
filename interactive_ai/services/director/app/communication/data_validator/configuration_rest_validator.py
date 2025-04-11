# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and
# your use of them is governed by the express license under which they were provided to
# you ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is,
# with no express or implied warranties, other than those that are expressly stated
# in the License.

"""This module implements the ConfigurationRestValidator class"""

import os
from typing import Any

import jsonschema

from geti_fastapi_tools.validation import RestApiValidator


class ConfigurationRestValidator(RestApiValidator):
    """
    Class to validate that json data for the configuration REST post endpoints adheres
    to the schema's for these endpoints
    """

    def __init__(self) -> None:
        """
        Initializes the schema's for the different configuration endpoints to validate
        against
        """
        base_dir = os.path.dirname(__file__) + "/../../../../api/schemas/"
        self.task_configuration_schema = self.load_schema_file_as_dict(
            base_dir + "configuration/requests/task_configuration.yaml"
        )
        self.task_chain_configuration_schema = self.load_schema_file_as_dict(
            base_dir + "configuration/requests/task_chain_configuration.yaml"
        )
        self.global_configuration_schema = self.load_schema_file_as_dict(
            base_dir + "configuration/requests/global_configuration.yaml"
        )
        self.full_configuration_schema = self.load_schema_file_as_dict(
            base_dir + "configuration/requests/full_configuration.yaml"
        )

    def validate_task_configuration(self, data: dict[str, Any]) -> None:
        """
        Validates task configuration json data

        :param data: Dictionary to validate
        """
        jsonschema.validate(data, schema=self.task_configuration_schema)

    def validate_task_chain_configuration(self, data: dict[str, list[dict[str, Any]]]) -> None:
        """
        Validates task chain configuration json data

        :param data: Dictionary to validate
        """
        jsonschema.validate(data, schema=self.task_chain_configuration_schema)

    def validate_global_configuration(self, data: dict[str, list[dict[str, Any]]]) -> None:
        """
        Validates global configuration json data

        :param data: Dictionary to validate
        """
        jsonschema.validate(data, schema=self.global_configuration_schema)

    def validate_full_configuration(self, data: dict[str, list[dict[str, Any]]]) -> None:
        """
        Validates global configuration json data

        :param data: Dictionary to validate
        """
        jsonschema.validate(data, schema=self.full_configuration_schema)

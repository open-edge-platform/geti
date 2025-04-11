# INTEL CONFIDENTIAL
#
# Copyright (C) 2024 Intel Corporation
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
import os
from typing import Any

import jsonschema

from geti_fastapi_tools.validation import RestApiValidator


class DeploymentPackageRESTValidator(RestApiValidator):
    """
    Class to validate that json data for the deployment package REST post endpoints adheres
    to the schema's for these endpoints
    """

    def __init__(self) -> None:
        base_dir = os.path.dirname(__file__) + "/../../../../api/schemas/"
        self.deployment_package_request_schema = self.load_schema_file_as_dict(
            base_dir + "deployment_package/requests/deployment_package_request.yaml"
        )

    def validate_deployment_package(self, data: dict[str, Any]) -> None:
        """
        Validates deployment package request

        :param data: JSON data from the request to be validated
        """
        jsonschema.validate(data, schema=self.deployment_package_request_schema)

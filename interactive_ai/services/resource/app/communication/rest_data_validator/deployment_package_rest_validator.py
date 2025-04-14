# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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

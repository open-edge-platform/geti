# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os
from typing import Any

import jsonschema

from geti_fastapi_tools.validation import RestApiValidator


class CodeDeploymentRESTValidator(RestApiValidator):
    """
    Class to validate that json data for the code deployment REST post endpoints adheres
    to the schema's for these endpoints
    """

    def __init__(self) -> None:
        base_dir = os.path.dirname(__file__) + "/../../../../api/schemas/"
        self.code_deployment_request_schema = self.load_schema_file_as_dict(
            base_dir + "code_deployment/requests/model_identifier_list.yaml"
        )

    def validate_code_deployment(self, data: dict[str, Any]) -> None:
        """
        Validates code deployment request

        :param data: JSON data from the request to be validated
        """
        jsonschema.validate(data, schema=self.code_deployment_request_schema)

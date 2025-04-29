# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the TrainingRestValidator class"""

import os

import jsonschema

from geti_fastapi_tools.validation import RestApiValidator


class TrainingRestValidator(RestApiValidator):
    def __init__(self) -> None:
        """
        Initializes the schema's for the train endpoint to validate against
        """
        base_dir = os.path.dirname(__file__) + "/../../../../api/schemas/"
        self.train_request_schema = self.load_schema_file_as_dict(base_dir + "training/requests/train_request.yaml")

    def validate_train_request(self, data: dict) -> None:
        """
        Validates train request endpoint json data

        :param data: Dictionary to validate
        """
        jsonschema.validate(data, schema=self.train_request_schema)

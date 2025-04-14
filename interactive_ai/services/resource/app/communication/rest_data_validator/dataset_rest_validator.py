# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import os

import jsonschema

from geti_fastapi_tools.exceptions import BadRequestException
from geti_fastapi_tools.validation import RestApiValidator


class DatasetRestValidator(RestApiValidator):
    def __init__(self) -> None:
        base_dir = os.path.dirname(__file__) + "/../../../../api/schemas/"
        self.create_dataset_schema = self.load_schema_file_as_dict(base_dir + "datasets/requests/post/dataset.yaml")

    def validate_creation_data(self, data: dict) -> None:
        """
        Validate that data adheres to the JSON schema of the 'create dataset' endpoint.

        :param data: JSON data to create the dataset
        :raises: ValidationError if the data does not comply with the schema
        """
        if not data:
            raise BadRequestException("Dataset creation requires a non-empty request body.")
        jsonschema.validate(data, self.create_dataset_schema)

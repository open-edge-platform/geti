# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the ModelTestResultRestValidator class"""

import os

import jsonschema

from .rest_validation_helpers import RestValidationHelpers
from geti_fastapi_tools.validation import RestApiValidator


class ModelTestRestValidator(RestApiValidator):
    """
    Class to validate that data for the model test REST endpoints sent by the user is correct
    """

    def __init__(self) -> None:
        base_dir = os.path.dirname(__file__) + "/../../../../api/schemas/"
        self._model_test_post_schema = self.load_schema_file_as_dict(
            base_dir + "model_test_results/requests/model_test_post.yaml"
        )

    def validate_model_test_params(self, args: dict):
        """
        Validates that the query parameters passed to the model tests endpoint are valid.
        :param args: Request arguments as they were passed to the endpoint
        :raises BadRequestException: For invalid query parameters
        """
        jsonschema.validate(args, self._model_test_post_schema)
        RestValidationHelpers.validate_objectid_field(args, "model_group_id")
        RestValidationHelpers.validate_objectid_field(args, "model_id")
        RestValidationHelpers.validate_objectid_list_field(args, "dataset_ids", single_item=True)

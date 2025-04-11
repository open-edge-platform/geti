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

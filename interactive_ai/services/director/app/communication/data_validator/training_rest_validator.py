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

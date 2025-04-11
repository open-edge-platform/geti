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

"""This module implements the AnnotationRestValidator class"""

import os

import jsonschema

from geti_fastapi_tools.exceptions import BadRequestException
from geti_fastapi_tools.validation import RestApiValidator

ID_ = "id"
NAME = "name"
VALUE = "value"


class AnnotationTemplateRestValidator(RestApiValidator):
    def __init__(self) -> None:
        base_dir = os.path.dirname(__file__) + "/../../../../api/schemas/"

        self.annotation_template_schema = self.load_schema_file_as_dict(
            base_dir + "annotation_template/requests/annotation_template.yaml"
        )

    def validate_annotation_template(
        self,
        annotation_template_rest: dict[str, str],
    ) -> None:
        """
        Validate annotation template json data with sanity checks. Steps:
        1. Schema validation
        2. Name validation
        3. Value validation
          - This validation step does not check the structure of the string, just that it is MongoDB safe

        :param annotation_template_rest: annotation template json data
        :raises jsonschema.exceptions.ValidationError when data doesn't match the yaml schema
        :raises BadRequestException when annotation_template_rest is empty or contains invalid characters
        """
        jsonschema.validate(annotation_template_rest, self.annotation_template_schema)
        if annotation_template_rest[NAME] is None:
            raise BadRequestException("The annotation template name cannot be empty.")
        if not annotation_template_rest[VALUE].isascii():  # TODO determine the correct characters received from UI
            raise BadRequestException("The provided annotation template value is not valid.")

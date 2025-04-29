# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module implements the MediaScoreFilterRestValidator class"""

import os

import jsonschema
from jsonschema import ValidationError

from communication.exceptions import InvalidFilterException

from geti_fastapi_tools.validation import RestApiValidator


class MediaScoreQueryValidator(RestApiValidator):
    """
    Class to validate that data for the model score filtering REST endpoints sent by the user is correct
    """

    def __init__(self) -> None:
        base_dir = os.path.dirname(__file__) + "/../../../../api/schemas/"
        self.media_score_query_schema = self.load_schema_file_as_dict(
            base_dir + "media_scores/requests/media_score_query.yaml"
        )

    def validate_media_score_query(self, data: dict) -> None:
        """
        Validate media score query json data for adherence to the json schema for the
        'media_scores_filter_endpoint' endpoint.

        :param data: media score query json data
        :raises InvalidFilterException: when data doesn't correspond
            with yaml schema
        """
        try:
            jsonschema.validate(data, self.media_score_query_schema)
        except ValidationError as exc:
            raise InvalidFilterException(f"Invalid json body used for test results filtering. Details: {exc.message}")

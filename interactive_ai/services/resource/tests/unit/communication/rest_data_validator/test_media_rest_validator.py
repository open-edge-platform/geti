# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import pytest

from communication.rest_data_validator import MediaRestValidator

from geti_fastapi_tools.exceptions import BadRequestException


class TestMediaRestValidator:
    @pytest.mark.parametrize(
        "upload_info, expected_error_message",
        [
            ("foo", "upload_info must be in json format."),
            ('"foo"', "upload_info must be a dictionary in json format. Received 'foo' of type <class 'str'> instead."),
        ],
        ids=[
            "invalid json",
            "valid json but no dict",
        ],
    )
    def test_validate_upload_info_error(self, upload_info, expected_error_message) -> None:
        # Act
        with pytest.raises(BadRequestException) as error:
            MediaRestValidator().validate_upload_info(upload_info=upload_info)

        assert error.value.message == expected_error_message

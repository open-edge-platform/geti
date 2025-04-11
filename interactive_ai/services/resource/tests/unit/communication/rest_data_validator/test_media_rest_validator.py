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

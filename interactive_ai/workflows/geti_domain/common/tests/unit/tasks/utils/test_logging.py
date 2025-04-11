# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your
# use of them is governed by the express license under which they were provided to you
# ("License"). Unless the License provides otherwise, you may not use, modify, copy,
# publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or
# implied warranties, other than those that are expressly stated in the License.

from unittest.mock import patch

import pytest

from jobs_common.tasks.utils.logging import init_logger


@pytest.mark.JobsComponent
class TestLogging:
    @patch("jobs_common.tasks.utils.logging.start_common_logger")
    def test_init_logger(self, mock_start_common_logger) -> None:
        # Arrange
        @init_logger(package_name="package_name")
        def test_function():
            pass

        # Act
        test_function()

        # Assert
        mock_start_common_logger.assert_called_once_with(package_name="package_name", use_async=False)

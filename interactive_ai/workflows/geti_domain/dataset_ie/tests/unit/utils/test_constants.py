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
"""Test constants"""

from unittest.mock import patch

import pytest

from job.utils.constants import _get_env_var


@pytest.mark.JobsComponent
class TestGetEnvVar:
    @pytest.mark.parametrize(("value", "expected_value"), (("123", 123), ("1e1", 10)))
    @patch("job.utils.constants.os.environ")
    @patch("job.utils.constants.logger")
    def test_get_env_var_exists(self, mock_logger, mock_environ, value, expected_value):
        var_name = "TEST_VAR"
        mock_environ.get.return_value = value

        result = _get_env_var(var_name)

        assert result == expected_value
        mock_logger.info.assert_called_with(f"{var_name} is configured as `{expected_value}`.")

    @patch("job.utils.constants.os.environ")
    @patch("job.utils.constants.logger")
    def test_get_env_var_not_set_with_default(self, mock_logger, mock_environ):
        mock_environ.get.return_value = ""
        var_name = "TEST_VAR"
        default_value = 10

        result = _get_env_var(var_name, default_value)

        assert result == default_value
        mock_logger.info.assert_called_with(
            f"{var_name} was not configured explicitly, it will be enforced as `{default_value}`."
        )

    @patch("job.utils.constants.os.environ")
    @patch("job.utils.constants.logger")
    def test_get_env_var_not_set_without_default(self, mock_logger, mock_environ):
        mock_environ.get.return_value = ""
        var_name = "TEST_VAR"

        result = _get_env_var(var_name)

        assert result is None
        mock_logger.info.assert_called_with(f"{var_name} was not configured explicitly, it won't be enforced.")

    @patch("job.utils.constants.os.environ")
    @patch("job.utils.constants.logger")
    def test_get_env_var_invalid_value_with_default(self, mock_logger, mock_environ):
        mock_environ.get.return_value = "invalid"
        var_name = "TEST_VAR"
        default_value = 10

        result = _get_env_var(var_name, default_value)

        assert result == default_value
        mock_logger.warning.assert_called_with(
            f"{var_name} was configured explicitly as `invalid`, but couldn't convert it into a numeric value."
            f" It will be enforced as `{default_value}`."
        )

    @patch("job.utils.constants.os.environ")
    @patch("job.utils.constants.logger")
    def test_get_env_var_invalid_value_without_default(self, mock_logger, mock_environ):
        mock_environ.get.return_value = "invalid"
        var_name = "TEST_VAR"

        result = _get_env_var(var_name)

        assert result is None
        mock_logger.warning.assert_called_with(
            f"{var_name} was configured explicitly as `invalid`, but couldn't convert it into a numeric value."
            " It won't be enforced."
        )

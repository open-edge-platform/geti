# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

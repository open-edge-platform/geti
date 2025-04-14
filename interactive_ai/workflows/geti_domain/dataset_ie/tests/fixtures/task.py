# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
This module implements task fixtures
"""

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def fxt_requests_post():
    """Patch istio-proxy termination callback not to raise an error in local environment."""
    with patch("jobs_common.tasks.primary_container_task.requests.post") as mock_requests_post:
        mock_requests_post.return_value.status_code = 200
        yield mock_requests_post

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest

from communication.jobs_client import JobsClient


@pytest.fixture()
def fxt_mock_jobs_client() -> Generator[JobsClient, None, None]:
    jobs_client = JobsClient()
    jobs_client._jobs_client = MagicMock()  # type: ignore[assignment]
    yield jobs_client
    jobs_client._jobs_client = None

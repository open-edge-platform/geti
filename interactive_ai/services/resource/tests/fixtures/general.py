# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import logging
import sys

import pytest

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def fxt_fix_pytest_logging_behaviour():
    """
    Prevent pytest from closing stdout and stderr, which can cause issues when
    teardown-like operations, which use logging, run after pytest has already
    (prematurely) closed these streams.
    Namely, the k8s_orchestrator teardown functionality in
    k8s_orchestrator._workload_life_timeout().
    """
    sys.stderr.close = lambda *args: None
    sys.stdout.close = lambda *args: None
    yield

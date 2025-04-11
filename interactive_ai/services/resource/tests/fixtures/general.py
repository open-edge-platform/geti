# INTEL CONFIDENTIAL
#
# Copyright (C) 2021 Intel Corporation
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

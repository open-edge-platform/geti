# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
#
# This software and the related documents are Intel copyrighted materials, and your use of them is governed by
# the express license under which they were provided to you ("License"). Unless the License provides otherwise,
# you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
# without Intel's prior written permission.
#
# This software and the related documents are provided as is, with no express or implied warranties,
# other than those that are expressly stated in the License.

"""
A module containing check functions that are interacting with local user.
"""

import logging
import os

from checks.errors import LocalUserCheckError
from texts.checks import LocalUserChecksTexts

logger = logging.getLogger(__name__)

ROOT_UID = 0


def check_user_id():  # noqa: ANN201
    """
    Check that proper local user is used.
    Usage: install, upgrade, uninstall
    """
    uid = os.getuid()
    if uid != ROOT_UID:
        raise LocalUserCheckError(LocalUserChecksTexts.user_check_error)

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

import os
from functools import wraps

from flytekit import Secret, current_context
from jobs_common.tasks.utils.secrets import SECRETS

PROJECT_IE_SECRETS = [
    *SECRETS,
    Secret(group="signing-ie-certificate", key="tls.key", mount_requirement=Secret.MountType.FILE),
]


def signing_key_env_vars(fn):  # noqa: ANN001, ANN201
    """
    Decorator to set task environment variables for signing keys
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        os.environ["SIGNING_IE_PRIVKEY"] = current_context().secrets.get("signing-ie-certificate", "tls.key")
        return fn(*args, **kwargs)

    return wrapper

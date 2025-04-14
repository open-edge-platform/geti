# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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

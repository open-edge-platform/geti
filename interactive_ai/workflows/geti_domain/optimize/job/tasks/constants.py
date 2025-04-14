# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
"""
Define constants for model optimization task
"""

from jobs_common.tasks.primary_container_task import get_flyte_pod_spec
from kubernetes.client.models import V1ResourceRequirements

OPTIMIZE_TASK_POD_SPEC = get_flyte_pod_spec(
    resources=V1ResourceRequirements(
        limits={"cpu": "100", "memory": "4000Mi", "ephemeral-storage": "4000Mi"},
        requests={"cpu": "1", "memory": "2000Mi", "ephemeral-storage": "2000Mi"},
    )
)

# Flyte task seems not allowing to return None. If we return None, it produces no output rather than returning None
# as follows.
#
# .venv-optimize-job/lib/python3.10/site-packages/flytekit/core/promise.py:592: in binding_data_from_python_std
#     raise AssertionError(
# E   AssertionError: Cannot pass output from task n0 that produces no outputs to a downstream task
NULL_COMPILED_DATASET_SHARDS_ID = ""

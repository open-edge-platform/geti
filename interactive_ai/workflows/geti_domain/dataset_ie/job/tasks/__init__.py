# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from jobs_common.tasks.primary_container_task import get_flyte_pod_spec
from kubernetes.client.models import V1ResourceRequirements

__all__ = ["IMPORT_EXPORT_TASK_POD_SPEC"]

IMPORT_EXPORT_TASK_POD_SPEC = get_flyte_pod_spec(
    resources=V1ResourceRequirements(
        limits={"cpu": "100", "memory": "4000Mi", "ephemeral-storage": "500Gi"},
        requests={"cpu": "1", "memory": "1000Mi", "ephemeral-storage": "1000Mi"},
    )
)

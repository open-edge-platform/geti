# INTEL CONFIDENTIAL
#
# Copyright (C) 2023 Intel Corporation
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

from jobs_common.tasks.primary_container_task import get_flyte_pod_spec
from kubernetes.client.models import V1ResourceRequirements

__all__ = ["IMPORT_EXPORT_TASK_POD_SPEC"]

IMPORT_EXPORT_TASK_POD_SPEC = get_flyte_pod_spec(
    resources=V1ResourceRequirements(
        limits={"cpu": "100", "memory": "4000Mi", "ephemeral-storage": "500Gi"},
        requests={"cpu": "1", "memory": "1000Mi", "ephemeral-storage": "1000Mi"},
    )
)

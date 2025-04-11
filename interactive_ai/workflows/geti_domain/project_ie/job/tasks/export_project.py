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

"""Defines the task for project export"""

import logging

from geti_types import ID
from jobs_common.tasks import flyte_multi_container_task as task
from jobs_common.tasks.utils.logging import init_logger
from jobs_common.tasks.utils.progress import report_progress, task_progress
from jobs_common.tasks.utils.secrets import env_vars
from jobs_common.tasks.utils.telemetry import task_telemetry

from job.tasks import IMPORT_EXPORT_TASK_POD_SPEC
from job.tasks.secrets import PROJECT_IE_SECRETS, signing_key_env_vars
from job.usecases import ProjectExportUseCase

logger = logging.getLogger(__name__)


@task(pod_spec=IMPORT_EXPORT_TASK_POD_SPEC, secret_requests=PROJECT_IE_SECRETS)
@env_vars
@signing_key_env_vars
@init_logger(package_name=__name__)
@task_telemetry
@task_progress(
    start_message="Starting to export project",
    finish_message="Project export complete",
    failure_message="Failed to export project",
)
def export_project(
    project_id: str,
) -> None:
    """
    Export project from Geti to zipped project task

    :param project_id: ID of the project to export
    :return: id of the exported project
    """
    ProjectExportUseCase.export_as_zip(project_id=ID(project_id), progress_callback=report_progress)

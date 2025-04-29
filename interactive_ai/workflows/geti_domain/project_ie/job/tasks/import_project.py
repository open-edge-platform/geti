# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Defines the task for project import"""

import logging

from geti_types import ID
from jobs_common.tasks import flyte_multi_container_task as task
from jobs_common.tasks.utils.logging import init_logger
from jobs_common.tasks.utils.progress import report_progress, task_progress
from jobs_common.tasks.utils.secrets import env_vars
from jobs_common.tasks.utils.telemetry import task_telemetry

from job.tasks import IMPORT_EXPORT_TASK_POD_SPEC
from job.tasks.secrets import PROJECT_IE_SECRETS, signing_key_env_vars
from job.usecases import ProjectImportUseCase

logger = logging.getLogger(__name__)


@task(pod_spec=IMPORT_EXPORT_TASK_POD_SPEC, secret_requests=PROJECT_IE_SECRETS)
@env_vars
@signing_key_env_vars
@init_logger(package_name=__name__)
@task_telemetry
@task_progress(
    start_message="Starting to import project",
    finish_message="Project import complete",
    failure_message="Failed to import project",
)
def import_project(
    file_id: str,
    keep_original_dates: bool,
    project_name: str,
    user_id: str,
) -> None:
    """
    Import project from an uploaded project zip archive to geti.

    :param file_id: S3 object id of the uploaded project
    :param keep_original_dates: if True original exported dates are kept
    :param project_name: if not an empty string, to use this name for the newly imported project
    :param user_id: ID of the user who is importing the project
    """
    project_import_use_case = ProjectImportUseCase(
        keep_original_dates=keep_original_dates,
        project_name=project_name,
    )
    project_import_use_case.import_zip(
        file_id=ID(file_id),
        creator_id=ID(user_id),
        progress_callback=report_progress,
    )

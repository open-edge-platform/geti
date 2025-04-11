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

"""
Job scheduler utils
"""

import os


def resolve_revert_job(job_type: str) -> tuple[str, str] | None:
    """
    Resolves a job type to Flyte revert workflow name and version.
    Uses environment variables for mapping.

    Workflow name env var mapping: job_type -> "JOB_{job_type.upper()}_REVERT_FLYTE_WORKFLOW_NAME"
    Workflow version env var mapping: job_type -> "JOB_{job_type.upper()}_REVERT_FLYTE_WORKFLOW_VERSION"

    Example: job_type = train
    Workflow name env var: JOB_TRAIN_REVERT_FLYTE_WORKFLOW_NAME
    Workflow version env var: JOB_TRAIN_REVERT_FLYTE_WORKFLOW_VERSION

    :param job_type: Job type
    :return Tuple[str, str]: workflows name and version
    """
    workflow_name = os.environ.get(f"JOB_{job_type.upper()}_REVERT_FLYTE_WORKFLOW_NAME", None)
    if workflow_name is None:
        return None

    workflow_version = os.environ.get(f"JOB_{job_type.upper()}_REVERT_FLYTE_WORKFLOW_VERSION", None)
    if workflow_version is None:
        return None

    return workflow_name, workflow_version


def resolve_main_job(job_type: str) -> tuple[str, str]:
    """
    Resolves a job type to Flyte workflow name and version.
    Uses environment variables for mapping.

    Workflow name env var mapping: job_type -> "JOB_{job_type.upper()}_FLYTE_WORKFLOW_NAME"
    Workflow version env var mapping: job_type -> "JOB_{job_type.upper()}_FLYTE_WORKFLOW_VERSION"

    Example: job_type = train
    Workflow name env var: JOB_TRAIN_FLYTE_WORKFLOW_NAME
    Workflow version env var: JOB_TRAIN_FLYTE_WORKFLOW_VERSION

    :param job_type: Job type
    :return Tuple[str, str]: workflows name and version
    """
    workflow_name = os.environ.get(f"JOB_{job_type.upper()}_FLYTE_WORKFLOW_NAME", None)
    if workflow_name is None:
        raise Exception(f"Workflow name mapping for job '{job_type}' is not found")

    workflow_version = os.environ.get(f"JOB_{job_type.upper()}_FLYTE_WORKFLOW_VERSION", None)
    if workflow_version is None:
        raise Exception(f"Workflow version mapping for job '{job_type}' is not found")

    return workflow_name, workflow_version


def get_revert_execution_name(job_id: str) -> str:
    """
    Returns Flyte revert execution name for a job
    Revert execution name is a main execution plus "-revert" suffix

    :param job_id: Job ID
    :return str: Flyte revert execution name
    """

    return f"{get_main_execution_name(job_id=job_id)}-revert"


def get_main_execution_name(job_id: str) -> str:
    """
    Returns Flyte execution name for a job from certain workspace
    Flyte execution name matches with job ID.
    Suffix ex is added because Flyte execution ID must start with a-z

    :param job_id: Job ID
    :return str: Flyte execution name
    """

    return f"ex-{job_id}"


class WrongExecutionName(Exception):
    """Exception for wrong Flyte execution name"""

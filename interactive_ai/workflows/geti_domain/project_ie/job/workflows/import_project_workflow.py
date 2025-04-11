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

"""This module implements project import workflow"""

from flytekit import workflow

from job.tasks.import_project import import_project


@workflow
def import_project_workflow(
    file_id: str,
    keep_original_dates: bool,
    project_name: str,
    user_id: str,
) -> None:
    """
    Flyte workflow for importing geti projects.

    :param file_id: S3 object id of the uploaded project
    :param keep_original_dates: if True original exported dates are kept
    :param project_name: if not an empty string, to use this name for the newly imported project
    :param user_id: ID of the user who is importing the project
    """
    import_project(
        file_id=file_id,
        keep_original_dates=keep_original_dates,
        project_name=project_name,
        user_id=user_id,
    )

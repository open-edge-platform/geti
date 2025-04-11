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
from geti_types import ID


class WorkspaceNotFoundException(Exception):
    """
    Exception raised when workspace could not be found in database.

    :param workspace_id: ID of the workspace
    """

    def __init__(self, workspace_id: ID) -> None:
        super().__init__(
            f"Workspace with id {workspace_id} could not be found.",
        )


class DuplicateJobFoundException(Exception):
    """
    Exception raised when job cannot be submitted, because duplicate is found and duplicate policy is REJECT.
    """

    def __init__(self) -> None:
        super().__init__("Duplicate job has been already submitted.")


class JobNotCancellableException(Exception):
    """
    Exception raised when job is non-cancellable and is already started

    :param job_id: job ID
    """

    def __init__(self, job_id: ID) -> None:
        super().__init__(
            f"Job with id {job_id} cannot be cancelled.",
        )

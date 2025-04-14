# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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

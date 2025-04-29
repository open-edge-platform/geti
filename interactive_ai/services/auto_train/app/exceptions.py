# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Exceptions raised within the auto-train controller"""


class InvalidAutoTrainRequestError(ValueError):
    """
    Exception raised when a auto-train request contains invalid data, so it cannot be processed.
    The caller should not retry to process such a request because most likely it would fail again.
    """


class JobSubmissionError(RuntimeError):
    """Exception raised when a problem occurs while submitting a job to the jobs client"""

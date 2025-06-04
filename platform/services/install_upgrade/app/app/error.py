# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE


class JobError(Exception):
    """
    Base class for job-related errors.
    """


class ParseDurationError(JobError):
    """
    Raised when there is an error parsing a time duration
    """


class HelmChartDeployError(JobError):
    """
    Raised when there is an error deploying a Helm chart.
    """


class TimeoutJobError(JobError):
    """
    Raised when a Job is neither successful nor failed in allocated time.
    """


class FailedJobError(JobError):
    """
    Raised when a job fails.
    """


class UnknownJobError(JobError):
    """
    Raised when an unknown job is encountered.
    """

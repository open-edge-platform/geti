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

"""
Module for jobs steps visual representation
"""

import logging
import os
from dataclasses import dataclass

import yaml

from geti_types import Singleton

logger = logging.getLogger(__name__)


@dataclass
class JobTemplateStepBranch:
    """
    Job template step branching information with corresponding skip message to show to user
    """

    condition: str
    branch: str
    skip_message: str | None = None


@dataclass
class JobTemplateStep:
    """
    Job template step, is used as a basis to build a certain step details while scheduling a new job.
    """

    name: str
    task_id: str
    branches: list[JobTemplateStepBranch] | None = None
    start_message: str | None = None
    finish_message: str | None = None
    failure_message: str | None = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.branches = (
            [JobTemplateStepBranch(**branch) for branch in kwargs["branches"]] if "branches" in kwargs else None
        )

    def get_branch(self, condition: str) -> JobTemplateStepBranch | None:
        """
        Returns a job step branch value by a branch condition name
        :param condition: condition name
        :return JobTemplateStepBranch: branch value or None if step is not a part of specified condition
        """
        return (
            next(
                (branch for branch in self.branches if branch.condition == condition),
                None,
            )
            if self.branches is not None
            else None
        )


@dataclass
class _JobTemplate:
    """
    Job template, is used as a basis to build a list of steps while scheduling a new job.
    """

    job_type: str
    steps: list[JobTemplateStep]

    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)
        self.steps = [JobTemplateStep(**step) for step in kwargs["steps"]]


class JobsTemplates(metaclass=Singleton):
    def __init__(self) -> None:
        JOBS_TEMPLATES_DIR = os.environ.get("JOBS_TEMPLATES_DIR", "/tmp")  # noqa: S108
        JOBS_TEMPLATES_FILE = os.environ.get("JOBS_TEMPLATES_FILE", "jobs_templates.yaml")

        with open(os.path.join(JOBS_TEMPLATES_DIR, JOBS_TEMPLATES_FILE)) as templates_file:
            templates = yaml.safe_load(templates_file)
            self.templates = [_JobTemplate(**template) for template in templates]
            logger.info(f"Loaded following job types templates: {[template.job_type for template in self.templates]}")

    def get_job_steps(self, job_type: str) -> list[JobTemplateStep]:
        """
        Returns steps of a certain job type
        :param job_type: job type
        :return list[JobStep]: job steps
        :raises RuntimeError: if job type cannot be found
        """
        job_steps = next((template.steps for template in self.templates if template.job_type == job_type), None)
        if job_steps is None:
            raise RuntimeError(f"Unable to find {job_type} job")
        return job_steps

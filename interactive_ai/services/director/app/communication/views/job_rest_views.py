# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""
Converters between objects and their corresponding REST views
"""

import logging

from geti_types import ID

logger = logging.getLogger(__name__)


class JobRestViews:
    @staticmethod
    def job_id_to_rest(job_id: ID | None) -> dict:
        """
        Get the REST view of a job

        :param job_id: job ID or None if no job was submitted
        :return: REST view of the job id
        """
        return {"job_id": job_id}

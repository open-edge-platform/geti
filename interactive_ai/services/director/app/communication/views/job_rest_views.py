# INTEL CONFIDENTIAL
#
# Copyright (C) 2022 Intel Corporation
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

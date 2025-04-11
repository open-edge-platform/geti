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
"""This module defines helpers related to jobs"""

import json
import os
from collections import OrderedDict
from enum import Enum, auto

JOB_SERVICE_GRPC_ADDRESS = os.environ.get("JOB_SERVICE_ADDRESS", "localhost:50051")


class JobType(str, Enum):
    EXPORT_DATASET = "export_dataset"
    PREPARE_IMPORT_TO_NEW_PROJECT = "prepare_import_to_new_project"
    PERFORM_IMPORT_TO_NEW_PROJECT = "perform_import_to_new_project"
    PREPARE_IMPORT_TO_EXISTING_PROJECT = "prepare_import_to_existing_project"
    PERFORM_IMPORT_TO_EXISTING_PROJECT = "perform_import_to_existing_project"


IMPORT_JOBS = (
    JobType.PREPARE_IMPORT_TO_NEW_PROJECT,
    JobType.PERFORM_IMPORT_TO_NEW_PROJECT,
    JobType.PREPARE_IMPORT_TO_EXISTING_PROJECT,
    JobType.PERFORM_IMPORT_TO_EXISTING_PROJECT,
)


class JobDuplicatePolicy(str, Enum):
    REPLACE = auto()
    OMIT = auto()
    REJECT = auto()


def serialize_job_key(job_key: dict) -> str:
    """
    Returns the job's key (represented as a dictionary) to a serialized string.

    :param job_key: dict instance to serialize
    :returns: string representation of the dict
    """
    return json.dumps(OrderedDict(sorted(job_key.items())))

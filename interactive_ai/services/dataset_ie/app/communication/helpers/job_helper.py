# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
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

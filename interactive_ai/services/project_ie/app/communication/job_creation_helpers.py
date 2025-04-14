# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
import json
from collections import OrderedDict
from enum import Enum, auto


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

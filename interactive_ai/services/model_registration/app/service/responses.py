# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from enum import Enum


class Responses(str, Enum):
    Created = "CREATED"
    Failed = "FAILED"
    Removed = "REMOVED"
    AlreadyRegistered = "PIPELINE_ALREADY_REGISTERED"
    NotImplemented = "NOT_IMPLEMENTED"

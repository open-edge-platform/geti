# INTEL CONFIDENTIAL
#
# Copyright (C) 2025 Intel Corporation
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
from dataclasses import dataclass

from sc_sdk.entities.compiled_dataset_shards import CompiledDatasetShards
from sc_sdk.entities.model import Model
from sc_sdk.entities.model_storage import ModelStorageIdentifier
from sc_sdk.entities.project import Project


@dataclass
class OptimizationConfig:
    """Dataclass to collect entities after the model optimization preparation step.

    :param project: Input project
    :param input_model: Input model that will be used as a baseline
    :param model_to_optimize: Model metadata that will represent optimized version
    :param compiled_dataset_shards: Input dataset for the optimization. It can be `NullCompiledDatasetShards`
        if dataset sharding is not used during optimize workflow.
    :param model_storage_identifier: The identifier for the model storage.
    """

    project: Project
    input_model: Model
    model_to_optimize: Model
    compiled_dataset_shards: CompiledDatasetShards
    model_storage_identifier: ModelStorageIdentifier

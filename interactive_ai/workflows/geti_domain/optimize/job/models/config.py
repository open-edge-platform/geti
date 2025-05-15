# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
from dataclasses import dataclass

from iai_core.entities.compiled_dataset_shards import CompiledDatasetShards
from iai_core.entities.model import Model
from iai_core.entities.model_storage import ModelStorageIdentifier
from iai_core.entities.project import Project


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

# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from enum import Enum

from pydantic import BaseModel, Field
from sc_sdk.algorithms.models.hyperparameters import Hyperparameters


class AlgorithmStats(BaseModel):
    gigaflops: float = Field(gt=0)
    trainable_parameters: int = Field(gt=0)


class SupportedStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    OBSOLETE = "obsolete"


class Algorithm(BaseModel):
    """
    Algorithm contains the necessary information for training a specific machine learning model.

    Attributes:
        id: Unique identifier for the algorithm (equivalent to the legacy model_template_id)
        name: Display name of the algorithm
        description: Detailed description of the algorithm
        task: Type of machine learning task the algorithm performs
        stats: Statistics of the model
        support_status: Current status (active, deprecated, or obsolete)
        supported_gpus: Dictionary mapping GPU types to compatibility status
        hyperparameters: Configuration parameters for model training
    """
    id: str
    name: str
    description: str
    task: str
    stats: AlgorithmStats
    support_status: SupportedStatus
    supported_gpus: dict[str, bool]
    hyperparameters: Hyperparameters


class NullAlgorithm(Algorithm):
    """
    NullAlgorithm is a placeholder for an empty or non-existent algorithm.

    This class is used to represent the absence of a valid algorithm configuration.
    """
    id: str = Field(default="null")
    name: str = Field(default="null")
    description: str = Field(default="null")
    task: str = Field(default="null")
    stats: AlgorithmStats = Field(default=AlgorithmStats(gigaflops=0, trainable_parameters=0))
    support_status: SupportedStatus = Field(default=SupportedStatus.OBSOLETE)
    supported_gpus: dict[str, bool] = Field(default={})

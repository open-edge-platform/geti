# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from geti_types import ID
from iai_core.entities.model_template import ModelTemplate


class NoActiveLearningAlgorithmSupported(RuntimeError):
    """
    Raised when there is no active learning algorithm enabled and supported for a task
    """

    def __init__(self, model_template: ModelTemplate) -> None:
        super().__init__(
            f"No active learning algorithm supported for model architecture `{model_template.model_template_id}`"
        )


class ActiveLearningModelStorageNotFound(RuntimeError):
    """
    Raised when a model storage necessary for active learning cannot be found

    :param model_storage_id: ID of the model storage
    """

    def __init__(self, model_storage_id: ID) -> None:
        super().__init__(f"No active learning model storage found with ID `{model_storage_id}`")


class ActiveLearningModelNotFound(RuntimeError):
    """
    Raised when a model necessary for active learning cannot be found

    :param model_id: ID of the model
    """

    def __init__(self, model_id: ID) -> None:
        super().__init__(f"No active learning model found with ID `{model_id}`")


class ActiveLearningDatasetNotFound(RuntimeError):
    """
    Raised when a dataset necessary for active learning cannot be found

    :param dataset_id: ID of the dataset
    """

    def __init__(self, dataset_id: ID) -> None:
        super().__init__(f"No active learning dataset found with ID `{dataset_id}`")


class IncorrectDatasetUsage(RuntimeError):
    """Raised when a Dataset is used improperly"""

    def __init__(self) -> None:
        super().__init__("Incorrect usage of dataset for active learning")


class FeatureVectorsNotFound(RuntimeError):
    """Raised when one or more feature vectors is missing in a dataset"""

    def __init__(self) -> None:
        super().__init__("Missing feature vectors for active learning")


class InvalidFeatureVectors(RuntimeError):
    """Raised when the feature vectors to update the active scores are invalid"""

    def __init__(self) -> None:
        super().__init__("Invalid feature vectors for active learning")


class FailedActiveScoreUpdate(RuntimeError):
    """Raised when the active scores cannot be updated for a task"""

    def __init__(self) -> None:
        super().__init__("Failed to update the active scores")

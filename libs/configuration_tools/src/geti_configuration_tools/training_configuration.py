# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

from geti_types import ID, PersistentEntity
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .hyperparameters import (
    AugmentationParameters,
    DatasetPreparationParameters,
    EvaluationParameters,
    Hyperparameters,
    TrainingHyperParameters,
)


class SubsetSplit(BaseModel):
    """
    Parameters for splitting a dataset into training, validation, and test subsets.
    The sum of training, validation, and test percentages must equal 100.
    """

    training: int = Field(
        ge=1, default=70, title="Training percentage", description="Percentage of data to use for training"
    )
    validation: int = Field(
        ge=1, default=20, title="Validation percentage", description="Percentage of data to use for validation"
    )
    test: int = Field(ge=1, default=10, title="Test percentage", description="Percentage of data to use for testing")
    auto_selection: bool = Field(
        default=True, title="Auto selection", description="Whether to automatically select data for each subset"
    )
    remixing: bool = Field(default=False, title="Remixing", description="Whether to remix data between subsets")

    @model_validator(mode="after")
    def validate_subsets(self) -> "SubsetSplit":
        if (self.training + self.validation + self.test) != 100:
            raise ValueError("Sum of subsets should be equal to 100")
        return self


class Filtering(BaseModel):
    """Parameters for filtering annotations in the dataset."""

    min_annotation_pixels: int = Field(
        gt=0, default=1, title="Minimum annotation pixels", description="Minimum number of pixels in an annotation"
    )
    max_annotation_pixels: int | None = Field(
        ge=1, default=None, title="Maximum annotation pixels", description="Maximum number of pixels in an annotation"
    )
    max_annotation_objects: int | None = Field(
        gt=1, default=None, title="Maximum annotation objects", description="Maximum number of objects in an annotation"
    )


class GlobalDatasetPreparationParameters(BaseModel):
    """
    Parameters for preparing a dataset for training within the global configuration.
    Controls data splitting and filtering before being passed for the training.
    """

    subset_split: SubsetSplit = Field(title="Subset split", description="Configuration for splitting data into subsets")
    filtering: Filtering = Field(title="Filtering", description="Configuration for filtering annotations")


class GlobalParameters(BaseModel):
    """
    Global parameters that are used within the application but are not directly passed to the training backend.
    These parameters still impact the final training outcome by controlling dataset preparation.
    """

    dataset_preparation: GlobalDatasetPreparationParameters = Field(
        title="Dataset preparation", description="Parameters for preparing the dataset"
    )


class TrainingConfiguration(BaseModel, PersistentEntity):
    """Configuration for model training"""

    def __init__(self, id_: ID, task_id: ID, ephemeral: bool = True, **data):
        # first initialize the Pydantic BaseModel with all arguments
        BaseModel.__init__(self, **data)

        # then initialize PersistentEntity with id and ephemeral parameters
        PersistentEntity.__init__(self, id_=id_, ephemeral=ephemeral)
        self.task_id = task_id

    model_config = ConfigDict(  # allows the class to have "extra" field such as task_id
        extra="allow", protected_namespaces=()
    )

    model_manifest_id: str | None = Field(
        default=None,
        title="Model manifest ID",
        description="ID for the model manifest that defines the supported parameters and capabilities for training",
    )
    global_parameters: GlobalParameters = Field(
        title="Global parameters", description="Global configuration parameters for training"
    )
    hyperparameters: Hyperparameters = Field(title="Hyperparameters", description="Hyperparameters for training")

    def __eq__(self, other: object) -> bool:
        """
        Compares two ProjectConfiguration instances.

        Checks if both objects have the same ID and task configurations.
        """
        if not isinstance(other, TrainingConfiguration):
            return False

        # Compare IDs
        if self.id_ != other.id_ or self.model_manifest_id != other.model_manifest_id:
            return False

        # Compare parameters
        return self.global_parameters == other.global_parameters and self.hyperparameters == other.hyperparameters


class NullTrainingConfiguration(TrainingConfiguration):
    """
    Null object implementation for TrainingConfiguration.

    This class implements the Null Object Pattern to represent a "non-existent" training configuration.
    """

    def __init__(self) -> None:
        TrainingConfiguration.__init__(
            self,
            id_=ID(),
            task_id=ID(),
            global_parameters=GlobalParameters(
                dataset_preparation=GlobalDatasetPreparationParameters(
                    subset_split=SubsetSplit(), filtering=Filtering()
                )
            ),
            hyperparameters=Hyperparameters(
                dataset_preparation=DatasetPreparationParameters(
                    augmentation=AugmentationParameters(),
                ),
                training=TrainingHyperParameters(
                    max_epochs=1,
                    learning_rate=0.001,
                ),
                evaluation=EvaluationParameters(metric=None),
            ),
            ephemeral=True,
        )
